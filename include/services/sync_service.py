import json
import math
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
import pytz

from include.infra.postgres_database import engine as default_engine
from include.builders.os_payload_builder import OSPayloadBuilder
from include.clients.autonox_client import AutonoxHttpClient
from include.data.models.autonox_outbox_model import AutonoxOutboxModel
from include.data.seeds.seed_config import seed_config

logger = logging.getLogger(__name__)


class SyncService:
    """
    Serviço principal de orquestração do Outbox Pattern para ingestão na API Autonox.
    """

    def __init__(self, db_engine: Optional[Engine] = None, marca: str = "BMW"):
        self.engine = db_engine or default_engine
        AutonoxOutboxModel.__table__.create(bind=self.engine, checkfirst=True)
        self._ensure_response_columns()
        seed_config(self.engine)
        with self.engine.connect() as conn:
            self.sync_config = dict(
                conn.execute(
                    text(
                        """
                        SELECT enqueue_limit, batch_size, max_attempts
                        FROM autonox_sync_config
                        WHERE config_id = 1
                        """
                    )
                )
                .mappings()
                .one()
            )
        self.builder = OSPayloadBuilder(db_engine=self.engine, marca_default=marca)
        self.client = AutonoxHttpClient()

    def _ensure_response_columns(self):
        with self.engine.begin() as conn:
            columns = {
                column["name"]
                for column in inspect(conn).get_columns("autonox_outbox")
            }
            for column_name, column_type in (
                ("response_status_code", "INTEGER"),
                ("response_message", "TEXT"),
            ):
                if column_name not in columns:
                    conn.execute(
                        text(
                            f"ALTER TABLE autonox_outbox "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )

    def now_utc_minus_3(self):
        return datetime.now(pytz.timezone("America/Sao_Paulo"))

    def get_empresa_configs(self) -> dict:
        """
        Consulta na tabela autonox_empresa_config os registros ativos mapeados por codigo_empresa.
        """
        query = text(
            """
            SELECT codigo_empresa, sigla, marca, api_key, is_active
            FROM autonox_empresa_config
            WHERE is_active = TRUE
        """
        )
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
                return {row["codigo_empresa"]: dict(row) for row in rows}
        except Exception as e:
            logger.warning(
                f"Erro ao buscar configurações de empresa na tabela autonox_empresa_config: {e}"
            )
            return {}

    def enqueue_updated_orders(self, limit: Optional[int] = None) -> int:
        """
        Enfileira na autonox_outbox as OS presentes na os_capa que ainda não foram enviadas
        ou que sofreram atualização recente.
        """
        limit = self.sync_config["enqueue_limit"] if limit is None else limit
        query_sync = text(
            """
            INSERT INTO autonox_outbox (cod_empresa, numero_os, status, attempts, created_at, updated_at)
            SELECT oc.cod_empresa, oc.numero_os, 'pending', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM os_capa oc
            LEFT JOIN autonox_outbox ob ON (oc.cod_empresa = ob.cod_empresa AND oc.numero_os = ob.numero_os)
            WHERE ob.id IS NULL 
               OR (oc.updated_at > ob.updated_at AND ob.status IN ('sent', 'error'))
            LIMIT :limit
            ON CONFLICT (cod_empresa, numero_os) DO UPDATE 
            SET status = 'pending',
                updated_at = CURRENT_TIMESTAMP
            WHERE autonox_outbox.status != 'pending'
        """
        )

        with self.engine.begin() as conn:
            result = conn.execute(query_sync, {"limit": limit})
            count = result.rowcount
            logger.info(
                f"Enfileiradas/atualizadas {count} OS na tabela autonox_outbox."
            )
            return count

    def process_outbox(
        self,
        batch_size: Optional[int] = None,
        max_attempts: Optional[int] = None,
    ) -> dict:
        """
        Processa a fila autonox_outbox enviando os payloads para a API Autonox com as chaves específicas por empresa.
        """
        batch_size = self.sync_config["batch_size"] if batch_size is None else batch_size
        max_attempts = (
            self.sync_config["max_attempts"] if max_attempts is None else max_attempts
        )
        query_fetch = text(
            """
            SELECT id, cod_empresa, numero_os, attempts
            FROM autonox_outbox
            WHERE status IN ('pending', 'error') AND attempts < :max_attempts
            ORDER BY id ASC
            LIMIT :batch_size
        """
        )

        with self.engine.connect() as conn:
            records = (
                conn.execute(
                    query_fetch,
                    {"max_attempts": max_attempts, "batch_size": batch_size},
                )
                .mappings()
                .all()
            )

        if not records:
            logger.info("Nenhum item pendente na fila autonox_outbox.")
            return {"processed": 0, "success": 0, "failed": 0}

        empresa_configs = self.get_empresa_configs()
        success_count = 0
        failed_count = 0

        for rec in records:
            outbox_id = rec["id"]
            cod_empresa = rec["cod_empresa"]
            numero_os = rec["numero_os"]
            attempts = rec["attempts"] + 1

            emp_config = empresa_configs.get(cod_empresa)
            if not emp_config:
                err_msg = f"Empresa {cod_empresa} inativa ou sem chave API configurada na tabela autonox_empresa_config."
                logger.error(err_msg)
                new_status = (
                    "failed_dead_letter" if attempts >= max_attempts else "error"
                )
                self._update_record_status(
                    outbox_id, new_status, attempts, err_msg, None
                )
                failed_count += 1
                continue

            api_key = emp_config.get("api_key")
            marca = emp_config.get("marca")

            # Constrói o payload consolidado
            payload = self.builder.build_payload(cod_empresa, numero_os, marca=marca)
            if not payload:
                # Se não conseguir construir a OS (dados ausentes), registra erro
                self._update_record_status(
                    outbox_id,
                    "error",
                    attempts,
                    "Incapaz de gerar payload (OS não encontrada na capa)",
                    None,
                )
                failed_count += 1
                continue

            # Envia via cliente HTTP utilizando a api_key da empresa
            success, status_code, resp_data, error_msg = self.client.send_os(
                payload, api_key=api_key
            )
            response_message = error_msg
            if response_message is None:
                response_message = resp_data.get("message") or resp_data.get("mensagem")
                if response_message is not None and not isinstance(
                    response_message, str
                ):
                    response_message = json.dumps(
                        response_message, ensure_ascii=False
                    )

            if success:
                processo_id = resp_data.get("processo_id")
                self._update_record_status(
                    outbox_id,
                    "sent",
                    attempts,
                    None,
                    processo_id,
                    payload,
                    status_code,
                    response_message,
                )
                self._mark_os_capa_sent(cod_empresa, numero_os)
                success_count += 1
            else:
                new_status = (
                    "failed_dead_letter" if attempts >= max_attempts else "error"
                )
                self._update_record_status(
                    outbox_id,
                    new_status,
                    attempts,
                    error_msg,
                    None,
                    payload,
                    status_code,
                    response_message,
                )
                failed_count += 1

        summary = {
            "processed": len(records),
            "success": success_count,
            "failed": failed_count,
        }
        logger.info(f"Processamento outbox concluído: {summary}")
        return summary

    @staticmethod
    def _sanitize_payload(obj):
        """
        Percorre recursivamente o payload substituindo float NaN por None,
        evitando erro de serialização JSON no PostgreSQL
        (NaN é JavaScript válido, mas inválido no padrão JSON/RFC 8259).
        """
        if isinstance(obj, float) and math.isnan(obj):
            return None
        if isinstance(obj, dict):
            return {k: SyncService._sanitize_payload(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [SyncService._sanitize_payload(v) for v in obj]
        return obj

    def _update_record_status(
        self,
        outbox_id: int,
        status: str,
        attempts: int,
        last_error: Optional[str],
        processo_id: Optional[str],
        payload: Optional[dict] = None,
        response_status_code: Optional[int] = None,
        response_message: Optional[str] = None,
    ):
        query = text(
            """
            UPDATE autonox_outbox
            SET status = :status,
                attempts = :attempts,
                last_error = :last_error,
                response_status_code = COALESCE(
                    :response_status_code, response_status_code
                ),
                response_message = CASE
                    WHEN :response_status_code IS NOT NULL
                    THEN :response_message
                    ELSE response_message
                END,
                processo_id = COALESCE(:processo_id, processo_id),
                payload = COALESCE(:payload, payload),
                updated_at = CURRENT_TIMESTAMP,
                sent_at = CASE WHEN :status = 'sent' THEN CURRENT_TIMESTAMP ELSE sent_at END
            WHERE id = :id
        """
        )
        with self.engine.begin() as conn:
            conn.execute(
                query,
                {
                    "id": outbox_id,
                    "status": status,
                    "attempts": attempts,
                    "last_error": last_error,
                    "response_status_code": response_status_code,
                    "response_message": response_message,
                    "processo_id": processo_id,
                    "payload": (
                        json.dumps(
                            self._sanitize_payload(payload), ensure_ascii=False
                        )
                        if payload
                        else None
                    ),
                },
            )

    def _mark_os_capa_sent(self, cod_empresa: int, numero_os: int):
        query = text(
            """
            UPDATE os_capa
            SET sent_autodeal = TRUE,
                sent_at_autodeal = CURRENT_TIMESTAMP,
                updated_at_autodeal = CURRENT_TIMESTAMP
            WHERE cod_empresa = :cod_empresa AND numero_os = :numero_os
        """
        )
        with self.engine.begin() as conn:
            conn.execute(query, {"cod_empresa": cod_empresa, "numero_os": numero_os})

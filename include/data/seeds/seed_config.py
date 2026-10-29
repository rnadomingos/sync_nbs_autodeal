import os
import logging
from datetime import date
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from include.infra.postgres_database import engine as default_engine
from include.data.models.autonox_sync_config_model import (
    AutonoxSyncConfigModel,
    DEFAULT_BATCH_SIZE,
    DEFAULT_ENQUEUE_LIMIT,
    DEFAULT_AUTONOX_API_URL,
    DEFAULT_INTEGRATION_START_DATE,
    DEFAULT_MAX_ATTEMPTS,
)

logger = logging.getLogger(__name__)

INITIAL_EMPRESA_SEEDS = [
    {
        "codigo_empresa": 2,
        "sigla": "GPBB",
        "marca": "BMW",
        "api_key_env_var": "AUTONOX_API_KEY_EMP_2",
        "default_api_key": "nox_sk_704L7xUmOG9zXxWr-1qhx8SfkFgO4OJY",
        "is_active": True,
    },
    {
        "codigo_empresa": 3,
        "sigla": "GPBL",
        "marca": "BMW",
        "api_key_env_var": "AUTONOX_API_KEY_EMP_3",
        "default_api_key": "nox_sk_8WkdJ7ZKzsieAGGLMRW3rt55X1z7OhZV",
        "is_active": True,
    },
    {
        "codigo_empresa": 5,
        "sigla": "GPLB",
        "marca": "LAND ROVER",
        "api_key_env_var": "AUTONOX_API_KEY_EMP_4",
        "default_api_key": "nox_sk_mZpOf3yp1XCaLVidayIr_VskAbaEfuvf",
        "is_active": True,
    },
]


def seed_config(engine: Engine = default_engine) -> int:
    """
    Popula a tabela autonox_empresa_config com as empresas/lojas iniciais se ainda não existirem.

    Returns:
        int: Quantidade de registros inseridos/atualizados na seed.
    """
    query = text(
        """
        INSERT INTO autonox_empresa_config (
            codigo_empresa, sigla, marca, api_key, is_active, created_at, updated_at
        )
        VALUES (
            :codigo_empresa, :sigla, :marca, :api_key, :is_active,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (codigo_empresa) DO UPDATE
        SET sigla = EXCLUDED.sigla,
            marca = EXCLUDED.marca,
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP
    """
    )

    global_api_key = os.getenv("AUTONOX_API_KEY", "")
    api_url = os.getenv("AUTONOX_API_URL") or DEFAULT_AUTONOX_API_URL
    start_date_value = os.getenv("INTEGRATION_START_DATE")
    inserted_count = 0

    with engine.begin() as conn:
        from include.data.models.autonox_empresa_config_model import (
            AutonoxEmpresaConfigModel,
        )

        AutonoxEmpresaConfigModel.__table__.create(bind=conn, checkfirst=True)
        AutonoxSyncConfigModel.__table__.create(bind=conn, checkfirst=True)
        sync_columns = {
            column["name"]
            for column in inspect(conn).get_columns("autonox_sync_config")
        }
        if "api_url" not in sync_columns:
            conn.execute(
                text(
                    "ALTER TABLE autonox_sync_config "
                    "ADD COLUMN api_url VARCHAR(2048) NOT NULL DEFAULT ''"
                )
            )
        conn.execute(
            text(
                """
                UPDATE autonox_sync_config
                SET api_url = :api_url
                WHERE config_id = 1 AND (api_url IS NULL OR api_url = '')
                """
            ),
            {"api_url": api_url},
        )
        company_columns = {
            column["name"]
            for column in inspect(conn).get_columns("autonox_empresa_config")
        }
        legacy_start_date = None
        if "data_inicial_integracao" in company_columns:
            legacy_start_date = conn.execute(
                text(
                    """
                    SELECT MIN(data_inicial_integracao)
                    FROM autonox_empresa_config
                    WHERE is_active = TRUE
                    """
                )
            ).scalar_one_or_none()

        initial_start_date = (
            legacy_start_date
            or (date.fromisoformat(start_date_value) if start_date_value else None)
            or DEFAULT_INTEGRATION_START_DATE
        )
        conn.execute(
            text(
                """
                INSERT INTO autonox_sync_config (
                    config_id, enqueue_limit, batch_size, max_attempts, api_url,
                    data_inicial_integracao
                )
                VALUES (
                    1, :enqueue_limit, :batch_size, :max_attempts, :api_url,
                    :data_inicial_integracao
                )
                ON CONFLICT (config_id) DO NOTHING
                """
            ),
            {
                "enqueue_limit": DEFAULT_ENQUEUE_LIMIT,
                "batch_size": DEFAULT_BATCH_SIZE,
                "max_attempts": DEFAULT_MAX_ATTEMPTS,
                "api_url": api_url,
                "data_inicial_integracao": initial_start_date,
            },
        )

        if "data_inicial_integracao" in company_columns:
            conn.execute(
                text(
                    "ALTER TABLE autonox_empresa_config "
                    "DROP COLUMN data_inicial_integracao"
                )
            )

        for item in INITIAL_EMPRESA_SEEDS:
            env_key = os.getenv(item["api_key_env_var"], "")
            api_key = env_key or global_api_key or item["default_api_key"]

            result = conn.execute(
                query,
                {
                    "codigo_empresa": item["codigo_empresa"],
                    "sigla": item["sigla"],
                    "marca": item["marca"],
                    "api_key": api_key,
                    "is_active": item["is_active"],
                },
            )
            inserted_count += result.rowcount

    logger.info(
        "Seed de configuração Autonox executada. "
        f"Registros de empresa afetados: {inserted_count}"
    )
    return inserted_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_config()

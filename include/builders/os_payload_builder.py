import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from include.infra.postgres_database import engine as default_engine
from include.data.schemas.autonox_payload_schema import (
    AutonoxOSPayload,
    ReclamacaoItem,
    ServicoItem,
    PecaItem,
    NotaFiscalItem,
)

logger = logging.getLogger(__name__)


class OSPayloadBuilder:
    """
    Construtor responsável por consultar as tabelas de staging no PostgreSQL
    e consolidar todos os dados de uma Ordem de Serviço (capa + coleções)
    no formato do contrato da API Autonox.
    """

    def __init__(self, db_engine: Optional[Engine] = None, marca_default: str = "BMW"):
        self.engine = db_engine or default_engine
        self.marca_default = marca_default

    def build_payload(
        self, cod_empresa: int, numero_os: int, marca: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Consolida a OS informada a partir das tabelas Postgres.
        Retorna o dicionário validado do payload ou None se a OS não for encontrada.
        """
        with self.engine.connect() as conn:
            # 1. Capa da OS
            query_capa = text(
                """
                SELECT 
                    oc.cod_empresa,
                    oc.numero_os,
                    lower(oc.status_os) as situacao,
                    oc.data_emissao,
                    coalesce(oc.data_encerramento, oc.data_cancelamento) as data_fechamento,
                    oc.chassi,
                    oc.placa,
                    oc.tipo_os,
                    oc.codigo_garantia,
                    oc.razao_social,
                    oc.responsavel,
                    oc.veic_modelo,
                    oc.ano,
                    oc.km,
                    oc.data_venda,
                    oc.total_pecas,
                    oc.total_servicos,
                    oc.valor_total
                FROM os_capa oc
                WHERE oc.cod_empresa = :cod_empresa AND oc.numero_os = :numero_os
                LIMIT 1
            """
            )
            capa = (
                conn.execute(
                    query_capa, {"cod_empresa": cod_empresa, "numero_os": numero_os}
                )
                .mappings()
                .first()
            )
            if not capa:
                logger.warning(
                    f"OS {numero_os} (empresa {cod_empresa}) não encontrada em os_capa."
                )
                return None

            # 2. Cliente
            query_cliente = text(
                """
                SELECT 
                    nome_cliente,
                    cpf_cnpj,
                    telefone,
                    celular
                FROM os_clientes
                WHERE cod_empresa = :cod_empresa AND numero_os = :numero_os
                LIMIT 1
            """
            )
            cliente = (
                conn.execute(
                    query_cliente, {"cod_empresa": cod_empresa, "numero_os": numero_os}
                )
                .mappings()
                .first()
                or {}
            )

            # 3. OS Relacionadas
            query_rel = text(
                """
                SELECT numero_os_irma
                FROM os_relacionadas
                WHERE cod_empresa = :cod_empresa AND numero_os = :numero_os
            """
            )
            rel_rows = conn.execute(
                query_rel, {"cod_empresa": cod_empresa, "numero_os": numero_os}
            ).fetchall()
            os_relacionadas = [str(r[0]) for r in rel_rows if r[0] is not None]

            # 4. Reclamações
            query_rec = text(
                """
                SELECT item, reclamacao as descricao
                FROM reclamacoes_ordem_servico
                WHERE cod_empresa = :cod_empresa AND numero_os = :numero_os
                ORDER BY item
            """
            )
            rec_rows = (
                conn.execute(
                    query_rec, {"cod_empresa": cod_empresa, "numero_os": numero_os}
                )
                .mappings()
                .all()
            )
            reclamacoes = [
                ReclamacaoItem(
                    item=str(r["item"]) if r["item"] is not None else None,
                    descricao=r["descricao"],
                )
                for r in rec_rows
            ]

            # 5. Serviços (Mão de Obra)
            query_serv = text(
                """
                SELECT 
                    codigo_servico as codigo,
                    cod_defeito,
                    descritivo,
                    valor
                FROM servicos_ordem_servico
                WHERE cod_empresa = :cod_empresa AND numero_os = :numero_os
            """
            )
            serv_rows = (
                conn.execute(
                    query_serv, {"cod_empresa": cod_empresa, "numero_os": numero_os}
                )
                .mappings()
                .all()
            )
            servicos = [
                ServicoItem(
                    codigo=str(r["codigo"]) if r["codigo"] is not None else None,
                    codigo_defeito=(
                        str(r["cod_defeito"]) if r["cod_defeito"] is not None else None
                    ),
                    descritivo=r["descritivo"],
                    valor=float(r["valor"]) if r["valor"] is not None else None,
                )
                for r in serv_rows
            ]

            # 6. Peças (Itens)
            query_pecas = text(
                """
                SELECT 
                    cod_item as codigo,
                    descricao,
                    qtde_peca as quantidade,
                    valor_os as valor
                FROM itens_ordem_servico
                WHERE cod_empresa = :cod_empresa AND numero_os = :numero_os
            """
            )
            pecas_rows = (
                conn.execute(
                    query_pecas, {"cod_empresa": cod_empresa, "numero_os": numero_os}
                )
                .mappings()
                .all()
            )
            pecas = [
                PecaItem(
                    codigo=str(r["codigo"]) if r["codigo"] is not None else None,
                    descricao=r["descricao"],
                    quantidade=(
                        float(r["quantidade"]) if r["quantidade"] is not None else None
                    ),
                    valor=float(r["valor"]) if r["valor"] is not None else None,
                )
                for r in pecas_rows
            ]

            # Totais pré-calculados pela query Oracle (os_capa)
            tot_pecas = (
                float(capa["total_pecas"]) if capa["total_pecas"] is not None else None
            )
            tot_servicos = (
                float(capa["total_servicos"])
                if capa["total_servicos"] is not None
                else None
            )
            tot_geral = (
                float(capa["valor_total"]) if capa["valor_total"] is not None else None
            )
            # Notas fiscais
            query_notas = text(
                """
                SELECT 
                    nr_nota_fiscal as numero,
                    case 
                        when tipo_nota_fiscal = '1' then 'servico'
                        when tipo_nota_fiscal = '2' then 'peca'
                        else '0'
                    end as tipo,
                    data_referencia as data,
                    valor
                FROM notas_fiscais_ordem_servico
                WHERE cod_empresa = :cod_empresa AND numero_os = :numero_os
            """
            )
            notas_rows = (
                conn.execute(
                    query_notas, {"cod_empresa": cod_empresa, "numero_os": numero_os}
                )
                .mappings()
                .all()
            )
            notas_fiscais = [
                NotaFiscalItem(
                    numero=str(r["numero"]) if r["numero"] is not None else None,
                    tipo=str(r["tipo"]) if r["tipo"] is not None else None,
                    data=str(r["data"].strftime("%Y-%m-%d")) if r["data"] is not None else None,
                    valor=float(r["valor"]) if r["valor"] is not None else None,
                )
                for r in notas_rows
            ]
            # Montagem do objeto Pydantic
            payload_obj = AutonoxOSPayload(
                marca=marca or self.marca_default,
                numero_os=str(capa["numero_os"]),
                situacao=capa["situacao"],
                data_os=(
                    capa["data_emissao"].strftime("%Y-%m-%d")
                    if capa["data_emissao"]
                    else None
                ),
                data_fechamento=(
                    capa["data_fechamento"].strftime("%Y-%m-%d")
                    if capa["data_fechamento"]
                    else None
                ),
                chassi=capa["chassi"],
                placa=capa["placa"],
                os_tipo=capa["tipo_os"],
                codigo_garantia=capa["codigo_garantia"],
                os_razao_social=capa["razao_social"],
                os_relacionadas=os_relacionadas,
                consultor_nome=capa["responsavel"],
                cliente_nome=cliente.get("nome_cliente"),
                cliente_cpf_cnpj=(
                    str(cliente.get("cpf_cnpj")) if cliente.get("cpf_cnpj") else None
                ),
                cliente_telefone=(
                    str(cliente.get("telefone")) if cliente.get("telefone") else None
                ),
                cliente_celular=(
                    str(cliente.get("celular")) if cliente.get("celular") else None
                ),
                veiculo_modelo=capa["veic_modelo"],
                veiculo_ano=str(capa["ano"]) if capa["ano"] is not None else None,
                veiculo_km=str(capa["km"]) if capa["km"] is not None else None,
                data_venda=(
                    capa["data_venda"].strftime("%Y-%m-%d")
                    if capa["data_venda"]
                    else None
                ),
                reclamacoes=reclamacoes,
                servicos=servicos,
                pecas=pecas,
                valor_pecas=round(tot_pecas, 2) if tot_pecas is not None else None,
                valor_mao_obra=(
                    round(tot_servicos, 2) if tot_servicos is not None else None
                ),
                valor_total=round(tot_geral, 2) if tot_geral is not None else None,
                notas_fiscais=notas_fiscais,
            )

            # Dump para dicionário (excluindo None nulos irrelevantes se desejado, mas mantendo estrutura limpa)
            return payload_obj.model_dump(exclude_none=True)

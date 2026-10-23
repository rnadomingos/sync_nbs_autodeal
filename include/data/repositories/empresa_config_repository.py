import logging
from typing import Tuple
from sqlalchemy import text
from include.infra.postgres_database import engine as default_engine

logger = logging.getLogger(__name__)


def get_active_empresa_ids(engine=None) -> Tuple[int, ...]:
    """
    Consulta a tabela autonox_empresa_config no PostgreSQL e retorna uma tupla
    com os 'codigo_empresa' de todas as lojas com is_active = True.

    Esta função é utilizada para compor dinamicamente o filtro
    'AND os.cod_empresa IN (...)' nas queries de extração do Oracle,
    evitando a necessidade de hardcodar os códigos de empresa nos SQLs.

    Args:
        engine: SQLAlchemy engine do PostgreSQL. Se None, usa o engine padrão.

    Returns:
        Tuple[int, ...]: Tupla com os códigos de empresa ativos.
                         Retorna uma tupla vazia se nenhuma empresa estiver ativa
                         ou em caso de erro.

    Raises:
        Não propaga exceções — retorna tupla vazia com log de warning em caso de falha.
    """
    db_engine = engine or default_engine
    query = text(
        """
        SELECT codigo_empresa
        FROM autonox_empresa_config
        WHERE is_active = TRUE
        ORDER BY codigo_empresa
        """
    )
    try:
        with db_engine.connect() as conn:
            rows = conn.execute(query).fetchall()
            empresa_ids = tuple(row[0] for row in rows)
            if not empresa_ids:
                logger.warning(
                    "Nenhuma empresa ativa encontrada na tabela autonox_empresa_config. "
                    "As queries Oracle serão executadas sem filtro de empresa."
                )
            else:
                logger.info(
                    f"Empresas ativas carregadas para filtro de extração Oracle: {empresa_ids}"
                )
            return empresa_ids
    except Exception as e:
        logger.error(
            f"Erro ao buscar empresas ativas em autonox_empresa_config: {e}. "
            "Retornando tupla vazia — nenhum dado será extraído do Oracle."
        )
        return ()


def format_empresa_ids_for_sql(empresa_ids: Tuple[int, ...]) -> str:
    """
    Formata uma tupla de códigos de empresa para uso seguro em cláusula SQL IN.

    Garante que os valores sejam inteiros antes de formatar a string,
    prevenindo injeção de SQL.

    Args:
        empresa_ids: Tupla de inteiros com os códigos de empresa.

    Returns:
        str: String formatada para uso em cláusula IN, ex: '2, 3, 5'.
             Retorna '0' se a tupla estiver vazia (resultará em zero linhas extraídas).

    Example:
        >>> format_empresa_ids_for_sql((2, 3, 5))
        '2, 3, 5'
        >>> format_empresa_ids_for_sql(())
        '0'
    """
    if not empresa_ids:
        return "0"
    # Garante que apenas inteiros sejam formatados (sanitização)
    sanitized = [int(eid) for eid in empresa_ids]
    return ", ".join(str(eid) for eid in sanitized)

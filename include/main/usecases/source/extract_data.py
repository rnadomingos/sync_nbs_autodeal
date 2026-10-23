from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import TextClause, text
from include.infra.oracle_database import engine
from include.data.repositories.empresa_config_repository import (
    get_active_empresa_ids,
    format_empresa_ids_for_sql,
)
from typing import TypeVar, Dict, Optional, Tuple, Union
from tqdm import tqdm
import pandera.pandas as pa
import pandas as pd


Base = declarative_base()

# TypeVar to data_model
BaseModel = TypeVar("T", bound=Base)  # type: ignore

# Placeholder utilizado nas queries Oracle para ser substituído pelos
# códigos de empresa ativos consultados dinamicamente no PostgreSQL.
EMPRESA_IDS_PLACEHOLDER = "{empresa_ids}"


class ExtractData:
    def __init__(
        self,
        query: Union[TextClause, str],
        query_params: Dict,
        empresa_ids: Optional[Tuple[int, ...]] = None,
    ) -> None:
        """
        Inicializa o extrator de dados do Oracle.

        Args:
            query: TextClause ou string SQL raw. Quando string, pode conter o
                   placeholder '{empresa_ids}' que será substituído pelos códigos
                   de empresa ativos consultados no PostgreSQL (autonox_empresa_config).
            query_params: Dicionário de parâmetros bindados da query (ex: {'max_date': '...'}).
            empresa_ids: Tupla opcional de códigos de empresa para substituir o placeholder.
                         Se None e a query contiver '{empresa_ids}', os IDs serão buscados
                         automaticamente no PostgreSQL.
        """
        self.query = self._resolve_query(query, empresa_ids)
        self.query_params = query_params

    @staticmethod
    def _resolve_query(
        query: Union[TextClause, str],
        empresa_ids: Optional[Tuple[int, ...]],
    ) -> TextClause:
        """
        Resolve a query final substituindo '{empresa_ids}' pelos códigos ativos.

        Quando a query é uma string contendo o placeholder '{empresa_ids}',
        os códigos de empresa são buscados no PostgreSQL (autonox_empresa_config
        WHERE is_active = TRUE) e injetados de forma segura na string SQL —
        apenas inteiros são permitidos, prevenindo SQL injection.

        Args:
            query: TextClause já compilado ou string SQL raw.
            empresa_ids: Tupla com os códigos de empresa, ou None para buscar do Postgres.

        Returns:
            TextClause pronto para execução via SQLAlchemy.
        """
        if isinstance(query, TextClause):
            return query

        # É uma string raw — verifica se contém o placeholder
        if EMPRESA_IDS_PLACEHOLDER in query:
            ids = empresa_ids if empresa_ids is not None else get_active_empresa_ids()
            ids_str = format_empresa_ids_for_sql(ids)
            query = query.replace(EMPRESA_IDS_PLACEHOLDER, ids_str)

        return text(query)

    def get_data_nbs(self, schema: pa.DataFrameModel, lazy: bool = True) -> pd.DataFrame:
        """
        Executes a SQL query and returns the result as a validated DataFrame.

        This method runs a parameterized SQL query using SQLAlchemy, retrieves the result
        as a pandas DataFrame, and validates it against the provided Pandera schema model.

        Args:
            schema (pa.DataFrameModel): A Pandera schema model used to validate the output DataFrame.
            lazy (bool, optional): If True, collects all validation errors before raising. Defaults to True.

        Returns:
            pd.DataFrame: The resulting DataFrame from the SQL query, validated against the given schema.

        Raises:
            SQLAlchemyError: If an error occurs during the SQL execution.
            SchemaError: If the DataFrame does not conform to the provided schema.
        """
        try:
            with engine.connect() as conn:
                tqdm.pandas()
                dataframe = pd.read_sql(self.query, conn, params=self.query_params)
                validate_df = schema.to_schema().validate(dataframe, lazy=lazy)
                return validate_df
        except SQLAlchemyError as e:
            print("Erro ao carregar os dados:")
            print(e.__class__.__name__, "-", e._message)
            raise
        return pd.DataFrame()

    def get_data_infer_schema_nbs(self) -> pd.DataFrame:
        """
        Executa a query SQL definida na instância e retorna o resultado como um DataFrame.

        Esta função estabelece uma conexão com o banco de dados usando o `engine`,
        executa a consulta SQL armazenada em `self.query` com os parâmetros `self.query_params`,
        e retorna o resultado em um objeto `pandas.DataFrame`.

        Caso ocorra um erro durante a execução da consulta, o erro é exibido no console
        e a exceção original é relançada.

        Returns:
            pd.DataFrame: DataFrame contendo os resultados da consulta.
            Retorna um DataFrame vazio se nenhum dado for obtido.

        Raises:
            SQLAlchemyError: Se ocorrer qualquer erro durante a execução da consulta SQL
            ou durante a conexão com o banco de dados.

        Example:
            >>> df = obj.get_data_infer_schema_nbs()
            >>> print(df.head())
        """
        try:
            with engine.connect() as conn:
                dataframe = pd.read_sql(self.query, conn, params=self.query_params)
                return dataframe
        except SQLAlchemyError as e:
            print("Erro ao carregar os dados:")
            print(e.__class__.__name__, "-", e._message)
            raise
        return pd.DataFrame()

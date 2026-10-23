import pandera.pandas as pa
from datetime import datetime


class OSCapaSchema(pa.DataFrameModel):
    """
    Validation schema for OS Capa data using Pandera.

    This schema defines the expected structure and constraints for the OS (Order of Service) header data.
    It is intended to validate pandas DataFrames loaded from external sources (e.g., SQL queries) to
    ensure data quality and type consistency before further processing.

    Attributes:
        cod_empresa (Series[int]): Company identifier. Must be between 2 and 4.
        numero_os (Series[int]): Service order number. Must be a non-negative integer.
        os_original (Series[str]): Indicates if the order is original.
        data_emissao (Series[datetime]): Emission date. Must be on or after 2024-10-21.
        data_encerramento (Series[str]): Closing date. Nullable.
        data_cancelamento (Series[str]): Cancellation date. Nullable.
        razao_social (Series[str]): Customer or company name.
        tipo_os (Series[str]): Type of service order.
        responsavel (Series[str]): Responsible person or technician.
        chassi (Series[str]): Vehicle chassis number.
        veic_modelo (Series[str]): Vehicle model.
        ano (Series[str]): Vehicle year.
        km (Series[int]): Vehicle mileage. Must be non-negative.
        placa (Series[str]): License plate. Nullable.
        data_venda (Series[datetime]): Sale date. Must be on or after 1899-12-30. Nullable.
        status_os (Series[str]): Status of the service order.
        numero_do_dealer (Series[str]): Dealer identification number.
        codigo_garantia (Series[str]): Warranty code (tipo_fabrica). Nullable.
        total_pecas (Series[float]): Total parts value after discount. Must be non-negative.
        total_servicos (Series[float]): Total services value after discount. Must be non-negative.
        valor_total (Series[float]): Total estimated service order value. Must be non-negative.

    Config:
        coerce (bool): Automatically convert column types where possible.
        strict (bool): Require that all defined columns exist in the input DataFrame.
        unique_column_names (bool): Disable check for unique column names.
    """

    cod_empresa: int = pa.Field(ge=0)
    numero_os: int = pa.Field(ge=0)
    os_original: str
    data_emissao: datetime = pa.Field(ge="2024-10-21")
    data_encerramento: str = pa.Field(nullable=True)
    data_cancelamento: str = pa.Field(nullable=True)
    razao_social: str
    tipo_os: str
    responsavel: str
    chassi: str
    veic_modelo: str
    ano: str
    km: int = pa.Field(ge=0)
    placa: str = pa.Field(nullable=True)
    data_venda: datetime = pa.Field(ge="1899-12-30", nullable=True)
    status_os: str
    numero_do_dealer: str
    codigo_garantia: str = pa.Field(nullable=True)
    total_pecas: float = pa.Field(ge=0)
    total_servicos: float = pa.Field(ge=0)
    valor_total: float = pa.Field(ge=0)

    class Config:
        coerce = True
        strict = True
        unique_column_names = False

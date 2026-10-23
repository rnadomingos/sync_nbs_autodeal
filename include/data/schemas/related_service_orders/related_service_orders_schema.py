import pandas as pd
import pandera.pandas as pa
from pandera.typing import Index
from pandera import Field


class RelatedServiceOrderSchema(pa.DataFrameModel):
    """
    Schema for validating related service order data.

    Validates company code, main service order number, and the related
    service order number with defined ranges and nullability rules.
    """

    cod_empresa: int = Field(ge=0, nullable=False)
    numero_os: int = Field(ge=0, nullable=False)
    numero_os_irma: pd.Int64Dtype = Field(
        ge=0, nullable=True
    )  # pd.Int64Dtype para validar nullable com números inteiros

    # Index validation
    __index__: Index[int] = Field(ge=0, nullable=False)

    class Config:
        coerce = True
        strict = False

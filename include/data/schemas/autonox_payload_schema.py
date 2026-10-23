from typing import List, Optional
from pydantic import BaseModel, Field


class ReclamacaoItem(BaseModel):
    """
    Modelo para os itens de reclamação da OS no Autonox.
    """

    item: Optional[str] = None
    descricao: Optional[str] = None


class ServicoItem(BaseModel):
    """
    Modelo para os serviços (mão de obra) da OS no Autonox.
    """

    codigo: Optional[str] = None
    codigo_defeito: Optional[str] = None
    descritivo: Optional[str] = None
    valor: Optional[float] = None


class PecaItem(BaseModel):
    """
    Modelo para as peças da OS no Autonox.
    """

    codigo: Optional[str] = None
    descricao: Optional[str] = None
    quantidade: Optional[float] = None
    valor: Optional[float] = None


class NotaFiscalItem(BaseModel):
    """
    Modelo para as notas fiscais da OS no Autonox.
    """

    numero: Optional[str] = None
    tipo: Optional[str] = None
    data: Optional[str] = None
    valor: Optional[float] = None


class AutonoxOSPayload(BaseModel):
    """
    Modelo Pydantic que espelha o contrato completo da API de Ingestão de OS do Autonox.
    Apenas 'marca' e 'numero_os' são campos obrigatórios de acordo com a documentação oficial.
    """

    marca: str = Field(..., description="Marca / montadora da OS (ex.: 'BMW')")
    numero_os: str = Field(
        ..., description="Número da Ordem de Serviço (Chave de Idempotência)"
    )

    situacao: Optional[str] = Field(None, description="Situação da OS")
    data_os: Optional[str] = Field(
        None, description="Data de emissão da OS (AAAA-MM-DD)"
    )
    data_fechamento: Optional[str] = Field(
        None, description="Data de fechamento da OS (AAAA-MM-DD)"
    )
    chassi: Optional[str] = Field(None, description="Chassi / VIN (17 caracteres)")
    placa: Optional[str] = Field(None, description="Placa do veículo")
    os_tipo: Optional[str] = Field(None, description="Tipo da OS / garantia")
    codigo_garantia: Optional[str] = Field(
        None, description="Código de garantia da fábrica"
    )
    os_razao_social: Optional[str] = Field(
        None, description="Razão social da concessionária"
    )
    os_relacionadas: Optional[List[str]] = Field(
        default_factory=list, description="Números de OS relacionadas"
    )

    consultor_nome: Optional[str] = Field(None, description="Consultor / responsável")
    cliente_nome: Optional[str] = Field(None, description="Nome do proprietário")
    cliente_cpf_cnpj: Optional[str] = Field(None, description="CPF ou CNPJ")
    cliente_telefone: Optional[str] = Field(None, description="Telefone fixo")
    cliente_celular: Optional[str] = Field(None, description="Telefone celular")

    veiculo_modelo: Optional[str] = Field(None, description="Modelo do veículo")
    veiculo_ano: Optional[str] = Field(None, description="Ano / modelo do veículo")
    veiculo_km: Optional[str] = Field(None, description="Quilometragem")
    data_venda: Optional[str] = Field(None, description="Data da venda (AAAA-MM-DD)")

    reclamacoes: Optional[List[ReclamacaoItem]] = Field(
        default_factory=list, description="Lista de reclamações"
    )
    servicos: Optional[List[ServicoItem]] = Field(
        default_factory=list, description="Lista de serviços (mão de obra)"
    )
    pecas: Optional[List[PecaItem]] = Field(
        default_factory=list, description="Lista de peças"
    )

    valor_pecas: Optional[float] = Field(None, description="Valor total de peças")
    valor_mao_obra: Optional[float] = Field(
        None, description="Valor total de mão de obra"
    )
    valor_total: Optional[float] = Field(None, description="Valor total geral da OS")
    notas_fiscais: Optional[List[NotaFiscalItem]] = Field(
        default_factory=list, description="Lista de notas fiscais"
    )

    sg_numero: Optional[str] = Field(None, description="Número da SG / Claim")
    oc_numero: Optional[str] = Field(None, description="Número da Ordem de Crédito")
    po_numero: Optional[str] = Field(None, description="Número do PO")
    nd_numero: Optional[str] = Field(None, description="Número da Nota de Débito")

    class Config:
        json_schema_extra = {
            "example": {
                "marca": "BMW",
                "numero_os": "82251",
                "situacao": "aberta",
                "data_os": "2024-04-16",
                "data_fechamento": "",
                "chassi": "98MJJ7009K4A85624",
                "placa": "ABC1D23",
                "os_tipo": "B2 GARANTIA AUTOS BMW - 2",
                "codigo_garantia": "G1",
                "os_razao_social": "GRAND POINT COMERCIO DE VEICULOS LTDA",
                "os_relacionadas": ["82250"],
                "consultor_nome": "Fulano de Tal",
                "cliente_nome": "C L DA SILVA",
                "cliente_cpf_cnpj": "12345678000190",
                "veiculo_modelo": "320i",
                "veiculo_ano": "2024",
                "veiculo_km": "15320",
                "data_venda": "2023-02-10",
                "reclamacoes": [{"item": "01", "descricao": "Ruido na suspensao"}],
                "servicos": [
                    {
                        "codigo": "0000618",
                        "codigo_defeito": "3213023900",
                        "descritivo": "Diagnostico",
                        "valor": 345.38,
                    }
                ],
                "pecas": [
                    {
                        "codigo": "34208882958",
                        "descricao": "Pastilha de freio",
                        "quantidade": 1,
                        "valor": 1413.54,
                    }
                ],
                "valor_pecas": 1413.54,
                "valor_mao_obra": 345.38,
                "valor_total": 1758.92,
                "notas_fiscais": [
                    {
                        "numero": "45120",
                        "tipo": "peca",
                        "data": "2026-10-15",
                        "valor": 1413.54,
                    },
                    {
                        "numero": "45121",
                        "tipo": "servico",
                        "data": "2026-10-15",
                        "valor": 500.54,
                    },
                ],
            }
        }

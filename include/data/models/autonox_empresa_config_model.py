from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime
import pytz

Base = declarative_base()

class AutonoxEmpresaConfigModel(Base):
    """
    Modelo ORM para a tabela de configuração de empresas/lojas para a integração Autonox.
    
    Attributes:
        codigo_empresa (int): Código identificador da empresa/loja no DMS NBS (chave primária).
        sigla (str): Sigla ou identificador abreviado da loja.
        marca (str): Marca veicular associada à loja (ex: 'BMW', 'MINI').
        api_key (str): Chave de API exclusiva fornecida pelo Autonox para a loja.
        is_active (bool): Status de ativação da integração para a loja.
        created_at (datetime): Data/hora de inserção do registro.
        updated_at (datetime): Data/hora da última atualização.
    """
    def now_utc_minus_3(self):
        return datetime.now(pytz.timezone("America/Sao_Paulo"))

    __tablename__ = "autonox_empresa_config"

    codigo_empresa = Column(Integer, primary_key=True)
    sigla = Column(String(50), nullable=False)
    marca = Column(String(50), nullable=False, default="BMW")
    api_key = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=now_utc_minus_3)
    updated_at = Column(DateTime(timezone=True), default=now_utc_minus_3, onupdate=now_utc_minus_3)

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base
from datetime import datetime
import pytz

Base = declarative_base()

class AutonoxOutboxModel(Base):
    """
    Modelo ORM para a tabela de controle de envio de OS para a API Autonox (Outbox Pattern).
    
    Attributes:
        cod_empresa (int): Identificador da empresa no DMS NBS.
        numero_os (int): Número da Ordem de Serviço.
        status (str): Estado da entrega ('pending', 'sent', 'error', 'failed_dead_letter').
        payload (JSON): Objeto JSON completo da OS gerado para ingestão.
        attempts (int): Contador de tentativas de envio.
        last_error (str): Mensagem de erro do último envio (se houver).
        response_status_code (int): Código HTTP retornado pela última requisição.
        response_message (str): Mensagem devolvida pela API ou erro da requisição.
        processo_id (str): ID do processo de garantia retornado pela API Autonox.
        created_at (datetime): Data/hora de criação na fila outbox.
        updated_at (datetime): Data/hora de última atualização.
        sent_at (datetime): Data/hora do envio com sucesso.
    """
    def now_utc_minus_3(self):
        return datetime.now(pytz.timezone("America/Sao_Paulo"))

    __tablename__ = "autonox_outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cod_empresa = Column(Integer, nullable=False)
    numero_os = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    payload = Column(JSON, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    response_status_code = Column(Integer, nullable=True)
    response_message = Column(Text, nullable=True)
    processo_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=now_utc_minus_3)
    updated_at = Column(DateTime(timezone=True), default=now_utc_minus_3, onupdate=now_utc_minus_3)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("cod_empresa", "numero_os", name="uq_autonox_outbox_empresa_os"),
    )

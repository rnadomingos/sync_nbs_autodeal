from datetime import date

from sqlalchemy import CheckConstraint, Column, Date, Integer
from sqlalchemy.orm import declarative_base

DEFAULT_ENQUEUE_LIMIT = 500
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_INTEGRATION_START_DATE = date(2026, 10, 10)

Base = declarative_base()


class AutonoxSyncConfigModel(Base):
    __tablename__ = "autonox_sync_config"
    __table_args__ = (
        CheckConstraint("config_id = 1", name="ck_autonox_sync_config_singleton"),
        CheckConstraint("enqueue_limit > 0", name="ck_autonox_sync_config_enqueue_limit"),
        CheckConstraint("batch_size > 0", name="ck_autonox_sync_config_batch_size"),
        CheckConstraint("max_attempts > 0", name="ck_autonox_sync_config_max_attempts"),
    )

    config_id = Column(Integer, primary_key=True)
    enqueue_limit = Column(Integer, nullable=False, default=DEFAULT_ENQUEUE_LIMIT)
    batch_size = Column(Integer, nullable=False, default=DEFAULT_BATCH_SIZE)
    max_attempts = Column(Integer, nullable=False, default=DEFAULT_MAX_ATTEMPTS)
    data_inicial_integracao = Column(
        Date, nullable=False, default=DEFAULT_INTEGRATION_START_DATE
    )

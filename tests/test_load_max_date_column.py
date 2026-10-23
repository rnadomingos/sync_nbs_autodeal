from datetime import date

from sqlalchemy import Column, Date, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from include.main.usecases.destination import load_max_date_column


Base = declarative_base()


class ServiceOrder(Base):
    __tablename__ = "test_service_orders"

    id = Column(Integer, primary_key=True)
    integration_date = Column(Date)


class SyncConfig(Base):
    __tablename__ = "autonox_sync_config"

    config_id = Column(Integer, primary_key=True)
    data_inicial_integracao = Column(Date)


def test_load_max_date_uses_global_start_date_when_destination_is_empty(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        session.add(
            SyncConfig(
                config_id=1,
                data_inicial_integracao=date(2026, 9, 1),
            )
        )
        session.commit()
    monkeypatch.setattr(
        load_max_date_column, "PostgresSessionLocal", session_factory
    )

    result = load_max_date_column.TableTools().loadMaxDateColumn(
        ServiceOrder.integration_date
    )

    assert result == {"max_date": "2026-09-01"}

    with session_factory() as session:
        session.add(ServiceOrder(integration_date=date(2026, 11, 5)))
        session.commit()

    result = load_max_date_column.TableTools().loadMaxDateColumn(
        ServiceOrder.integration_date
    )

    assert result == {"max_date": "2026-11-05"}

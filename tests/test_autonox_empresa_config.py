import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from include.data.models.autonox_empresa_config_model import AutonoxEmpresaConfigModel, Base
from include.data.models.autonox_sync_config_model import AutonoxSyncConfigModel
from include.data.seeds.seed_config import seed_config, INITIAL_EMPRESA_SEEDS
from include.clients.autonox_client import AutonoxHttpClient
from include.services.sync_service import SyncService


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_sync_service_creates_outbox_table(memory_db):
    SyncService(db_engine=memory_db)

    with memory_db.connect() as connection:
        connection.execute(text("SELECT * FROM autonox_outbox"))


def test_autonox_empresa_config_model_creation(memory_db):
    Session = sessionmaker(bind=memory_db)
    session = Session()

    config = AutonoxEmpresaConfigModel(
        codigo_empresa=10,
        sigla="TST",
        marca="BMW",
        api_key="secret_test_key",
        is_active=True
    )
    session.add(config)
    session.commit()

    retrieved = session.query(AutonoxEmpresaConfigModel).filter_by(codigo_empresa=10).first()
    assert retrieved is not None
    assert retrieved.sigla == "TST"
    assert retrieved.marca == "BMW"
    assert retrieved.api_key == "secret_test_key"
    assert retrieved.is_active is True


def test_seed_config(memory_db, monkeypatch):
    monkeypatch.setenv("INTEGRATION_START_DATE", "2026-08-01")
    monkeypatch.setenv("AUTONOX_API_URL", "https://example.com/autonox/os")
    inserted_count = seed_config(memory_db)
    assert inserted_count >= len(INITIAL_EMPRESA_SEEDS)

    Session = sessionmaker(bind=memory_db)
    session = Session()

    emp2 = session.query(AutonoxEmpresaConfigModel).filter_by(codigo_empresa=2).first()
    assert emp2 is not None
    assert emp2.sigla == "GPBB"
    assert emp2.is_active is True
    assert emp2.api_key != ""
    sync_config = session.query(AutonoxSyncConfigModel).one()
    assert sync_config.enqueue_limit == 500
    assert sync_config.batch_size == 50
    assert sync_config.max_attempts == 5
    assert sync_config.api_url == "https://example.com/autonox/os"
    assert sync_config.data_inicial_integracao.isoformat() == "2026-08-01"


def test_seed_does_not_overwrite_existing_sync_config(memory_db, monkeypatch):
    monkeypatch.setenv("INTEGRATION_START_DATE", "2026-08-01")
    monkeypatch.setenv("AUTONOX_API_URL", "https://example.com/first")
    seed_config(memory_db)
    with memory_db.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE autonox_sync_config
                SET enqueue_limit = 100, batch_size = 20, max_attempts = 3
                WHERE config_id = 1
                """
            )
        )

    monkeypatch.setenv("INTEGRATION_START_DATE", "2026-09-01")
    monkeypatch.setenv("AUTONOX_API_URL", "https://example.com/second")
    seed_config(memory_db)
    service = SyncService(db_engine=memory_db)
    with sessionmaker(bind=memory_db)() as session:
        sync_config = session.query(AutonoxSyncConfigModel).one()
        assert sync_config.enqueue_limit == 100
        assert sync_config.batch_size == 20
        assert sync_config.max_attempts == 3
        assert sync_config.api_url == "https://example.com/first"
        assert sync_config.data_inicial_integracao.isoformat() == "2026-08-01"
    assert service.sync_config == {
        "enqueue_limit": 100,
        "batch_size": 20,
        "max_attempts": 3,
    }


def test_seed_migrates_legacy_start_date_to_sync_config(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE autonox_empresa_config (
                    codigo_empresa INTEGER PRIMARY KEY,
                    sigla VARCHAR(50) NOT NULL,
                    marca VARCHAR(50) NOT NULL,
                    api_key VARCHAR(255) NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    data_inicial_integracao DATE,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO autonox_empresa_config
                    (codigo_empresa, sigla, marca, api_key, is_active,
                     data_inicial_integracao)
                VALUES
                    (10, 'A', 'BMW', 'key', TRUE, '2026-09-01'),
                    (11, 'B', 'BMW', 'key', TRUE, '2026-08-01'),
                    (12, 'C', 'BMW', 'key', FALSE, '2026-01-01')
                """
            )
        )
    monkeypatch.setenv("INTEGRATION_START_DATE", "2026-10-01")

    seed_config(engine)

    with engine.connect() as connection:
        configured_date = connection.execute(
            text(
                "SELECT data_inicial_integracao FROM autonox_sync_config "
                "WHERE config_id = 1"
            )
        ).scalar_one()
        legacy_column_exists = connection.execute(
            text("PRAGMA table_info(autonox_empresa_config)")
        ).all()
    assert configured_date == "2026-08-01"
    assert "data_inicial_integracao" not in {column[1] for column in legacy_column_exists}


def test_seed_creates_config_table_for_new_database(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setenv("INTEGRATION_START_DATE", "2026-10-01")
    monkeypatch.setenv("AUTONOX_API_URL", "https://example.com/autonox/os")

    seed_config(engine)

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT enqueue_limit, batch_size, max_attempts, api_url,
                       data_inicial_integracao
                FROM autonox_sync_config WHERE config_id = 1
                """
            )
        ).one()
    assert row == (500, 50, 5, "https://example.com/autonox/os", "2026-10-01")


def test_seed_adds_api_url_to_existing_sync_config(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE autonox_sync_config (
                    config_id INTEGER PRIMARY KEY,
                    enqueue_limit INTEGER NOT NULL,
                    batch_size INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    data_inicial_integracao DATE NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO autonox_sync_config
                    (config_id, enqueue_limit, batch_size, max_attempts,
                     data_inicial_integracao)
                VALUES (1, 100, 20, 3, '2026-08-01')
                """
            )
        )
    monkeypatch.setenv("AUTONOX_API_URL", "https://example.com/migrated")

    seed_config(engine)

    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT api_url FROM autonox_sync_config WHERE config_id = 1"
            )
        ).scalar_one()
    assert row == "https://example.com/migrated"


def test_autonox_client_empresa_api_key():
    client = AutonoxHttpClient(api_url="http://mock-endpoint")
    
    # Test send_os with specific api_key (without real HTTP call by validating failure key handling or monkeypatch)
    success, status_code, resp_json, err_msg = client.send_os({"numero_os": "123"}, api_key=None)
    # When api_key is None and env has no default, should fail with 401
    assert success is False
    assert status_code == 401
    assert "AUTONOX_API_KEY não informada" in err_msg


def test_sync_service_empresa_config_fetching(memory_db):
    seed_config(memory_db)
    service = SyncService(db_engine=memory_db)

    configs = service.get_empresa_configs()
    assert 2 in configs
    assert configs[2]["sigla"] == "GPBB"

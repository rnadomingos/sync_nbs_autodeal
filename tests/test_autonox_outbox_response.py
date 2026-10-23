from sqlalchemy import create_engine, text

from include.services.sync_service import SyncService


def test_process_outbox_persists_request_status_and_message():
    engine = create_engine("sqlite:///:memory:")
    service = SyncService(db_engine=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO autonox_outbox
                    (cod_empresa, numero_os, status, attempts)
                VALUES (1, 123, 'pending', 0)
                """
            )
        )

    service.get_empresa_configs = lambda: {
        1: {"api_key": "test-key", "marca": "BMW"}
    }
    service.builder.build_payload = lambda *args, **kwargs: {"numero_os": 123}
    service.client.send_os = lambda *args, **kwargs: (
        False,
        422,
        {},
        "HTTPError 422: OS inválida",
    )

    result = service.process_outbox()

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT status, last_error, response_status_code, response_message
                FROM autonox_outbox
                WHERE cod_empresa = 1 AND numero_os = 123
                """
            )
        ).one()

    assert result == {"processed": 1, "success": 0, "failed": 1}
    assert row == (
        "error",
        "HTTPError 422: OS inválida",
        422,
        "HTTPError 422: OS inválida",
    )


def test_sync_service_adds_response_columns_to_existing_outbox():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE autonox_outbox (
                    id INTEGER PRIMARY KEY,
                    cod_empresa INTEGER NOT NULL,
                    numero_os INTEGER NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0
                )
                """
            )
        )

    SyncService(db_engine=engine)

    with engine.connect() as connection:
        columns = {
            column[1]
            for column in connection.execute(
                text("PRAGMA table_info(autonox_outbox)")
            )
        }

    assert "response_status_code" in columns
    assert "response_message" in columns


def test_process_outbox_persists_success_response_message():
    engine = create_engine("sqlite:///:memory:")
    service = SyncService(db_engine=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO autonox_outbox
                    (cod_empresa, numero_os, status, attempts)
                VALUES (1, 456, 'pending', 0)
                """
            )
        )

    service.get_empresa_configs = lambda: {
        1: {"api_key": "test-key", "marca": "BMW"}
    }
    service.builder.build_payload = lambda *args, **kwargs: {"numero_os": 456}
    service.client.send_os = lambda *args, **kwargs: (
        True,
        201,
        {"processo_id": "process-456", "message": "OS recebida"},
        None,
    )
    service._mark_os_capa_sent = lambda *args, **kwargs: None

    result = service.process_outbox()

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT status, response_status_code, response_message, processo_id
                FROM autonox_outbox
                WHERE cod_empresa = 1 AND numero_os = 456
                """
            )
        ).one()

    assert result == {"processed": 1, "success": 1, "failed": 0}
    assert row == ("sent", 201, "OS recebida", "process-456")

from unittest.mock import MagicMock

import pandas as pd
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import declarative_base

from include.main.usecases.destination import upsert_data


Base = declarative_base()


class ConflictOnlyModel(Base):
    __tablename__ = "upsert_conflict_only"

    id = Column(Integer, primary_key=True)
    key = Column(Integer, nullable=False)


class UpdatableModel(Base):
    __tablename__ = "upsert_with_business_data"

    id = Column(Integer, primary_key=True)
    key = Column(Integer, nullable=False)
    name = Column(String, nullable=False)


def _save_and_compile(monkeypatch, model, row):
    session_context = MagicMock()
    session = session_context.__enter__.return_value
    monkeypatch.setattr(
        upsert_data, "PostgresSessionLocal", lambda: session_context
    )

    upsert_data.UpsertData(
        data_frame=pd.DataFrame([row]),
        data_model=model,
        conflict_keys=["key"],
    ).save_data()

    session.commit.assert_called_once_with()
    statement = session.execute.call_args.args[0]
    return str(statement.compile(dialect=postgresql.dialect()))


def test_upsert_ignores_conflicts_when_model_has_no_updatable_columns(monkeypatch):
    sql = _save_and_compile(monkeypatch, ConflictOnlyModel, {"key": 1})

    assert "ON CONFLICT (key) DO NOTHING" in sql


def test_upsert_updates_business_columns_when_available(monkeypatch):
    sql = _save_and_compile(
        monkeypatch, UpdatableModel, {"key": 1, "name": "service order"}
    )

    assert "ON CONFLICT (key) DO UPDATE SET name = excluded.name" in sql

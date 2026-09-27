"""
GET /api/v1/pix/history deve usar PixLedger como fonte.

Estratégia: chamar get_history diretamente (sem TestClient), com um banco
SQLite isolado em memória, criado e destruído por teste.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "pix-history-ledger-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.pix_ledger import PixLedger
from app.api.v1.routes.pix import get_history


EXPECTED_KEYS = {
    "id",
    "tipo",
    "valor",
    "descricao",
    "taxa_percentual",
    "taxa_valor",
    "valor_liquido",
    "criado_em",
}


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _add_ledger(db, *, user_id, kind, amount, created_at, description=None):
    entry = PixLedger(
        user_id=user_id,
        kind=kind,
        amount=amount,
        description=description,
        created_at=created_at,
    )
    db.add(entry)
    db.commit()
    return entry


def _call(db, user_id):
    resp = get_history(current_user=SimpleNamespace(id=user_id), db=db)
    assert resp.status_code == 200
    return json.loads(resp.body)


def test_history_maps_ledger_rows(db_session):
    base = datetime(2026, 1, 10, 12, 0, 0)
    _add_ledger(
        db_session, user_id=1, kind="credit", amount=Decimal("100.50"),
        created_at=base, description="recebido",
    )
    _add_ledger(
        db_session, user_id=1, kind="debit", amount=Decimal("30.25"),
        created_at=base + timedelta(hours=1),
    )

    data = _call(db_session, 1)

    assert len(data) == 2
    for item in data:
        assert set(item.keys()) == EXPECTED_KEYS

    saida, entrada = data
    assert saida["tipo"] == "saida"
    assert saida["valor"] == 30.25
    assert saida["valor_liquido"] == 30.25
    assert saida["descricao"] == ""
    assert saida["taxa_percentual"] == 0.0
    assert saida["taxa_valor"] == 0.0
    assert saida["criado_em"].startswith("2026-01-10T13:00:00")

    assert entrada["tipo"] == "entrada"
    assert entrada["valor"] == 100.5
    assert entrada["valor_liquido"] == 100.5
    assert entrada["descricao"] == "recebido"
    assert entrada["criado_em"].startswith("2026-01-10T12:00:00")


def test_history_orders_by_created_at_then_id_desc(db_session):
    same_ts = datetime(2026, 1, 10, 12, 0, 0)
    older = _add_ledger(
        db_session, user_id=1, kind="credit", amount=Decimal("1"),
        created_at=same_ts - timedelta(days=1),
    )
    first_same = _add_ledger(
        db_session, user_id=1, kind="credit", amount=Decimal("2"),
        created_at=same_ts,
    )
    second_same = _add_ledger(
        db_session, user_id=1, kind="debit", amount=Decimal("3"),
        created_at=same_ts,
    )

    ids = [item["id"] for item in _call(db_session, 1)]

    assert ids == [second_same.id, first_same.id, older.id]


def test_history_limits_to_50_and_isolates_user(db_session):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(55):
        _add_ledger(
            db_session, user_id=1, kind="credit", amount=Decimal("1"),
            created_at=base + timedelta(minutes=i),
        )
    _add_ledger(
        db_session, user_id=2, kind="debit", amount=Decimal("999"),
        created_at=base + timedelta(days=1),
    )

    data = _call(db_session, 1)

    assert len(data) == 50
    assert all(item["valor"] == 1.0 for item in data)
    assert _call(db_session, 3) == []

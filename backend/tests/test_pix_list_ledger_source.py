"""
GET /api/v1/pix/list — fonte de dados (A2).

Antes da correção, a rota lia Transaction (alias PixTransaction):
- ignorava os créditos que só existem em pix_ledger;
- mostrava o valor bruto (sem tarifa) em vez do débito real do ledger;
- devolvia created_at sempre None (o modelo usa criado_em);
- em falha de banco respondia 200 com lista vazia.

Agora lê PixLedger, a fonte de verdade do saldo, mantendo o formato de
resposta, e responde 503 em falha de banco. Chama a função de rota
diretamente com SQLite em memória.
"""
import json
import os
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "pix-list-ledger-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.pix_ledger import PixLedger
from app.models.transaction import Transaction
from app.api.v1.routes import pix

LIST_DETAIL = "Lista PIX indisponível no momento."


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


def _seed(db):
    """Espelha o produto: crédito só no ledger; envio grava nas duas tabelas."""
    db.add(PixLedger(
        user_id=1, kind="credit", amount=Decimal("1000.00"),
        description="credito", created_at=datetime(2026, 1, 2, 9, 0, 0),
    ))
    tx = Transaction(
        user_id=1, tipo="saida", valor=100.0, referencia="chave@teste",
        criado_em=datetime(2026, 1, 5, 9, 0, 0),
    )
    db.add(tx)
    db.flush()
    db.add(PixLedger(
        user_id=1, kind="debit", amount=Decimal("100.50"), ref_tx_id=tx.id,
        description="envio", created_at=datetime(2026, 1, 5, 9, 0, 0),
    ))
    # Outro usuário: não pode vazar para o usuário 1.
    db.add(PixLedger(
        user_id=2, kind="credit", amount=Decimal("5000.00"),
        description="outro", created_at=datetime(2026, 1, 3, 9, 0, 0),
    ))
    db.commit()


def _user(uid=1):
    return SimpleNamespace(id=uid)


def _list(db, uid=1, limit=50):
    resp = pix.get_list(limit=limit, current_user=_user(uid), db=db)
    assert resp.status_code == 200
    return json.loads(resp.body)


class _BrokenSession:
    """Sessão falsa: qualquer consulta simula falha de banco."""

    def __init__(self, error):
        self.error = error

    def query(self, *args, **kwargs):
        raise self.error


def test_list_ignores_legacy_transaction_rows(db_session):
    db_session.add(Transaction(
        user_id=1, tipo="entrada", valor=777.0, referencia="legado",
        criado_em=datetime(2026, 1, 4, 9, 0, 0),
    ))
    db_session.commit()

    assert _list(db_session) == []


def test_list_maps_credit_and_debit_newest_first(db_session):
    _seed(db_session)

    items = _list(db_session)

    assert [i["tipo"] for i in items] == ["saida", "entrada"]


def test_list_returns_ledger_amount_date_and_description(db_session):
    _seed(db_session)

    debit, credit = _list(db_session)

    assert set(debit) == {
        "id", "tipo", "valor", "descricao", "taxa_percentual",
        "taxa_valor", "valor_liquido", "created_at",
    }
    assert debit["valor"] == 100.5
    assert debit["valor_liquido"] == 100.5
    assert debit["descricao"] == "envio"
    assert debit["created_at"].startswith("2026-01-05T09:00:00")
    assert credit["valor"] == 1000.0
    assert credit["descricao"] == "credito"
    assert credit["created_at"].startswith("2026-01-02T09:00:00")


def test_list_matches_pix_history(db_session):
    _seed(db_session)

    history = json.loads(
        pix.get_history(current_user=_user(1), db=db_session).body
    )
    items = _list(db_session)

    assert [(i["id"], i["tipo"], i["valor"], i["created_at"]) for i in items] == [
        (h["id"], h["tipo"], h["valor"], h["criado_em"]) for h in history
    ]


def test_list_isolates_user(db_session):
    _seed(db_session)

    other = _list(db_session, uid=2)
    assert [i["descricao"] for i in other] == ["outro"]
    assert _list(db_session, uid=3) == []


@pytest.mark.parametrize("limit,expected", [(1, 1), (100, 100), (500, 100), (0, 50)])
def test_list_limit_clamped(db_session, limit, expected):
    for i in range(105):
        db_session.add(PixLedger(
            user_id=1, kind="credit", amount=Decimal("1.00"),
            created_at=datetime(2026, 1, 1, i // 60, i % 60, 0),
        ))
    db_session.commit()

    items = _list(db_session, limit=limit)

    assert len(items) == expected
    assert items[0]["created_at"].startswith("2026-01-01T01:44:00")


def test_list_db_failure_returns_503():
    original = RuntimeError("falha de banco")

    with pytest.raises(HTTPException) as captured:
        pix.get_list(limit=50, current_user=_user(1), db=_BrokenSession(original))

    assert captured.value.status_code == 503
    assert captured.value.detail == LIST_DETAIL
    assert captured.value.__cause__ is original

"""
GET /api/v1/wallet/balance e /api/v1/wallet/history — fonte de dados.

Antes da correção, as duas rotas liam Transaction usando atributos que o
modelo não possui (kind, amount, description, created_at):
- history lançava AttributeError (HTTP 500) sempre;
- balance lançava AttributeError com linhas em Transaction e retornava
  "0.00" sem elas, divergindo de /pix/balance (PixLedger).

Agora as duas leem PixLedger, a fonte de verdade do saldo, mantendo o
formato de resposta. Chama as funções de rota diretamente com SQLite em
memória.
"""
import os
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "wallet-balance-history-ledger-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.pix_ledger import PixLedger
from app.models.transaction import Transaction
from app.api.v1.routes import pix, wallet


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


def test_balance_matches_ledger_and_pix_balance(db_session):
    _seed(db_session)

    resp = wallet.get_balance(current_user=_user(1), db=db_session)

    assert resp == {"user_id": 1, "balance": "899.50"}
    pix_saldo = pix.get_balance(db=db_session, current_user=_user(1))["saldo"]
    assert Decimal(resp["balance"]) == Decimal(str(pix_saldo))


def test_balance_ignores_legacy_transaction_rows(db_session):
    db_session.add(Transaction(
        user_id=1, tipo="entrada", valor=777.0, referencia="legado",
        criado_em=datetime(2026, 1, 4, 9, 0, 0),
    ))
    db_session.commit()

    resp = wallet.get_balance(current_user=_user(1), db=db_session)

    assert resp == {"user_id": 1, "balance": "0.00"}


def test_history_returns_ledger_entries_newest_first(db_session):
    _seed(db_session)

    resp = wallet.get_history(current_user=_user(1), db=db_session)

    assert resp["user_id"] == 1
    assert [h["kind"] for h in resp["history"]] == ["debit", "credit"]
    first = resp["history"][0]
    assert set(first) == {"id", "kind", "description", "amount", "created_at"}
    assert first["description"] == "envio"
    assert first["amount"] == "100.50"
    assert first["created_at"].startswith("2026-01-05T09:00:00")


def test_history_limited_to_twenty(db_session):
    for i in range(25):
        db_session.add(PixLedger(
            user_id=1, kind="credit", amount=Decimal("1.00"),
            created_at=datetime(2026, 1, 1, 0, i, 0),
        ))
    db_session.commit()

    resp = wallet.get_history(current_user=_user(1), db=db_session)

    assert len(resp["history"]) == 20


def test_balance_and_history_isolate_user(db_session):
    _seed(db_session)

    assert wallet.get_balance(current_user=_user(2), db=db_session) == {
        "user_id": 2, "balance": "5000.00",
    }
    other = wallet.get_history(current_user=_user(2), db=db_session)
    assert [h["description"] for h in other["history"]] == ["outro"]

    empty = wallet.get_history(current_user=_user(3), db=db_session)
    assert empty == {"user_id": 3, "history": []}
    assert wallet.get_balance(current_user=_user(3), db=db_session) == {
        "user_id": 3, "balance": "0.00",
    }

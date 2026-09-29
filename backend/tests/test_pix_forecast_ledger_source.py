"""
GET /api/v1/pix/forecast — fonte de dados (caracterização do A1).

Cenário real do produto:
- créditos existem apenas em pix_ledger (ledger_seed / Asaas);
- send_pix grava Transaction(tipo="saida") + PixLedger(kind="debit").

/pix/balance e /pix/forecast devem ler a mesma fonte: PixLedger.
Antes da correção (A1), o forecast lia Transaction (alias PixTransaction),
ignorava os créditos do ledger e classificava o risco errado.

Estratégia: chamar as funções de rota diretamente com SQLite em memória,
com data fixa (2026-01-10, mês de 31 dias) para o cálculo de projeção.
"""
import json
import os
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "pix-forecast-ledger-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.pix_ledger import PixLedger
from app.models.transaction import Transaction
from app.api.v1.routes import pix

FIXED_NOW = datetime(2026, 1, 10, 12, 0, 0)


class _FixedDatetime(datetime):
    @classmethod
    def utcnow(cls):
        return FIXED_NOW


@pytest.fixture()
def db_session(monkeypatch):
    monkeypatch.setattr(pix, "datetime", _FixedDatetime)
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


def _seed_real_scenario(db):
    """Espelha o produto: crédito só no ledger; envio grava nas duas tabelas."""
    # Crédito inicial (ledger_seed / recebimento): só existe em pix_ledger.
    db.add(PixLedger(
        user_id=1, kind="credit", amount=Decimal("1000.00"),
        description="credito", created_at=datetime(2026, 1, 2, 9, 0, 0),
    ))
    # Envio PIX (pix_service.send_pix): Transaction saida + PixLedger debit.
    tx = Transaction(
        user_id=1, tipo="saida", valor=100.0, referencia="chave@teste",
        criado_em=datetime(2026, 1, 5, 9, 0, 0),
    )
    db.add(tx)
    db.flush()
    db.add(PixLedger(
        user_id=1, kind="debit", amount=Decimal("100.00"), ref_tx_id=tx.id,
        created_at=datetime(2026, 1, 5, 9, 0, 0),
    ))
    # Outro usuário: não pode vazar para o usuário 1.
    db.add(PixLedger(
        user_id=2, kind="credit", amount=Decimal("5000.00"),
        created_at=datetime(2026, 1, 3, 9, 0, 0),
    ))
    db.commit()


def _user(uid=1):
    return SimpleNamespace(id=uid)


def _forecast(db, uid=1):
    resp = pix.get_forecast(db=db, current_user=_user(uid))
    assert resp.status_code == 200
    return json.loads(resp.body)


def _balance(db, uid=1):
    return pix.get_balance(db=db, current_user=_user(uid))["saldo"]


def test_forecast_ignores_legacy_transaction_rows(db_session):
    """Linhas só em Transaction (sem ledger) não entram no forecast."""
    db_session.add(Transaction(
        user_id=1, tipo="entrada", valor=777.0, referencia="legado",
        criado_em=datetime(2026, 1, 4, 9, 0, 0),
    ))
    db_session.commit()

    forecast = _forecast(db_session)

    assert forecast["entradas_mes"] == 0.0
    assert forecast["saidas_mes"] == 0.0
    assert forecast["saldo_atual"] == _balance(db_session) == 0.0


def test_forecast_should_match_ledger_source_of_truth(db_session):
    _seed_real_scenario(db_session)

    forecast = _forecast(db_session)

    assert forecast["saldo_atual"] == _balance(db_session) == 900.0
    assert forecast["entradas_mes"] == 1000.0
    assert forecast["saidas_mes"] == 100.0
    # media 100/10 dias * 31 = 310 -> 1000 - 310 = 690 >= 20% de 1000 -> ok
    assert forecast["previsao_fim_mes"] == pytest.approx(690.0)
    assert forecast["nivel_risco"] == "ok"


def test_forecast_isolates_user(db_session):
    _seed_real_scenario(db_session)

    other = _forecast(db_session, uid=3)

    assert other["saldo_atual"] == 0.0
    assert other["entradas_mes"] == 0.0
    assert other["saidas_mes"] == 0.0

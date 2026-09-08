"""
Regressão: GET /api/v1/pix/balance deve retornar "ultimos_7d" (achado
identificado em test_transactions.py::test_login_and_balance_flow).

Estratégia: testar a lógica de agregação diretamente (sem TestClient, sem
subir a aplicação), usando um banco SQLite isolado, exclusivo deste arquivo
de teste, criado e destruído em memória por teste. Nenhuma rede externa,
nenhum arquivo persistente do repositório é tocado.

A data de referência ("hoje") é sempre obtida dinamicamente via
datetime.date.today() no momento em que a fixture `frozen_today` roda --
nunca uma data literal fixa -- para não depender do relógio real de
Production nem congelar uma data específica no código. A fixture apenas
congela, durante a execução de cada teste, o "hoje" que o próprio módulo
app.api.v1.routes.pix enxerga, eliminando o risco (pequeno, mas real) de
corrida de meia-noite entre o setup do teste e a chamada de date.today()
feita internamente pelo código de produção.
"""
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.api.v1.routes.pix as pix_module
from app.database import Base
from app.models.pix_ledger import PixLedger
from app.api.v1.routes.pix import (
    _empty_ultimos_7d,
    _ultimos_7d_dates,
    _ultimos_7d_from_ledger,
    get_balance,
)


@pytest.fixture()
def frozen_today(monkeypatch):
    """Congela o 'hoje' visto por app.api.v1.routes.pix durante o teste.

    Captura date.today() uma única vez (nunca uma data literal) e substitui
    apenas o símbolo `date` dentro do módulo pix, para que todas as chamadas
    internas de date.today() feitas pelo código de produção retornem
    exatamente o mesmo valor usado para montar os dados do teste. Revertido
    automaticamente pelo pytest ao final do teste.
    """
    today = date.today()

    class FrozenDate(date):
        @classmethod
        def today(cls):
            return today

    monkeypatch.setattr(pix_module, "date", FrozenDate)
    return today


@pytest.fixture()
def db_session():
    # SQLite isolado em memória, criado e descartado a cada teste.
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


def _add_ledger(db, *, user_id, kind, amount, created_at):
    entry = PixLedger(
        user_id=user_id,
        kind=kind,
        amount=amount,
        created_at=created_at,
    )
    db.add(entry)
    db.commit()


def test_ultimos_7d_dates_has_exactly_seven_days_ascending_ending_today(frozen_today):
    dias = _ultimos_7d_dates()

    assert len(dias) == 7
    assert dias == sorted(dias)
    assert dias[-1] == frozen_today
    assert dias[0] == frozen_today - timedelta(days=6)


def test_empty_ultimos_7d_has_seven_zeroed_days_matching_expected_dates(frozen_today):
    empty = _empty_ultimos_7d()
    expected_dates = [d.isoformat() for d in _ultimos_7d_dates()]

    assert isinstance(empty, list)
    assert len(empty) == 7
    assert [item["dia"] for item in empty] == expected_dates
    for item in empty:
        assert item["entradas"] == 0.0
        assert item["saidas"] == 0.0
        assert item["saldo_dia"] == 0.0


def test_ultimos_7d_from_ledger_returns_seven_days_when_user_has_no_entries(db_session, frozen_today):
    result = _ultimos_7d_from_ledger(db_session, user_id=1)

    assert len(result) == 7
    assert [item["dia"] for item in result] == [d.isoformat() for d in _ultimos_7d_dates()]
    for item in result:
        assert item["entradas"] == 0.0
        assert item["saidas"] == 0.0
        assert item["saldo_dia"] == 0.0


def test_ultimos_7d_from_ledger_classifies_credit_and_debit_on_correct_day(db_session, frozen_today):
    hoje = frozen_today
    ontem = hoje - timedelta(days=1)

    _add_ledger(
        db_session,
        user_id=1,
        kind="credit",
        amount=100,
        created_at=datetime.combine(hoje, datetime.min.time()),
    )
    _add_ledger(
        db_session,
        user_id=1,
        kind="debit",
        amount=30,
        created_at=datetime.combine(ontem, datetime.min.time()),
    )

    result = _ultimos_7d_from_ledger(db_session, user_id=1)
    by_day = {item["dia"]: item for item in result}

    assert by_day[hoje.isoformat()]["entradas"] == 100.0
    assert by_day[hoje.isoformat()]["saidas"] == 0.0
    assert by_day[hoje.isoformat()]["saldo_dia"] == 100.0

    assert by_day[ontem.isoformat()]["entradas"] == 0.0
    assert by_day[ontem.isoformat()]["saidas"] == 30.0
    assert by_day[ontem.isoformat()]["saldo_dia"] == -30.0


def test_ultimos_7d_from_ledger_day_without_movement_stays_zeroed(db_session, frozen_today):
    hoje = frozen_today

    _add_ledger(
        db_session,
        user_id=1,
        kind="credit",
        amount=50,
        created_at=datetime.combine(hoje, datetime.min.time()),
    )

    result = _ultimos_7d_from_ledger(db_session, user_id=1)
    by_day = {item["dia"]: item for item in result}

    dia_sem_movimento = (hoje - timedelta(days=3)).isoformat()
    assert by_day[dia_sem_movimento]["entradas"] == 0.0
    assert by_day[dia_sem_movimento]["saidas"] == 0.0
    assert by_day[dia_sem_movimento]["saldo_dia"] == 0.0


def test_ultimos_7d_from_ledger_ignores_entries_from_other_users(db_session, frozen_today):
    hoje = frozen_today

    _add_ledger(
        db_session,
        user_id=1,
        kind="credit",
        amount=100,
        created_at=datetime.combine(hoje, datetime.min.time()),
    )
    _add_ledger(
        db_session,
        user_id=2,
        kind="credit",
        amount=999,
        created_at=datetime.combine(hoje, datetime.min.time()),
    )

    result_user_1 = _ultimos_7d_from_ledger(db_session, user_id=1)
    by_day = {item["dia"]: item for item in result_user_1}

    assert by_day[hoje.isoformat()]["entradas"] == 100.0


def test_ultimos_7d_from_ledger_saldo_dia_equals_entradas_minus_saidas(db_session, frozen_today):
    hoje = frozen_today

    _add_ledger(
        db_session,
        user_id=1,
        kind="credit",
        amount=200,
        created_at=datetime.combine(hoje, datetime.min.time()),
    )
    _add_ledger(
        db_session,
        user_id=1,
        kind="debit",
        amount=80,
        created_at=datetime.combine(hoje, datetime.min.time()),
    )

    result = _ultimos_7d_from_ledger(db_session, user_id=1)
    by_day = {item["dia"]: item for item in result}
    hoje_item = by_day[hoje.isoformat()]

    assert hoje_item["entradas"] == 200.0
    assert hoje_item["saidas"] == 80.0
    assert hoje_item["saldo_dia"] == hoje_item["entradas"] - hoje_item["saidas"]
    assert hoje_item["saldo_dia"] == 120.0


def test_get_balance_returns_saldo_and_source_real_with_ultimos_7d(db_session, frozen_today):
    hoje = frozen_today

    _add_ledger(
        db_session,
        user_id=1,
        kind="credit",
        amount=150,
        created_at=datetime.combine(hoje, datetime.min.time()),
    )
    _add_ledger(
        db_session,
        user_id=1,
        kind="debit",
        amount=20,
        created_at=datetime.combine(hoje, datetime.min.time()),
    )

    response = get_balance(db=db_session, current_user=SimpleNamespace(id=1))

    assert response["saldo"] == 130.0
    assert response["source"] == "real"
    assert isinstance(response["ultimos_7d"], list)
    assert len(response["ultimos_7d"]) == 7
    by_day = {item["dia"]: item for item in response["ultimos_7d"]}
    assert by_day[hoje.isoformat()]["entradas"] == 150.0
    assert by_day[hoje.isoformat()]["saidas"] == 20.0


def test_get_balance_falls_back_to_lab_with_zeroed_ultimos_7d_on_error(db_session, frozen_today):
    # current_user sem atributo "id" força a exceção dentro de get_balance,
    # exercitando deliberadamente o caminho de fallback já existente.
    broken_user = SimpleNamespace()

    response = get_balance(db=db_session, current_user=broken_user)

    assert response["saldo"] == 0.0
    assert response["source"] == "lab"
    assert isinstance(response["ultimos_7d"], list)
    assert len(response["ultimos_7d"]) == 7
    expected_dates = [d.isoformat() for d in _ultimos_7d_dates()]
    assert [item["dia"] for item in response["ultimos_7d"]] == expected_dates
    for item in response["ultimos_7d"]:
        assert item["entradas"] == 0.0
        assert item["saidas"] == 0.0
        assert item["saldo_dia"] == 0.0

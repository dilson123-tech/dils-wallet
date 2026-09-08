"""
M1.1 (Fase 1) — correção da colisão cross-user de Idempotency-Key em
send_pix, com compatibility bridge para coexistência com instâncias
anteriores a esta correção.

Estratégia de teste: SQLite isolado em memória, exclusivo deste arquivo,
sem TestClient, sem tocar o banco real do repositório. Linhas "legadas"
(simulando o comportamento do código anterior a esta correção, que gravava
a Idempotency-Key crua diretamente) são inseridas manualmente nos testes
que precisam delas, sem depender de nenhuma versão antiga real do código.

Sobre concorrência real (múltiplas conexões/threads simultâneas): NÃO
implementada neste arquivo. SQLite (especialmente em memória) não oferece
um modelo de concorrência representativo do PostgreSQL usado em produção
para esse tipo de teste (single-writer, sem MVCC real entre conexões),
e forçar um teste de threads contra SQLite tende a ser instável/pouco
confiável. Os testes abaixo validam deterministicamente o mecanismo
INSERT + flush + UNIQUE + IntegrityError (que é o que de fato resolve a
concorrência em produção), exercitando-o em sequência controlada. Validação
de concorrência real fica registrada como follow-up contra PostgreSQL.
"""
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.idempotency import IdempotencyKey
from app.models.pix_ledger import PixLedger
from app.models.transaction import Transaction
from app.services.pix_service import (
    PIX_SEND_IDEMPOTENCY_KEY_MAX_LENGTH,
    PIX_SEND_SCOPED_KEY_PREFIX,
    _idem_hash,
    _pix_send_scoped_key,
    _round_money,
    send_pix,
)
from decimal import Decimal


def _expected_hash(*, user_id, valor, chave_pix, descricao):
    """Replica exatamente o arredondamento que send_pix aplica a `valor`
    antes de calcular o hash, para que o request_hash de uma linha
    legada seedada em teste seja diretamente comparável ao que send_pix
    recalcula internamente."""
    return _idem_hash(
        user_id=user_id,
        valor=_round_money(Decimal(valor)),
        chave_pix=chave_pix,
        descricao=descricao,
    )


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


def _fund(db, *, user_id, amount):
    db.add(PixLedger(user_id=user_id, kind="credit", amount=amount))
    db.commit()


def _seed_legacy_raw(
    db,
    *,
    key,
    request_hash=None,
    response_json=None,
):
    row = IdempotencyKey(key=key, request_hash=request_hash, response_json=response_json)
    db.add(row)
    db.commit()
    return row


def _seed_completed_transaction(db, *, user_id, valor):
    tx = Transaction(user_id=user_id, tipo="saida", valor=float(valor), referencia="dest@legacy")
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def _legacy_response_payload(tx, *, valor):
    return json.dumps({
        "id": tx.id,
        "valor": str(valor),
        "taxa_percentual": "0.0000",
        "taxa_valor": "0.00",
        "valor_liquido": str(valor),
        "status": "success",
    })


def _count(db, model):
    return db.query(model).count()


# --- 1-4: fluxo novo (sem legado envolvido) ---------------------------------


def test_new_user_key_payload_processes_once(db_session):
    _fund(db_session, user_id=1, amount=100)

    result = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-new-1",
    )

    assert isinstance(result, Transaction)
    assert _count(db_session, Transaction) == 1
    assert _count(db_session, PixLedger) == 2  # crédito de fundo + débito
    assert _count(db_session, IdempotencyKey) == 2  # raw bridge + scoped


def test_new_user_key_payload_retry_replays_without_second_debit(db_session):
    _fund(db_session, user_id=1, amount=100)

    first = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-retry-1",
    )
    second = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-retry-1",
    )

    assert isinstance(second, dict)
    assert second["id"] == first.id
    assert _count(db_session, Transaction) == 1


def test_new_user_key_different_payload_conflicts(db_session):
    _fund(db_session, user_id=1, amount=100)

    send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-conflict-1",
    )
    result = send_pix(
        db_session, user_id=1, valor=20, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-conflict-1",
    )

    assert result["code"] == "IDEMPOTENCY_KEY_REUSE_DIFFERENT_PAYLOAD"
    assert _count(db_session, Transaction) == 1


def test_two_users_same_key_process_independently(db_session):
    _fund(db_session, user_id=1, amount=100)
    _fund(db_session, user_id=2, amount=100)

    result_a = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-shared",
    )
    result_b = send_pix(
        db_session, user_id=2, valor=15, chave_pix="dest@b", descricao="PIX",
        idempotency_key="K-shared",
    )

    assert isinstance(result_a, Transaction)
    assert isinstance(result_b, Transaction)
    assert result_a.id != result_b.id
    assert _count(db_session, Transaction) == 2

    scoped_a = _pix_send_scoped_key(1, "K-shared")
    scoped_b = _pix_send_scoped_key(2, "K-shared")
    assert db_session.query(IdempotencyKey).filter_by(key=scoped_a).first() is not None
    assert db_session.query(IdempotencyKey).filter_by(key=scoped_b).first() is not None


# --- 5-7: ownership de legado (raw bridge pré-existente) --------------------


def test_legacy_raw_completed_of_a_retry_exact_a_replays(db_session):
    valor = 10
    tx = _seed_completed_transaction(db_session, user_id=1, valor=valor)
    req_hash = _expected_hash(user_id=1, valor=valor, chave_pix="dest@legacy", descricao="PIX")
    _seed_legacy_raw(
        db_session,
        key="K-legacy-1",
        request_hash=req_hash,
        response_json=_legacy_response_payload(tx, valor=valor),
    )

    result = send_pix(
        db_session, user_id=1, valor=valor, chave_pix="dest@legacy", descricao="PIX",
        idempotency_key="K-legacy-1",
    )

    assert isinstance(result, dict)
    assert result["id"] == tx.id
    assert _count(db_session, Transaction) == 1  # nenhuma nova transação


def test_legacy_raw_completed_of_a_different_payload_conflicts(db_session):
    valor = 10
    tx = _seed_completed_transaction(db_session, user_id=1, valor=valor)
    req_hash = _expected_hash(user_id=1, valor=valor, chave_pix="dest@legacy", descricao="PIX")
    _seed_legacy_raw(
        db_session,
        key="K-legacy-2",
        request_hash=req_hash,
        response_json=_legacy_response_payload(tx, valor=valor),
    )

    result = send_pix(
        db_session, user_id=1, valor=999, chave_pix="dest@legacy", descricao="PIX",
        idempotency_key="K-legacy-2",
    )

    assert result["code"] == "IDEMPOTENCY_KEY_REUSE_DIFFERENT_PAYLOAD"
    assert _count(db_session, Transaction) == 1


def test_legacy_raw_completed_of_a_used_by_b_processes_via_scoped(db_session):
    valor = 10
    tx_a = _seed_completed_transaction(db_session, user_id=1, valor=valor)
    req_hash_a = _expected_hash(user_id=1, valor=valor, chave_pix="dest@legacy", descricao="PIX")
    _seed_legacy_raw(
        db_session,
        key="K-legacy-3",
        request_hash=req_hash_a,
        response_json=_legacy_response_payload(tx_a, valor=valor),
    )
    _fund(db_session, user_id=2, amount=100)

    result_b = send_pix(
        db_session, user_id=2, valor=20, chave_pix="dest@b", descricao="PIX",
        idempotency_key="K-legacy-3",
    )

    assert isinstance(result_b, Transaction)
    assert result_b.user_id == 2
    assert result_b.id != tx_a.id
    assert _count(db_session, Transaction) == 2

    raw_row = db_session.query(IdempotencyKey).filter_by(key="K-legacy-3").first()
    assert json.loads(raw_row.response_json)["id"] == tx_a.id  # linha de A intocada
    assert raw_row.request_hash == req_hash_a  # request_hash de A preservado

    scoped_b = _pix_send_scoped_key(2, "K-legacy-3")
    scoped_row_b = db_session.query(IdempotencyKey).filter_by(key=scoped_b).first()
    assert scoped_row_b is not None
    assert json.loads(scoped_row_b.response_json)["id"] == result_b.id


# --- 8-12: legado indeterminado -> fail-closed ------------------------------


def test_legacy_raw_in_progress_returns_in_progress_no_debit(db_session):
    _seed_legacy_raw(db_session, key="K-inprogress", request_hash="deadbeef", response_json=None)

    result = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-inprogress",
    )

    assert result["code"] == "IDEMPOTENCY_IN_PROGRESS"
    assert _count(db_session, Transaction) == 0


def test_legacy_raw_malformed_json_fails_closed(db_session):
    _seed_legacy_raw(db_session, key="K-malformed", request_hash="deadbeef", response_json="{not-json")

    result = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-malformed",
    )

    assert result["code"] == "IDEMPOTENCY_IN_PROGRESS"
    assert _count(db_session, Transaction) == 0


def test_legacy_raw_missing_id_fails_closed(db_session):
    incomplete = json.dumps({
        "valor": "10", "taxa_percentual": "0", "taxa_valor": "0",
        "valor_liquido": "10", "status": "success",
    })
    _seed_legacy_raw(db_session, key="K-noid", request_hash="deadbeef", response_json=incomplete)

    result = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-noid",
    )

    assert result["code"] == "IDEMPOTENCY_IN_PROGRESS"
    assert _count(db_session, Transaction) == 0


def test_legacy_raw_nonexistent_transaction_id_fails_closed(db_session):
    fake_response = json.dumps({
        "id": 999999, "valor": "10", "taxa_percentual": "0", "taxa_valor": "0",
        "valor_liquido": "10", "status": "success",
    })
    _seed_legacy_raw(db_session, key="K-ghost", request_hash="deadbeef", response_json=fake_response)

    result = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-ghost",
    )

    assert result["code"] == "IDEMPOTENCY_IN_PROGRESS"
    assert _count(db_session, Transaction) == 0


def test_legacy_raw_unrelated_purpose_never_replayed_as_pix_send(db_session):
    # Formato de uma linha de OUTRO fluxo (correlação de pagamento Asaas),
    # que compartilha a mesma tabela idempotency_keys, mas não é uma
    # resposta de send_pix.
    other_flow_payload = json.dumps({
        "contract": "asaas_payment_user_correlation_v1",
        "provider": "asaas",
        "user_id": 5,
        "correlation_status": "registered",
    })
    _seed_legacy_raw(
        db_session,
        key="K-other-flow",
        request_hash="deadbeef",
        response_json=other_flow_payload,
    )

    result = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-other-flow",
    )

    assert result["code"] == "IDEMPOTENCY_IN_PROGRESS"
    assert _count(db_session, Transaction) == 0


# --- 13-14: limite de comprimento -------------------------------------------


def test_raw_key_exactly_128_chars_accepted(db_session):
    _fund(db_session, user_id=1, amount=100)
    key = "K" * PIX_SEND_IDEMPOTENCY_KEY_MAX_LENGTH
    assert len(key) == 128

    result = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key=key,
    )

    assert isinstance(result, Transaction)


def test_raw_key_129_chars_rejected_before_insert(db_session):
    _fund(db_session, user_id=1, amount=100)
    key = "K" * (PIX_SEND_IDEMPOTENCY_KEY_MAX_LENGTH + 1)

    with pytest.raises(ValueError):
        send_pix(
            db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
            idempotency_key=key,
        )

    assert _count(db_session, IdempotencyKey) == 0
    assert _count(db_session, Transaction) == 0


# --- 15: propriedades da scoped_key -----------------------------------------


def test_scoped_key_helper_properties():
    key_a = _pix_send_scoped_key(1, "same-raw")
    key_a_again = _pix_send_scoped_key(1, "same-raw")
    key_b = _pix_send_scoped_key(2, "same-raw")

    assert key_a.startswith(PIX_SEND_SCOPED_KEY_PREFIX)
    assert len(key_a) == 73
    assert key_a == key_a_again
    assert key_a != key_b


# --- 16: atomicidade raw + scoped ------------------------------------------


def test_bridge_creates_both_raw_and_scoped_rows_pointing_to_same_transaction(db_session):
    _fund(db_session, user_id=1, amount=100)

    result = send_pix(
        db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
        idempotency_key="K-bridge-atomic",
    )

    raw_row = db_session.query(IdempotencyKey).filter_by(key="K-bridge-atomic").first()
    scoped_key = _pix_send_scoped_key(1, "K-bridge-atomic")
    scoped_row = db_session.query(IdempotencyKey).filter_by(key=scoped_key).first()

    assert raw_row is not None and scoped_row is not None
    assert json.loads(raw_row.response_json)["id"] == result.id
    assert json.loads(scoped_row.response_json)["id"] == result.id
    assert raw_row.request_hash == scoped_row.request_hash


# --- 17: falha antes do commit não deixa linhas órfãs -----------------------


def test_operational_failure_before_commit_leaves_no_orphaned_rows(db_session):
    # Usuário sem saldo -> ValueError("Saldo insuficiente") é levantado
    # DEPOIS de raw bridge + scoped key já terem sido flush()ados, mas
    # ANTES do commit final.
    with pytest.raises(ValueError):
        send_pix(
            db_session, user_id=1, valor=10, chave_pix="dest@a", descricao="PIX",
            idempotency_key="K-fails-before-commit",
        )

    # Simula o teardown de sessão do FastAPI (get_db fecha a sessão sem
    # commit explícito), que descarta a transação pendente.
    db_session.rollback()

    assert _count(db_session, IdempotencyKey) == 0
    assert _count(db_session, Transaction) == 0

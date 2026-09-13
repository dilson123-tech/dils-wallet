"""
M2 — testes funcionais da autoridade server-side da intent de envio PIX
(backend/app/services/pix_send_intent_service.py).

Estratégia: SQLite isolado em memória, mesmo padrão de
test_pix_send_idempotency_scope.py. Concorrência real (threads/PostgreSQL)
fica em test_pix_send_intent_concurrency_postgres.py, seguindo o mesmo
padrão de test_pix_send_concurrency_postgres.py.

Cobre: criação, reuso enquanto pending, isolamento entre usuários e entre
payloads distintos, bloqueio de renovação silenciosa (acknowledged sem
force_new, e force_new enquanto ainda pending), renovação explícita
autorizada, ack fail-closed (sem PIX concluído) e idempotente, e o
cenário completo de resposta perdida + replay sem segundo débito.
"""
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.pix_ledger import PixLedger
from app.services.pix_send_intent_service import (
    PixSendIntentAckError,
    acknowledge_pix_send_intent,
    reserve_pix_send_intent,
)
from app.services.pix_service import send_pix


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


def _reserve(db, user_id=1, valor="50.00", chave_pix="dest@aurea.gold", descricao="PIX", force_new=False):
    return reserve_pix_send_intent(
        db,
        user_id=user_id,
        valor=Decimal(valor),
        chave_pix=chave_pix,
        descricao=descricao,
        force_new=force_new,
    )


# 1. Primeira reserva cria K1.
def test_first_reservation_creates_k1(db_session):
    result = _reserve(db_session)

    assert result["state"] == "pending"
    assert result["send_key"]
    assert result["generation"] == 1
    assert result["reused"] is False
    assert result["can_send"] is True
    assert result["requires_explicit_new"] is False


# 2. Segunda reserva igual pending retorna K1.
def test_second_identical_reservation_returns_same_k1(db_session):
    first = _reserve(db_session)
    second = _reserve(db_session)

    assert second["send_key"] == first["send_key"]
    assert second["reused"] is True
    assert second["generation"] == 1


# 3. Usuários diferentes ficam isolados.
def test_different_users_get_isolated_intents(db_session):
    user_a = _reserve(db_session, user_id=1)
    user_b = _reserve(db_session, user_id=2)

    assert user_a["send_key"] != user_b["send_key"]


# 4. Payload diferente gera intent diferente.
def test_different_payload_generates_different_intent(db_session):
    base = _reserve(db_session, valor="50.00")
    different_dest = _reserve(db_session, chave_pix="outro@aurea.gold")
    different_valor = _reserve(db_session, valor="51.00")
    different_desc = _reserve(db_session, descricao="Aluguel")

    keys = {base["send_key"], different_dest["send_key"], different_valor["send_key"], different_desc["send_key"]}
    assert len(keys) == 4


# 5/6/7/8. acknowledged + force_new — não cria K2 sem flag, cria com flag,
# K2 != K1, generation incrementa.
def test_force_new_only_creates_k2_after_acknowledged(db_session):
    _fund(db_session, user_id=1, amount=Decimal("1000.00"))

    reserved = _reserve(db_session)
    k1 = reserved["send_key"]

    send_pix(
        db_session,
        user_id=1,
        valor=Decimal("50.00"),
        chave_pix="dest@aurea.gold",
        descricao="PIX",
        idempotency_key=k1,
    )
    ack = acknowledge_pix_send_intent(db_session, user_id=1, send_key=k1)
    assert ack["state"] == "acknowledged"

    # 5) acknowledged + force_new=false NÃO cria K2.
    no_force = _reserve(db_session, force_new=False)
    assert no_force["state"] == "acknowledged"
    assert no_force["can_send"] is False
    assert no_force["requires_explicit_new"] is True
    assert no_force["send_key"] is None

    # 6/7/8) acknowledged + force_new=true cria K2, K2 != K1, generation=2.
    forced = _reserve(db_session, force_new=True)
    assert forced["state"] == "pending"
    assert forced["can_send"] is True
    assert forced["send_key"] is not None
    assert forced["send_key"] != k1
    assert forced["generation"] == 2


# 9. force_new enquanto pending não substitui K1.
def test_force_new_while_pending_is_rejected(db_session):
    reserved = _reserve(db_session)
    k1 = reserved["send_key"]

    attempt = _reserve(db_session, force_new=True)

    assert attempt["send_key"] == k1
    assert attempt["state"] == "pending"
    assert attempt.get("force_new_rejected") is True


# 10. ack sem PIX concluído rejeitado.
def test_ack_without_completed_pix_is_rejected(db_session):
    reserved = _reserve(db_session)

    with pytest.raises(PixSendIntentAckError):
        acknowledge_pix_send_intent(db_session, user_id=1, send_key=reserved["send_key"])


# 11. ack após PIX realmente concluído funciona.
def test_ack_after_real_completion_succeeds(db_session):
    _fund(db_session, user_id=1, amount=Decimal("1000.00"))
    reserved = _reserve(db_session)
    k1 = reserved["send_key"]

    send_pix(
        db_session,
        user_id=1,
        valor=Decimal("50.00"),
        chave_pix="dest@aurea.gold",
        descricao="PIX",
        idempotency_key=k1,
    )

    ack = acknowledge_pix_send_intent(db_session, user_id=1, send_key=k1)
    assert ack["state"] == "acknowledged"
    assert ack["reused"] is False


# Item crítico: ack deve rejeitar quando o PIX concluído com a send_key da
# intent tem um request_hash DIFERENTE do fingerprint_hash da intent (ou
# seja, send_pix foi chamado com K1 mas um payload diferente do reservado).
def test_ack_rejects_when_completed_pix_payload_differs_from_intent(db_session):
    _fund(db_session, user_id=1, amount=Decimal("1000.00"))

    reserved = _reserve(db_session, valor="50.00", chave_pix="dest@aurea.gold", descricao="PIX")
    k1 = reserved["send_key"]

    # send_pix aceita K1 normalmente pelas SUAS próprias regras (primeira
    # vez que essa raw key é usada) — mas com um payload B diferente do
    # que a intent A reservou.
    tx_b = send_pix(
        db_session,
        user_id=1,
        valor=Decimal("999.00"),
        chave_pix="outro-destino@aurea.gold",
        descricao="Pagamento completamente diferente",
        idempotency_key=k1,
    )
    assert tx_b is not None

    with pytest.raises(PixSendIntentAckError):
        acknowledge_pix_send_intent(db_session, user_id=1, send_key=k1)

    # Intent A permanece pending, mesma generation — nenhum efeito.
    intent_a = _reserve(db_session, valor="50.00", chave_pix="dest@aurea.gold", descricao="PIX")
    assert intent_a["state"] == "pending"
    assert intent_a["send_key"] == k1
    assert intent_a["generation"] == 1


# 12. ack repetido é idempotente.
def test_ack_is_idempotent(db_session):
    _fund(db_session, user_id=1, amount=Decimal("1000.00"))
    reserved = _reserve(db_session)
    k1 = reserved["send_key"]

    send_pix(
        db_session,
        user_id=1,
        valor=Decimal("50.00"),
        chave_pix="dest@aurea.gold",
        descricao="PIX",
        idempotency_key=k1,
    )

    first_ack = acknowledge_pix_send_intent(db_session, user_id=1, send_key=k1)
    second_ack = acknowledge_pix_send_intent(db_session, user_id=1, send_key=k1)

    assert first_ack["state"] == second_ack["state"] == "acknowledged"
    assert second_ack["reused"] is True


# 13. Resposta perdida / replay: reload+retry reusa K1, sem segundo débito.
def test_lost_response_reload_retry_replays_without_double_debit(db_session):
    _fund(db_session, user_id=1, amount=Decimal("1000.00"))

    first_reserve = _reserve(db_session)
    k1 = first_reserve["send_key"]

    tx1 = send_pix(
        db_session,
        user_id=1,
        valor=Decimal("50.00"),
        chave_pix="dest@aurea.gold",
        descricao="PIX",
        idempotency_key=k1,
    )

    # "resposta se perde" — nada a fazer no teste, simplesmente o cliente
    # nunca chamou ack() e a página "recarregou": reserve() é chamado de
    # novo, sem nenhum estado em memória.
    reload_reserve = _reserve(db_session)
    assert reload_reserve["send_key"] == k1
    assert reload_reserve["state"] == "pending"

    # retry com a MESMA key → replay do backend, não um novo débito.
    replay = send_pix(
        db_session,
        user_id=1,
        valor=Decimal("50.00"),
        chave_pix="dest@aurea.gold",
        descricao="PIX",
        idempotency_key=k1,
    )
    # replay é o dict já persistido (response_json), não uma nova Transaction.
    assert isinstance(replay, dict)
    assert replay["id"] == tx1.id  # mesma transação, não uma nova

    balance_after = (
        db_session.query(PixLedger)
        .filter(PixLedger.user_id == 1, PixLedger.kind == "debit")
        .count()
    )
    assert balance_after == 1  # exatamente um débito, nunca dois

    ack = acknowledge_pix_send_intent(db_session, user_id=1, send_key=k1)
    assert ack["state"] == "acknowledged"

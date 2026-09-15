"""
Testes do soft cap operacional de cardinalidade por namespace sandbox
(P0-B) -- WALLET_SANDBOX_NAMESPACE_MAX_ROWS (app/config.py) e
enforce_sandbox_namespace_cap (app/services/sandbox_namespace_cap.py).

Cobre aqui, com um banco SQLite real (não os FakeDb usados nos testes
de endpoint), porque estes cenários dependem do filtro real por
prefixo (key.like(...)) e da contagem real via COUNT, que os FakeDb
existentes nos outros arquivos de teste não reproduzem com fidelidade:

- parsing fail-closed da env var;
- isolamento entre os 3 namespaces sandbox;
- prova de que pix-send: e o bridge raw/legado nunca são contados nem
  tocados (segurança real-money);
- boundary exato (count == limite aceita; limite+1 rejeita).

Os cenários de integração ponta a ponta (B/E/F: replay preservado,
503 + Retry-After, zero inserção líquida na rejeição) estão nos
arquivos de teste já existentes de cada endpoint
(test_wallet_sandbox_end_to_end_statement.py,
test_wallet_asaas_correlated_pix_payment_preparation_endpoint.py,
test_asaas_webhook_receiver.py), reaproveitando o padrão FakeDb já
estabelecido neles.

Nenhum acesso a Asaas/Railway/Production. Nenhum dinheiro real.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.idempotency import IdempotencyKey
from app.services import sandbox_namespace_cap as cap_module
from app.services.sandbox_namespace_cap import (
    SandboxNamespaceCapExceeded,
    enforce_sandbox_namespace_cap,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _insert_key(session, key: str) -> None:
    session.add(IdempotencyKey(key=key, request_hash="h" * 64))
    session.flush()


# ---------------------------------------------------------------------
# A) Parsing fail-closed de WALLET_SANDBOX_NAMESPACE_MAX_ROWS.
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw_value, expected",
    [
        (None, 5000),
        ("500", 500),
        ("5000", 5000),
        ("100000", 100000),
        ("not-an-integer", 5000),
        ("0", 5000),
        ("-1", 5000),
        ("499", 5000),
        ("100001", 5000),
    ],
)
def test_parse_wallet_sandbox_namespace_max_rows_is_fail_closed(
    monkeypatch, raw_value, expected
):
    if raw_value is None:
        monkeypatch.delenv("WALLET_SANDBOX_NAMESPACE_MAX_ROWS", raising=False)
    else:
        monkeypatch.setenv("WALLET_SANDBOX_NAMESPACE_MAX_ROWS", raw_value)

    from app.config import _parse_wallet_sandbox_namespace_max_rows

    assert _parse_wallet_sandbox_namespace_max_rows() == expected


# ---------------------------------------------------------------------
# G) Boundary exato.
# ---------------------------------------------------------------------
def test_enforce_cap_accepts_exactly_at_limit_and_rejects_one_above(
    monkeypatch, db_session
):
    monkeypatch.setattr(cap_module, "WALLET_SANDBOX_NAMESPACE_MAX_ROWS", 3)

    for i in range(3):
        _insert_key(db_session, f"wallet-sandbox-webhook:row-{i}")

    # count == limite (3) -> aceita, não levanta.
    enforce_sandbox_namespace_cap(
        db_session, namespace_prefix="wallet-sandbox-webhook:"
    )

    _insert_key(db_session, "wallet-sandbox-webhook:row-3")

    # count == limite+1 (4) -> rejeita.
    with pytest.raises(SandboxNamespaceCapExceeded):
        enforce_sandbox_namespace_cap(
            db_session, namespace_prefix="wallet-sandbox-webhook:"
        )


# ---------------------------------------------------------------------
# E) Isolamento entre namespaces.
# ---------------------------------------------------------------------
def test_enforce_cap_is_isolated_per_namespace(monkeypatch, db_session):
    monkeypatch.setattr(cap_module, "WALLET_SANDBOX_NAMESPACE_MAX_ROWS", 2)

    for i in range(5):
        _insert_key(db_session, f"wallet-sandbox-webhook:row-{i}")

    with pytest.raises(SandboxNamespaceCapExceeded):
        enforce_sandbox_namespace_cap(
            db_session, namespace_prefix="wallet-sandbox-webhook:"
        )

    # asaas-payment-correlation: continua livre, mesmo com o namespace
    # acima completamente esgotado.
    _insert_key(db_session, "asaas-payment-correlation:row-0")
    enforce_sandbox_namespace_cap(
        db_session, namespace_prefix="asaas-payment-correlation:"
    )

    # asaas-sandbox-webhook: também continua livre.
    _insert_key(db_session, "asaas-sandbox-webhook:row-0")
    enforce_sandbox_namespace_cap(
        db_session, namespace_prefix="asaas-sandbox-webhook:"
    )


# ---------------------------------------------------------------------
# F) Segurança real-money: pix-send: e o bridge raw/legado nunca são
# contados nem tocados pelo cap sandbox.
# ---------------------------------------------------------------------
def test_enforce_cap_never_counts_or_touches_pix_send_or_raw_bridge(
    monkeypatch, db_session
):
    monkeypatch.setattr(cap_module, "WALLET_SANDBOX_NAMESPACE_MAX_ROWS", 1)

    for i in range(10):
        _insert_key(db_session, f"pix-send:{'a' * 55}{i:02d}")

    for i in range(10):
        _insert_key(db_session, f"raw-legacy-key-without-prefix-{i:02d}")

    # o namespace sandbox continua vazio (0 <= limite 1) -> aceito,
    # mesmo com 20 linhas de pix-send:/raw já na tabela compartilhada.
    enforce_sandbox_namespace_cap(
        db_session, namespace_prefix="wallet-sandbox-webhook:"
    )

    # as 20 linhas de pix-send:/raw continuam intactas -- nunca
    # tocadas/deletadas pelo cap sandbox.
    assert db_session.query(IdempotencyKey).count() == 20

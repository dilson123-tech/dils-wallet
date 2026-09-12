from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from . import Base


class PixSendIntent(Base):
    """
    Autoridade server-side da intenção de envio PIX (M2 — persistência real
    de retry, sobrevive a reload/fechar app/outro dispositivo/outra aba).

    Uma linha representa "a intenção atual de enviar exatamente este PIX
    (mesmo usuário, mesmo destino, mesmo valor, mesma descrição)" — não a
    própria transação financeira, que continua vivendo em `Transaction`/
    `PixLedger`/`idempotency_keys` (namespace `pix-send:`), sem nenhuma
    mudança de semântica ali.

    `state`:
      - "pending": send_key ativo, ainda não confirmado como concluído.
      - "acknowledged": o PIX desta geração foi confirmado concluído
        (verificado server-side contra `idempotency_keys`, nunca por
        alegação do cliente) — fingerprint livre para uma nova geração
        somente mediante force_new=true explícito.

    `generation` começa em 1 e só é incrementado quando uma nova geração é
    explicitamente autorizada (acknowledged + force_new=true) — nunca por
    TTL/heurística de tempo.
    """

    __tablename__ = "pix_send_intents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # sha256(user_id|valor_canonico|chave_pix|descricao) — mesma fórmula
    # (pix_send_request_hash) usada pelo request_hash de idempotency_keys,
    # para nunca haver uma segunda definição do que é "o mesmo PIX".
    fingerprint_hash = Column(String(64), nullable=False)

    # UUID aleatório enviado como header Idempotency-Key ao POST /pix/send.
    send_key = Column(String(64), nullable=False, unique=True, index=True)

    state = Column(String(16), nullable=False, default="pending")
    generation = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", backref="pix_send_intents")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "fingerprint_hash",
            name="uq_pix_send_intents_user_fingerprint",
        ),
        CheckConstraint(
            "state in ('pending', 'acknowledged')",
            name="ck_pix_send_intents_state",
        ),
    )

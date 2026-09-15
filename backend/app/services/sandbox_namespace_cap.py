"""
Soft cap operacional de cardinalidade por namespace sandbox na tabela
compartilhada idempotency_keys (P0-B).

NÃO é TTL, NÃO é retenção, NÃO é capacidade derivada de negócio -- é
um limite de segurança operacional configurável via
WALLET_SANDBOX_NAMESPACE_MAX_ROWS (app/config.py), aplicado de forma
independente a cada um dos namespaces sandbox:

    wallet-sandbox-webhook:
    asaas-payment-correlation:
    asaas-sandbox-webhook:

Nunca conta nem toca pix-send: nem o bridge raw/legado sem prefixo --
o filtro é estritamente pelo prefixo do namespace informado.

Soft cap, não hard cap: sob concorrência real (PostgreSQL READ
COMMITTED), múltiplas transações podem observar a contagem abaixo do
limite antes de qualquer commit concorrente e todas inserir -- o
overshoot é limitado pela concorrência ativa (hoje já bounded pelos
rate limits por IP dos endpoints sandbox), nunca eliminado. Nenhuma
garantia matemática de teto rígido é feita.

Só deve ser chamado DEPOIS de um db.flush() bem-sucedido que já
comprovou que a chave é genuinamente NOVA (nunca antes de saber se é
replay) -- a própria linha recém-flushed já está visível nesta mesma
Session/transação e é contada.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import WALLET_SANDBOX_NAMESPACE_MAX_ROWS
from app.models.idempotency import IdempotencyKey


class SandboxNamespaceCapExceeded(Exception):
    """
    Levantada quando o namespace sandbox informado já ultrapassou o
    soft cap operacional no momento em que uma chave nova acabou de
    ser inserida (flush) nesta Session. O chamador é responsável por
    fazer db.rollback() e mapear para a resposta de indisponibilidade
    apropriada -- esta exceção nunca deve vazar como resposta HTTP
    diretamente.
    """


def enforce_sandbox_namespace_cap(
    db: Session, *, namespace_prefix: str
) -> None:
    count = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.key.like(f"{namespace_prefix}%"))
        .count()
    )

    if count > WALLET_SANDBOX_NAMESPACE_MAX_ROWS:
        raise SandboxNamespaceCapExceeded(namespace_prefix)

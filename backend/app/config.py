import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-override-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# demo = modo atual/lab, sem dinheiro real
# partner = futuro modo com parceiro financeiro/PSP/BaaS
_wallet_mode_raw = os.getenv("WALLET_MODE", "demo").strip().lower()
WALLET_MODE = _wallet_mode_raw if _wallet_mode_raw in {"demo", "partner"} else "demo"

_wallet_partner_provider_raw = (
    os.getenv("WALLET_PARTNER_PROVIDER")
    or os.getenv("WALLET_PROVIDER")
    or "demo"
)
WALLET_PARTNER_PROVIDER = _wallet_partner_provider_raw.strip().lower()
_IS_SANDBOX_PROVIDER = WALLET_PARTNER_PROVIDER in {"sandbox", "partner-sandbox", "sandbox_partner"}
IS_SANDBOX_PARTNER = WALLET_MODE == "partner" and _IS_SANDBOX_PROVIDER

IS_DEMO_WALLET = WALLET_MODE == "demo"
IS_PARTNER_WALLET = WALLET_MODE == "partner" and not IS_SANDBOX_PARTNER

# Limite operacional de segurança (soft cap) de cardinalidade por
# namespace sandbox na tabela compartilhada idempotency_keys (P0-B).
# NÃO é TTL, NÃO é período de retenção, NÃO é capacidade derivada de
# negócio -- é só um teto de segurança configurável. Parsing
# fail-closed: qualquer valor ausente, não-inteiro, <=0, abaixo do
# mínimo ou acima do máximo NUNCA desabilita a proteção -- sempre cai
# no default seguro, nunca significa "ilimitado".
_WALLET_SANDBOX_NAMESPACE_MAX_ROWS_DEFAULT = 5000
_WALLET_SANDBOX_NAMESPACE_MAX_ROWS_MIN = 500
_WALLET_SANDBOX_NAMESPACE_MAX_ROWS_MAX = 100000


def _parse_wallet_sandbox_namespace_max_rows() -> int:
    raw = os.getenv("WALLET_SANDBOX_NAMESPACE_MAX_ROWS")
    if raw is None:
        return _WALLET_SANDBOX_NAMESPACE_MAX_ROWS_DEFAULT

    try:
        value = int(raw.strip())
    except (TypeError, ValueError):
        return _WALLET_SANDBOX_NAMESPACE_MAX_ROWS_DEFAULT

    if value < _WALLET_SANDBOX_NAMESPACE_MAX_ROWS_MIN:
        return _WALLET_SANDBOX_NAMESPACE_MAX_ROWS_DEFAULT

    if value > _WALLET_SANDBOX_NAMESPACE_MAX_ROWS_MAX:
        return _WALLET_SANDBOX_NAMESPACE_MAX_ROWS_DEFAULT

    return value


WALLET_SANDBOX_NAMESPACE_MAX_ROWS = _parse_wallet_sandbox_namespace_max_rows()


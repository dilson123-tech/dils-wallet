from __future__ import annotations

from functools import lru_cache

from app.config import IS_SANDBOX_PARTNER, WALLET_MODE, WALLET_PARTNER_PROVIDER
from app.partner.base import PartnerAdapter
from app.partner.demo_adapter import DemoPartnerAdapter
from app.partner.sandbox_adapter import SandboxPartnerAdapter


@lru_cache(maxsize=1)
def get_partner_adapter() -> PartnerAdapter:
    """
    Resolve o adapter financeiro ativo.

    Hoje:
    - demo: adapter local, sem dinheiro real.
    - sandbox: adapter técnico controlado, sem dinheiro real.

    Futuro:
    - partner: adapter real do PSP/BaaS escolhido e homologado.
    """
    if IS_SANDBOX_PARTNER:
        return SandboxPartnerAdapter()

    if WALLET_MODE == "demo":
        return DemoPartnerAdapter()

    raise RuntimeError(
        "WALLET_MODE=partner configurado, mas nenhum Partner Adapter real foi registrado "
        f"para WALLET_PARTNER_PROVIDER={WALLET_PARTNER_PROVIDER!r}."
    )

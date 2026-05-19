from __future__ import annotations

from functools import lru_cache

from app.config import WALLET_MODE
from app.partner.base import PartnerAdapter
from app.partner.demo_adapter import DemoPartnerAdapter


@lru_cache(maxsize=1)
def get_partner_adapter() -> PartnerAdapter:
    """
    Resolve o adapter financeiro ativo.

    Hoje:
    - demo: adapter local, sem dinheiro real.

    Futuro:
    - partner: adapter real do PSP/BaaS escolhido.
    """
    if WALLET_MODE == "demo":
        return DemoPartnerAdapter()

    raise RuntimeError(
        "WALLET_MODE=partner configurado, mas nenhum Partner Adapter real foi registrado."
    )

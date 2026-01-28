import os
import secrets
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/dev-seed", tags=["dev-seed"])

class SeedResult(BaseModel):
    ok: bool
    user_seed: str | None = None
    ledger_seed: str | None = None

def _check_seed_token(x_admin_seed_token: str | None) -> None:
    token = os.getenv("ADMIN_SEED_TOKEN", "")
    # Se não configurou token, o endpoint "não existe"
    if not token:
        raise HTTPException(status_code=404, detail="Not Found")
    if not x_admin_seed_token or not secrets.compare_digest(x_admin_seed_token, token):
        raise HTTPException(status_code=403, detail="Forbidden")

@router.get("/ping")
def ping():
    return {"ok": True}

@router.post("/seed", response_model=SeedResult, include_in_schema=False)
def seed(
    x_admin_seed_token: str | None = Header(default=None, alias="X-Admin-Seed-Token"),
):
    _check_seed_token(x_admin_seed_token)

    # Chamadas “plugáveis” (não quebram deploy; só falham se alguém chamar e a função não existir)
    user_seed_name = None
    ledger_seed_name = None

    from app.utils import seed_user as seed_user_mod
    from app.utils import ledger_seed as ledger_seed_mod

    # tenta vários nomes comuns pra reduzir atrito
    for name in ("seed_admin_user", "seed_admin", "seed_user", "run", "main"):
        fn = getattr(seed_user_mod, name, None)
        if callable(fn):
            fn()
            user_seed_name = name
            break

    for name in ("seed_ledger_from_users", "seed_ledger", "seed_initial_ledger", "ledger_seed", "run", "main"):
        fn = getattr(ledger_seed_mod, name, None)
        if callable(fn):
            fn()
            ledger_seed_name = name
            break

    return SeedResult(ok=True, user_seed=user_seed_name, ledger_seed=ledger_seed_name)

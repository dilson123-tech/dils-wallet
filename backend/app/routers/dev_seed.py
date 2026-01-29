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


@router.get("/schema", include_in_schema=False)
def schema(
    x_admin_seed_token: str | None = Header(default=None, alias="X-Admin-Seed-Token"),
):
    _check_seed_token(x_admin_seed_token)
    from sqlalchemy import inspect
    from app.database import engine
    insp = inspect(engine)
    tables = sorted(insp.get_table_names())
    focus = {}
    for tn in ("user_main", "users", "pix_ledger", "pix_ledger_main"):
        if tn in tables:
            cols = [c.get("name") for c in insp.get_columns(tn)]
            focus[tn] = cols
    return {
        "dialect": engine.url.get_backend_name(),
        "tables_count": len(tables),
        "tables_focus": focus,
    }


@router.post("/seed-ledger", include_in_schema=False)
def seed_ledger(
    x_admin_seed_token: str | None = Header(default=None, alias="X-Admin-Seed-Token"),
):
    _check_seed_token(x_admin_seed_token)
    from app.utils.ledger_seed import seed_ledger_from_users
    try:
        result = seed_ledger_from_users()
        return {"ok": True, "ran": "seed_ledger_from_users", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("/admin-check", include_in_schema=False)
def admin_check(
    x_admin_seed_token: str | None = Header(default=None, alias="X-Admin-Seed-Token"),
):
    _check_seed_token(x_admin_seed_token)
    from sqlalchemy import text
    from app.database import engine

    q = text("SELECT id, email, username, role FROM users WHERE role='admin' ORDER BY id LIMIT 10;")
    with engine.begin() as conn:
        rows = [dict(r._mapping) for r in conn.execute(q).fetchall()]

    def mask(s):
        if not s: return None
        if "@" in s:
            a,b = s.split("@",1)
            return (a[:2] + "***@" + b)
        return s[:2] + "***"

    return {
        "admins": len(rows),
        "items": [{"id": r["id"], "email": mask(r.get("email")), "username": mask(r.get("username")), "role": r.get("role")} for r in rows],
    }

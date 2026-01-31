import os
import secrets
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

import re
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text
from app.database import engine

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


@router.post("/admin-reset-password", include_in_schema=False)
def admin_reset_password(
    x_admin_seed_token: str | None = Header(default=None, alias="X-Admin-Seed-Token"),
):
    _check_seed_token(x_admin_seed_token)

    # senha vem do ENV (não passa no curl)
    new_pw = os.getenv("ADMIN_TEMP_PASSWORD", "").strip()
    if not new_pw:
        # sem senha configurada, endpoint "não existe"
        raise HTTPException(status_code=404, detail="Not Found")

    from passlib.context import CryptContext
    from sqlalchemy import text
    from app.database import engine

    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hp = ctx.hash(new_pw)

    q = text("UPDATE users SET hashed_password = :hp WHERE role = 'admin';")
    with engine.begin() as conn:
        res = conn.execute(q, {"hp": hp})
        updated = getattr(res, "rowcount", None)

    return {"ok": True, "updated": updated}

def _env_pick(*keys: str) -> str:
    for k in keys:
        v = os.getenv(k)
        if v is not None:
            v = v.strip()
            if v:
                return v
    return ""

@router.post("/admin-reset-passwd")
def admin_reset_passwd(request: Request):
    """
    Reseta a senha do admin usando uma ENV (não retorna senha).
    Proteção: header X-Admin-Seed-Token deve bater com ADMIN_SEED_TOKEN (ou AUREA_DEV_SECRET).
    """

    expected = _env_pick("ADMIN_SEED_TOKEN", "admin_seed_token", "AUREA_DEV_SECRET", "aurea_dev_secret")
    if not expected:
        # se não tem seed token configurado, a rota "não existe"
        raise HTTPException(status_code=404, detail="Not Found")

    got = (request.headers.get("X-Admin-Seed-Token") or "").strip()
    if got != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_pass = _env_pick("ADMIN_TEMP_PASSWORD", "admin_temp_password", "adm_temp_password", "ADM_TEMP_PASSWORD")
    if not new_pass:
        raise HTTPException(status_code=400, detail="ADMIN_TEMP_PASSWORD missing")

    admin_email = _env_pick("ADMIN_EMAIL", "admin_email") or "admin@aurea.local"

    # hashing compat (tenta funções do projeto; fallback passlib)
    try:
        from app.utils.security import get_password_hash  # type: ignore
        hp = get_password_hash(new_pass)
    except Exception:
        try:
            from app.security import get_password_hash  # type: ignore
            hp = get_password_hash(new_pass)
        except Exception:
            from passlib.context import CryptContext
            hp = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(new_pass)

    table = _env_pick("USER_TABLE", "user_table") or "user_main"
    if not re.match(r"^[A-Za-z0-9_]+$", table):
        raise HTTPException(status_code=400, detail="Invalid USER_TABLE")

    cols_pwd = ["hashed_password", "password_hash", "password"]
    cols_email = ["email", "username"]

    used = None
    updated = 0
    last_err = None

    with engine.begin() as conn:
        for c_email in cols_email:
            for c_pwd in cols_pwd:
                if not re.match(r"^[A-Za-z0-9_]+$", c_email) or not re.match(r"^[A-Za-z0-9_]+$", c_pwd):
                    continue
                try:
                    r = conn.execute(
                        text(f"UPDATE {table} SET {c_pwd} = :hp WHERE {c_email} = :email"),
                        {"hp": hp, "email": admin_email},
                    )
                    if getattr(r, "rowcount", 0) and r.rowcount > 0:
                        used = f"{table}.{c_pwd} WHERE {c_email}"
                        updated = int(r.rowcount)
                        break
                except Exception as e:
                    last_err = e
                    continue
            if used:
                break

    if not used:
        print("[dev-seed] admin-reset-passwd failed:", repr(last_err))
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"ok": True, "admin_email": admin_email, "updated": updated, "used": used}

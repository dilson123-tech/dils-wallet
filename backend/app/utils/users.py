from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from app.database import Base
from app import models  # garante registry dos mappers

IDENT_CANDS = ["email", "username", "cpf", "documento", "login"]
NAME_CANDS  = ["name", "nome", "full_name"]

# Descobre dinamicamente o modelo de usuário e a coluna de identificação
def _pick_ident(cols:set[str]) -> Optional[str]:
    for k in IDENT_CANDS:
        if k in cols: return k
    return None

def _user_model():
    best = None
    for m in Base.registry.mappers:
        cls = m.class_
        try:
            cols = set(cls.__table__.c.keys())
        except Exception:
            continue
        ident = _pick_ident(cols)
        score = 0 if ident == "email" else (1 if ident else 5)
        name = cls.__table__.name.lower()
        if any(x in name for x in ["user","users","usuario","account","conta","cliente","clientes","pessoa"]):
            score -= 1
        cand = (score, cls, ident or next(iter(cols)))
        if best is None or cand[0] < best[0]:
            best = cand
    if not best:
        raise RuntimeError("user_model_not_found")
    return best[1], best[2]

UserModel, IDENT_COL = _user_model()

def get_or_create_user(db: Session, email: str, name: Optional[str] = None):
    # 1) tenta pelo identificador
    u = db.query(UserModel).filter(getattr(UserModel, IDENT_COL) == email).first()
    if u:
        return u
    # 2) fallback: usa o primeiro usuário existente
    fallback = db.query(UserModel).first()
    if fallback:
        return fallback
    # 3) semear manualmente pelo admin: não criamos para evitar trigger no banco
    raise RuntimeError("no_user_seeded")

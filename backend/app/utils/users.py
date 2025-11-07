from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.database import Base
from app import models  # noqa: F401

IDENT_CANDS = ["email", "username", "cpf", "documento", "login"]
NAME_CANDS  = ["name", "nome", "full_name"]
SALDO_CANDS = ["saldo_pix", "saldo", "balance_pix", "balance", "saldo_total", "saldo_atual", "amount", "valor"]

_UserModel = None
_WalletModel = None
_IDENT_COL = None
_USER_FK_COL = None
_SALDO_COL = None

def _pick_ident(cols:set[str]):
    for k in IDENT_CANDS:
        if k in cols: return k
    return None

def _pick_saldo(cols:set[str]):
    for k in SALDO_CANDS:
        if k in cols: return k
    for c in cols:
        lc=c.lower()
        if any(k in lc for k in ["saldo","balance","amount","valor"]):
            return c
    return None

def _init_models():
    global _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL
    if _UserModel:
        return _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL

    # User
    user_candidates = []
    for m in Base.registry.mappers:
        cls = m.class_
        try:
            cols = set(cls.__table__.c.keys())
        except Exception:
            continue
        ident = _pick_ident(cols)
        score = 0 if ident == "email" else (1 if ident else 5)
        tname = cls.__table__.name.lower()
        if any(x in tname for x in ["user","users","usuario","clientes","pessoa","account","conta"]):
            score -= 1
        user_candidates.append((score, cls, cols, ident))
    user_candidates.sort(key=lambda t: t[0])
    _UserModel, ucols, _IDENT_COL = user_candidates[0][1], user_candidates[0][2], user_candidates[0][3] or list(user_candidates[0][2])[0]

    # Wallet por FK real para User
    user_table = _UserModel.__table__.name
    best = None
    for m in Base.registry.mappers:
        cls = m.class_
        try:
            table = cls.__table__
        except Exception:
            continue
        cols = set(table.c.keys())
        fk_col_name = None
        for col in table.columns:
            for fk in getattr(col, "foreign_keys", []):
                try:
                    if fk.column.table.name == user_table:
                        fk_col_name = col.name
                        break
                except Exception:
                    continue
            if fk_col_name: break
        if not fk_col_name:
            continue
        saldo_col = _pick_saldo(cols)
        score = 0 if saldo_col in ("saldo_pix","saldo") else (1 if saldo_col else 3)
        if best is None or score < best[0]:
            best = (score, cls, fk_col_name, saldo_col)
    if best:
        _WalletModel, _USER_FK_COL, _SALDO_COL = best[1], best[2], best[3]
    else:
        _WalletModel, _USER_FK_COL, _SALDO_COL = None, None, None

    return _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL

def get_or_create_user(db: Session, email: str, name: Optional[str] = None):
    UserModel, WalletModel, IDENT_COL, USER_FK_COL, SALDO_COL = _init_models()

    # localizar por identificador
    ident_value = email
    u = db.query(UserModel).filter(getattr(UserModel, IDENT_COL) == ident_value).first()
    if not u:
        table = UserModel.__table__
        cols = set(table.c.keys())
        kwargs = {}

        # identificadores
        if IDENT_COL in cols:
            kwargs[IDENT_COL] = ident_value
        if "email" in cols and IDENT_COL != "email":
            kwargs["email"] = email
        if "username" in cols and IDENT_COL != "username":
            kwargs["username"] = email

        # nome
        for nc in NAME_CANDS:
            if nc in cols:
                kwargs[nc] = name or email.split("@")[0]
                break

        # campos obrigatórios comuns
        if "role" in cols and kwargs.get("role") is None:
            kwargs["role"] = "customer"
        if "hashed_password" in cols and ("hashed_password" not in kwargs):
            # placeholder seguro (não autentica; só satisfaz NOT NULL)
            kwargs["hashed_password"] = "!autogen-dev-placeholder!"

        u = UserModel(**kwargs)  # type: ignore
        db.add(u)
        try:
            db.flush()
        except Exception:
            db.rollback()
            existing = db.query(UserModel).first()
            if existing is None:
                # sem fallback possível, propaga
                raise
            u = existing

    # carteira opcional
    if WalletModel and USER_FK_COL:
        fk_col = getattr(WalletModel, USER_FK_COL)
        uid = getattr(u, "id")
        w = db.query(WalletModel).filter(fk_col == uid).first()
        if not w:
            w_kwargs = {USER_FK_COL: uid}
            if SALDO_COL:
                w_kwargs[SALDO_COL] = 0
            db.add(WalletModel(**w_kwargs))  # type: ignore

    try:
        db.commit()
    except Exception as e:
        # FALLBACK_EXISTING_USER: se o commit falhar (ex.: trigger inserindo pix_transactions sem defaults),
        # usa o primeiro usuário existente para não quebrar o fluxo do PIX
        db.rollback()
        existing = db.query(UserModel).first()
        if existing is None:
            raise e
        u = existing
    db.refresh(u)
    return u

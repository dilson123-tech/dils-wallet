from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.database import Base
from app import models  # noqa: F401

IDENT_CANDS = ["email", "cpf", "documento", "username", "login"]
NAME_CANDS  = ["name", "nome", "full_name"]
SALDO_CANDS = ["saldo_pix", "saldo", "balance_pix", "balance", "saldo_total", "saldo_atual", "amount", "valor"]

_UserModel = None
_WalletModel = None
_IDENT_COL = None
_USER_FK_COL = None
_SALDO_COL = None

def _pick_ident(cols:set[str]) -> Optional[str]:
    for k in IDENT_CANDS:
        if k in cols: return k
    return None

def _pick_saldo(cols:set[str]) -> Optional[str]:
    for k in SALDO_CANDS:
        if k in cols: return k
    # fallback heurístico por nome
    for c in cols:
        lc=c.lower()
        if any(k in lc for k in ["saldo","balance","amount","valor"]):
            return c
    return None

def _init_models() -> Tuple[object, Optional[object], str, Optional[str], Optional[str]]:
    global _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL
    if _UserModel:
        return _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL

    # 1) User: por coluna identificadora, senão por nome da tabela
    user_candidates = []
    for m in Base.registry.mappers:
        cls = m.class_
        try: cols = set(cls.__table__.c.keys())
        except Exception: continue
        ident = _pick_ident(cols)
        score = 0 if ident=="email" else (1 if ident else 5)
        tname = cls.__table__.name.lower()
        if any(x in tname for x in ["user","users","usuario","clientes","pessoa","account","conta"]):
            score -= 1
        user_candidates.append((score, cls, cols, ident))
    if not user_candidates:
        raise RuntimeError("nenhum modelo SQLAlchemy registrado")
    user_candidates.sort(key=lambda t:t[0])
    _UserModel = user_candidates[0][1]
    _IDENT_COL = user_candidates[0][3] or list(_UserModel.__table__.c.keys())[0]  # usa 1ª se não houver

    # 2) Wallet: por FK real para User + coluna de saldo (se existir)
    user_table = _UserModel.__table__.name
    best = None
    for m in Base.registry.mappers:
        cls = m.class_
        try: table = cls.__table__
        except Exception: continue
        cols = set(table.c.keys())
        # acha FK que aponta para a tabela do usuário
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
        # score: com saldo preferido é melhor
        score = 0 if saldo_col in ("saldo_pix","saldo") else (1 if saldo_col else 3)
        best = (score, cls, fk_col_name, saldo_col) if (best is None or score < best[0]) else best

    if best:
        _WalletModel = best[1]; _USER_FK_COL = best[2]; _SALDO_COL = best[3]
    else:
        _WalletModel = None; _USER_FK_COL = None; _SALDO_COL = None

    return _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL

def get_or_create_user(db: Session, email: str, name: Optional[str] = None):
    UserModel, WalletModel, IDENT_COL, USER_FK_COL, SALDO_COL = _init_models()

    ident_value = email  # usamos email como identificador universal (ou o que a tabela tiver)
    u = db.query(UserModel).filter(getattr(UserModel, IDENT_COL) == ident_value).first()
    if not u:
        kwargs = {IDENT_COL: ident_value}
        for nc in NAME_CANDS:
            if hasattr(UserModel, nc):
                kwargs[nc] = name or email.split("@")[0]; break
        u = UserModel(**kwargs)
        db.add(u)
        db.flush()

    # carteira é opcional: só cria se modelo existir
    if WalletModel and USER_FK_COL:
        fk_col = getattr(WalletModel, USER_FK_COL)
        w = db.query(WalletModel).filter(fk_col == getattr(u, "id")).first()
        if not w:
            w_kwargs = {USER_FK_COL: getattr(u, "id")}
            if SALDO_COL: w_kwargs[SALDO_COL] = 0
            db.add(WalletModel(**w_kwargs))

    db.commit()
    db.refresh(u)
    return u

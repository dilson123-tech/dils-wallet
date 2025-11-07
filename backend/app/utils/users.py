from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.database import Base
from app import models  # noqa: F401  (garante registro dos mappers)

# preferências de nomes de colunas
IDENT_CANDIDATES = ["email", "cpf", "documento", "username", "login"]
NAME_CANDIDATES  = ["name", "nome", "full_name"]
USER_FK_CANDS    = ["user_id", "cliente_id", "account_id", "usuario_id", "owner_id", "userId"]
SALDO_CANDS      = ["saldo_pix", "saldo", "balance_pix", "balance"]

_UserModel = None
_WalletModel = None
_IDENT_COL = None
_USER_FK_COL = None
_SALDO_COL = None

def _init_models() -> Tuple[type, type, str, str, str]:
    global _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL
    if _UserModel and _WalletModel:
        return _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL

    # 1) descobrir modelo de usuário pelo identificador
    user_candidates: list[tuple[type, set[str]]] = []
    for m in Base.registry.mappers:
        cls = m.class_
        try:
            cols = set(cls.__table__.c.keys())
        except Exception:
            continue
        if any(c in cols for c in IDENT_CANDIDATES):
            user_candidates.append((cls, cols))

    if not user_candidates:
        raise RuntimeError("Não há modelo de usuário com colunas identificadoras (email/cpf/documento/username/login).")

    # escolhe o que tiver 'email' > 'cpf' > ...
    def ident_of(cols: set[str]) -> Optional[str]:
        for k in IDENT_CANDIDATES:
            if k in cols: return k
        return None

    user_candidates.sort(key=lambda t: IDENT_CANDIDATES.index(ident_of(t[1])) if ident_of(t[1]) in IDENT_CANDIDATES else 99)
    _UserModel, ucols = user_candidates[0]
    _IDENT_COL = ident_of(ucols)  # type: ignore

    # 2) descobrir carteira: precisa ter alguma FK de usuário e coluna de saldo
    wallet_candidates: list[tuple[type, set[str], str, str]] = []
    for m in Base.registry.mappers:
        cls = m.class_
        try:
            cols = set(cls.__table__.c.keys())
        except Exception:
            continue
        fk_match = next((fk for fk in USER_FK_CANDS if fk in cols), None)
        saldo_match = next((sc for sc in SALDO_CANDS if sc in cols), None)
        if fk_match and saldo_match:
            wallet_candidates.append((cls, cols, fk_match, saldo_match))

    if not wallet_candidates:
        raise RuntimeError("Não há modelo de carteira com FK para usuário e coluna de saldo.")

    # preferência: saldo_pix > saldo > balance_pix > balance
    def saldo_rank(c: str) -> int:
        order = {k:i for i,k in enumerate(SALDO_CANDS)}
        return order.get(c, 99)

    wallet_candidates.sort(key=lambda t: saldo_rank(t[3]))
    _WalletModel, wcols, _USER_FK_COL, _SALDO_COL = wallet_candidates[0]

    return _UserModel, _WalletModel, _IDENT_COL, _USER_FK_COL, _SALDO_COL  # type: ignore

def get_or_create_user(db: Session, email: str, name: Optional[str] = None):
    UserModel, WalletModel, IDENT_COL, USER_FK_COL, SALDO_COL = _init_models()

    # localizar por identificador (se o ident não for email, usamos o email como valor do ident por ora)
    ident_value = email
    u = db.query(UserModel).filter(getattr(UserModel, IDENT_COL) == ident_value).first()
    if not u:
        kwargs = {IDENT_COL: ident_value}
        # setar nome, se existir
        for nc in NAME_CANDIDATES:
            if hasattr(UserModel, nc):
                kwargs[nc] = name or email.split("@")[0]
                break
        u = UserModel(**kwargs)  # type: ignore
        db.add(u)
        db.flush()

    # garantir carteira
    fk_col = getattr(WalletModel, USER_FK_COL)
    uid = getattr(u, "id")
    w = db.query(WalletModel).filter(fk_col == uid).first()
    if not w:
        w_kwargs = {USER_FK_COL: uid, SALDO_COL: 0}
        db.add(WalletModel(**w_kwargs))  # type: ignore

    db.commit()
    db.refresh(u)
    return u

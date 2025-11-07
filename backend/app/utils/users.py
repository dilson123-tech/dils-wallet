from typing import Optional
from sqlalchemy.orm import Session
from app.database import Base
from app import models

def _find_model(cols_required: list[str], cols_any: Optional[list[str]] = None):
    """Busca uma classe ORM contendo colunas obrigatórias e opcionais."""
    for m in Base.registry.mappers:
        cls = m.class_
        try:
            cols = set(cls.__table__.c.keys())
        except Exception:
            continue
        if not set(cols_required).issubset(cols):
            continue
        if cols_any and not (set(cols_any) & cols):
            continue
        return cls
    raise RuntimeError(f"Nenhum modelo encontrado com {cols_required}")

# localizar dinamicamente modelos
UserModel = _find_model(["email"])
_user_fk_candidates = ["user_id", "owner_id", "usuario_id", "userId"]
_saldo_candidates = ["saldo_pix", "saldo", "balance_pix", "balance"]

WalletModel = None
USER_FK_COL = None
for fk in _user_fk_candidates:
    try:
        WalletModel = _find_model([fk], _saldo_candidates)
        USER_FK_COL = fk
        break
    except Exception:
        continue
if WalletModel is None:
    raise RuntimeError("Não foi possível localizar modelo de carteira.")

SALDO_COL = next(iter(set(WalletModel.__table__.c.keys()) & set(_saldo_candidates)))

def get_or_create_user(db: Session, email: str, name: Optional[str] = None):
    """Cria ou retorna usuário e carteira associada."""
    u = db.query(UserModel).filter(getattr(UserModel, "email") == email).first()
    if not u:
        kwargs = {"email": email}
        if hasattr(UserModel, "name"):
            kwargs["name"] = name or email.split("@")[0]
        elif hasattr(UserModel, "nome"):
            kwargs["nome"] = name or email.split("@")[0]
        u = UserModel(**kwargs)
        db.add(u)
        db.flush()

    fk_col = getattr(WalletModel, USER_FK_COL)
    w = db.query(WalletModel).filter(fk_col == getattr(u, "id")).first()
    if not w:
        w_kwargs = {USER_FK_COL: getattr(u, "id"), SALDO_COL: 0}
        db.add(WalletModel(**w_kwargs))
    db.commit()
    db.refresh(u)
    return u

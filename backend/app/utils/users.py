from typing import Optional
from sqlalchemy.orm import Session
from app.database import Base
from app import models  # importa o módulo para registrar mappers

def _find_model(cols_required: list[str], cols_any: Optional[list[str]] = None):
    """
    Encontra uma classe ORM cujo __table__.c contenha todas as cols_required
    e (se fornecido) pelo menos uma de cols_any.
    """
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
    raise RuntimeError(f"Nenhum modelo com colunas {cols_required}"
                       + (f" e uma de {cols_any}" if cols_any else ""))

# Heurísticas:
# - Usuário: precisa ter 'email'; aceita variações de nome da classe (dinâmico)
UserModel = _find_model(cols_required=["email"])

# - Carteira: precisa ter relação com usuário + saldo
#   aceita variações: user_id|owner_id|usuario_id  e saldo_pix|saldo
WalletModel = None
_user_fk_candidates = ["user_id", "owner_id", "usuario_id", "userId"]
_saldo_candidates = ["saldo_pix", "saldo", "balance_pix", "balance"]

for fk in _user_fk_candidates:
    try:
        WalletModel = _find_model(cols_required=[fk], cols_any=_saldo_candidates)
        USER_FK_COL = fk
        break
    except Exception:
        continue

if WalletModel is None:
    raise RuntimeError("Nenhum modelo de carteira/carteira_pix encontrado (precisa ter FK de usuário e coluna de saldo).")

# Resolve nome efetivo da coluna de saldo
SALDO_COL = next(iter(set(WalletModel.__table__.c.keys()) & set(_saldo_candidates)))

def get_or_create_user(db: Session, email: str, name: Optional[str] = None):
    # query dinâmica por coluna 'email'
    u = db.query(UserModel).filter(getattr(UserModel, "email") == email).first()
    if not u:
        # tenta nome/nickname se existir
        kwargs = {"email": email}
        if hasattr(UserModel, "name"):
            kwargs["name"] = name or email.split("@")[0]
        elif hasattr(UserModel, "nome"):
            kwargs["nome"] = name or email.split("@")[0]
        u = UserModel(**kwargs)  # type: ignore
        db.add(u)
        db.flush()  # garante u.id

    # garantir carteira
    fk_col = getattr(WalletModel, USER_FK_COL)
    w = db.query(WalletModel).filter(fk_col == getattr(u, "id")).first()
    if not w:
        w_kwargs = {USER_FK_COL: getattr(u, "id"), SALDO_COL: 0}
        w = WalletModel(**w_kwargs)  # type: ignore
        db.add(w)

    db.commit()
    db.refresh(u)
    return u

from sqlalchemy.orm import Session
from app import models

def get_or_create_user(db: Session, email: str, name: str | None = None):
    u = db.query(models.User).filter(models.User.email == email).first()
    if u:
        return u
    u = models.User(email=email, name=name or email.split("@")[0])
    db.add(u)
    db.flush()
    if not db.query(models.Wallet).filter(models.Wallet.user_id == u.id).first():
        db.add(models.Wallet(user_id=u.id, saldo_pix=0))
    db.commit()
    db.refresh(u)
    return u

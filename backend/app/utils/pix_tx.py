from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

def create_pix_tx(db: Session, user_id: int, valor: float, descricao: Optional[str] = None, tipo: str = "envio") -> int:
    v = float(valor or 0)
    if v <= 0:
        raise ValueError("valor_invalido")
    t = tipo or "envio"
    stmt = text("""
        INSERT INTO pix_transactions (user_id, tipo, valor, descricao)
        VALUES (:user_id, :tipo, :valor, :descricao)
        RETURNING id
    """)
    rid = db.execute(stmt, {"user_id": user_id, "tipo": t, "valor": v, "descricao": descricao}).scalar()
    db.commit()
    return int(rid)

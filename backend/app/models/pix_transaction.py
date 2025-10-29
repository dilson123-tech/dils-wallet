from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from app.models import Base  # garante que usamos a Base declarada em app/models/__init__.py

class PixTransaction(Base):
    __tablename__ = "pix_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    # "entrada" ou "saida"
    tipo = Column(String(20), nullable=False)

    # valor em dinheiro (ex: 159.32)
    valor = Column(Numeric(10, 2), nullable=False)

    # ex: "PIX demo", "Transferência PIX mercado"
    descricao = Column(String(255), nullable=False)

    # quando aconteceu
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # IMPORTANTE:
    # removemos relationship("User", back_populates="pix_transactions")
    # pra evitar erro de mapeamento circular enquanto a app sobe.

from sqlalchemy import Column, String

# adiciona o campo descricao se não existir
if not hasattr(PixTransaction, "descricao"):
    PixTransaction.descricao = Column(String, nullable=True)

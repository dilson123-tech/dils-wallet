from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from . import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    # tipo da movimentação: "credit", "debit"
    kind = Column(String(20), nullable=False)

    # descrição tipo "PIX recebido de João", "Pagamento QR Code", etc
    description = Column(String(255), nullable=False, default="")
    reference = Column(String(100), nullable=True)

    # valor em centavos ou decimal controlado
    amount = Column(Numeric(scale=2), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", backref="transactions")

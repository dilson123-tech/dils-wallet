from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.app.database import Base

class PixTransaction(Base):
    __tablename__ = "pix_transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

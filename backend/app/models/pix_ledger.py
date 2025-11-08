from sqlalchemy import Column, Integer, String, Numeric, DateTime, func, CheckConstraint, Index
from app.database import Base

class PixLedger(Base):
    __tablename__ = "pix_ledger"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    kind = Column(String(6), nullable=False)  # 'credit' | 'debit'
    amount = Column(Numeric(14, 2), nullable=False)
    ref_tx_id = Column(Integer, nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("kind in ('credit','debit')", name="ck_pix_ledger_kind"),
        CheckConstraint("amount >= 0", name="ck_pix_ledger_amount_nonneg"),
        Index("ix_pix_ledger_user_created", "user_id", "created_at"),
    )

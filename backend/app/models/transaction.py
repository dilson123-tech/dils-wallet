from sqlalchemy import Column, Integer, String, ForeignKey, Float
from ..database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tipo      = Column(String, index=True)
    valor     = Column(Float, nullable=False)
    referencia = Column(String, nullable=True)

from sqlalchemy import Column, Integer, String, Float
from ..database import Base

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(100))
    balance = Column(Float, default=0.0)

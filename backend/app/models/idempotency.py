from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(128), unique=True, nullable=False, index=True)
    status_code = Column(Integer, nullable=True)
    response_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

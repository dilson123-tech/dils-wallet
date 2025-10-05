from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from ..database import Base

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key = Column(String(64), primary_key=True)
    request_hash = Column(String(128), nullable=False)
    response_body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from backend.app.database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)

    ip = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    active = Column(Boolean, nullable=False, default=True, index=True)

Index("ix_refresh_active_user", RefreshToken.active, RefreshToken.user_id)

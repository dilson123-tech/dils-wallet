from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from . import Base


class RefreshTokenRetiredHash(Base):
    """Hash (sha256) de um refresh token que já foi rotacionado.

    family_id é o id da linha de refresh_tokens -- estável entre
    rotações (a rotação é in-place). Serve só para detectar reuse: se um
    hash aposentado for reapresentado fora da grace window, a família
    inteira é revogada. Nunca guarda o token cru.
    """

    __tablename__ = "refresh_token_retired_hashes"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    family_id = Column(
        Integer,
        ForeignKey("refresh_tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    retired_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=lambda: datetime.now(timezone.utc),
    )

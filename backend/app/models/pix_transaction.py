from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from app.database import Base

class PixTransaction(Base):
    __tablename__ = "pix_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)

    # tipo normalizado
    tipo = Column(String(20), nullable=False)

    # valor NUMERIC(10,2)
    valor = Column(Numeric(10, 2), nullable=False)

    # descricao blindada: sempre default "PIX"
    descricao = Column(String(255), nullable=False, default="PIX")

    timestamp = Column(DateTime(timezone=True),
                       server_default=func.datetime('now'),
                       nullable=False)

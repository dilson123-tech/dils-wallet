from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from app.database import Base


class PixTransaction(Base):
    __tablename__ = "pix_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)

    # tipo normalizado (envio, recebido, etc.)
    tipo = Column(String(20), nullable=False)

    # valor original NUMERIC(10,2)
    valor = Column(Numeric(10, 2), nullable=False)

    # descricao blindada: sempre default "PIX"
    descricao = Column(String(255), nullable=False, default="PIX")

    # 🔹 Campos de taxa do Aurea Gold (preparados para produção)
    # taxa_percentual: ex.: 0.008 = 0,8%
    taxa_percentual = Column(Numeric(5, 4), nullable=True)

    # taxa_valor: valor absoluto da taxa cobrada em R$
    taxa_valor = Column(Numeric(10, 2), nullable=True)

    # valor_liquido: valor após desconto da taxa (para saldo / relatórios)
    valor_liquido = Column(Numeric(10, 2), nullable=True)

    # timestamp da transação (já usado pelo histórico)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.datetime("now"),
        nullable=False,
    )

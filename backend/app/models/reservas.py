from datetime import datetime, date

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String

from app.database import Base


class Reserva(Base):
    """
    Modelo oficial de reservas de recursos do Aurea Gold.

    Esta tabela centraliza a visão operacional das reservas:
    - quem reservou (cliente)
    - qual recurso (sala, auditório, espaço premium etc.)
    - data e horário
    - status (ativa, cancelada, concluída)
    - valor confirmado / pendente.
    """

    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)

    # Quem está reservando
    cliente = Column(String(220), nullable=False)
    # Qual recurso está sendo usado (sala, auditório, espaço premium etc.)
    recurso = Column(String(220), nullable=False)

    # Data da reserva (data do evento)
    data = Column(Date, nullable=False, index=True)

    # Janela de horário no formato simples "19:00 - 22:00"
    horario = Column(String(64), nullable=False)

    # Valor associado à reserva
    valor = Column(Numeric(12, 2), nullable=False, default=0)

    # Status da reserva no tempo:
    # - "ativa"
    # - "cancelada"
    # - "concluída"
    status = Column(
        String(20),
        nullable=False,
        default="pendente",
        doc="Status operacional da reserva (ativa, cancelada, concluída).",
    )

    # Campos de auditoria
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

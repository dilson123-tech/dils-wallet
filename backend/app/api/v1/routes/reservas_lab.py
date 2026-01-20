from datetime import date, timedelta
from typing import List, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(
    prefix="/reservas",
    tags=["reservas_lab"],
)

PeriodoLiteral = Literal["hoje", "7d", "30d"]


class Receita(BaseModel):
    id: int
    origem: str
    valor: float
    data: date
    status: Literal["confirmada", "pendente"]


class Reserva(BaseModel):
    id: int
    cliente: str
    recurso: str
    data: date
    horario: str
    status: Literal["ativa", "cancelada", "concluída"]


class Totais(BaseModel):
    receitas_confirmadas: float
    reservas_periodo: int


class PainelReservasResponse(BaseModel):
    periodo: PeriodoLiteral
    label_periodo: str
    receitas: List[Receita]
    reservas: List[Reserva]
    totais: Totais


# --- Dados LAB (iguais ao painel 1) ---

HOJE_FIXO = date(2025, 11, 29)

RECEITAS_LAB: List[Receita] = [
    Receita(
        id=1,
        origem="Reserva Sala Reunião 01",
        valor=350.0,
        data=date(2025, 11, 29),
        status="confirmada",
    ),
    Receita(
        id=2,
        origem="Reserva Auditório Aurea",
        valor=900.0,
        data=date(2025, 11, 29),
        status="confirmada",
    ),
    Receita(
        id=3,
        origem="Reserva Espaço Premium",
        valor=520.5,
        data=date(2025, 11, 28),
        status="pendente",
    ),
    Receita(
        id=4,
        origem="Reserva Coworking Flex",
        valor=180.0,
        data=date(2025, 11, 23),
        status="confirmada",
    ),
    Receita(
        id=5,
        origem="Reserva Estacionamento VIP",
        valor=75.0,
        data=date(2025, 11, 10),
        status="confirmada",
    ),
]

RESERVAS_LAB: List[Reserva] = [
    Reserva(
        id=11,
        cliente="Empresa Alpha LTDA",
        recurso="Sala Reunião 01",
        data=date(2025, 11, 29),
        horario="09:00 - 11:00",
        status="ativa",
    ),
    Reserva(
        id=12,
        cliente="Tech Beta Solutions",
        recurso="Auditório Aurea",
        data=date(2025, 11, 29),
        horario="14:00 - 18:00",
        status="ativa",
    ),
    Reserva(
        id=13,
        cliente="StartUp Gama",
        recurso="Espaço Premium",
        data=date(2025, 11, 30),
        horario="19:00 - 22:00",
        status="concluída",
    ),
    Reserva(
        id=14,
        cliente="Cowork People",
        recurso="Coworking Flex",
        data=date(2025, 11, 23),
        horario="08:00 - 18:00",
        status="concluída",
    ),
    Reserva(
        id=15,
        cliente="Logística Delta",
        recurso="Vaga Estacionamento VIP",
        data=date(2025, 11, 10),
        horario="Dia todo",
        status="cancelada",
    ),
]


def _label_periodo(periodo: PeriodoLiteral) -> str:
    if periodo == "hoje":
        return "Hoje"
    if periodo == "7d":
        return "Últimos 7 dias"
    return "Últimos 30 dias"


def _dentro_do_periodo(d: date, periodo: PeriodoLiteral) -> bool:
    if periodo == "hoje":
        return d == HOJE_FIXO
    if periodo == "7d":
        return d >= HOJE_FIXO - timedelta(days=6)
    return d >= HOJE_FIXO - timedelta(days=29)


@router.get("/painel_lab", response_model=PainelReservasResponse)
def get_painel_reservas_lab(
    periodo: PeriodoLiteral = Query("hoje", description="hoje | 7d | 30d"),
) -> PainelReservasResponse:
    receitas_filtradas = [
        r for r in RECEITAS_LAB if _dentro_do_periodo(r.data, periodo)
    ]
    reservas_filtradas = [
        r for r in RESERVAS_LAB if _dentro_do_periodo(r.data, periodo)
    ]

    total_receitas = sum(
        r.valor for r in receitas_filtradas if r.status == "confirmada"
    )

    totais = Totais(
        receitas_confirmadas=total_receitas,
        reservas_periodo=len(reservas_filtradas),
    )

    return PainelReservasResponse(
        periodo=periodo,
        label_periodo=_label_periodo(periodo),
        receitas=receitas_filtradas,
        reservas=reservas_filtradas,
        totais=totais,
    )

@router.get("/painel", response_model=PainelReservasResponse)
def get_painel_reservas(
    periodo: PeriodoLiteral = Query("hoje", description="hoje | 7d | 30d"),
) -> PainelReservasResponse:
    """
    ENDPOINT OFICIAL do painel de reservas & receitas.

    Neste momento, ele reutiliza exatamente a mesma lógica da versão LAB,
    apenas expondo em uma rota estável (/reservas/painel) para o frontend.

    No futuro, vamos trocar o backend para ler da tabela oficial de reservas
    no banco, mantendo o mesmo contrato de resposta.
    """
    receitas_filtradas = [
        r for r in RECEITAS_LAB if _dentro_do_periodo(r.data, periodo)
    ]
    reservas_filtradas = [
        r for r in RESERVAS_LAB if _dentro_do_periodo(r.data, periodo)
    ]

    total_receitas = sum(
        r.valor for r in receitas_filtradas if r.status == "confirmada"
    )

    totais = Totais(
        receitas_confirmadas=total_receitas,
        reservas_periodo=len(reservas_filtradas),
    )

    return PainelReservasResponse(
        periodo=periodo,
        label_periodo=_label_periodo(periodo),
        receitas=receitas_filtradas,
        reservas=reservas_filtradas,
        totais=totais,
    )

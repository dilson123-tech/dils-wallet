from datetime import datetime
import calendar
from decimal import Decimal

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction


router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

# Mesma lógica do pix_balance_get: usuário fixo por enquanto.
USER_FIXO_ID = 1


@router.get("/forecast")
def get_pix_forecast(
    x_user_email: str = Header(..., alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    """
    Versão GET da rota /api/v1/pix/forecast.

    Por enquanto:
    - Ignora o e-mail e usa um usuário fixo (USER_FIXO_ID).
    - Calcula entradas/saídas via PixTransaction.
    - Faz uma projeção simples até o fim do mês.
    """

    debug_error = None

    try:
        # Somatórios de entradas e saídas, igual ao pix_balance_get
        entradas = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
            .filter(
                PixTransaction.user_id == USER_FIXO_ID,
                PixTransaction.tipo.in_(["recebimento", "entrada"]),
            )
            .scalar()
            or 0.0
        )

        saidas = (
            db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
            .filter(
                PixTransaction.user_id == USER_FIXO_ID,
                PixTransaction.tipo.in_(["envio", "saida"]),
            )
            .scalar()
            or 0.0
        )

        saldo_atual = float(entradas - saidas)

        # Dados de calendário (mês atual, UTC)
        agora = datetime.utcnow()
        dia_atual = max(agora.day, 1)
        dias_mes = calendar.monthrange(agora.year, agora.month)[1]

        # Média diária de saídas e projeção até o fim do mês
        if dia_atual > 0:
            media_saidas_dia = float(saidas) / dia_atual
        else:
            media_saidas_dia = 0.0

        previsao_saidas_total = media_saidas_dia * dias_mes
        previsao_fim_mes = float(entradas) - previsao_saidas_total

        # Classificação de risco simples
        if previsao_fim_mes >= 0:
            # Se ainda sobra pelo menos 20% das entradas, ok
            if entradas > 0 and previsao_fim_mes >= 0.2 * float(entradas):
                nivel_risco = "ok"
            else:
                nivel_risco = "atencao"
        else:
            # Negativo: olhar o tamanho do buraco
            if previsao_fim_mes >= -200:
                nivel_risco = "alerta"
            else:
                nivel_risco = "critico"

        # Análise textual
        if nivel_risco == "ok":
            analise = (
                "Com base no ritmo atual de entradas e saídas, "
                "sua projeção até o fim do mês está saudável. "
                "Você está gastando abaixo do que entra via PIX."
            )
            recomendacoes = [
                "Continue acompanhando entradas e saídas pelo painel Super2.",
                "Mantenha uma reserva mínima em conta para imprevistos.",
                "Se possível, direcione parte do saldo para uma reserva recorrente.",
            ]
        elif nivel_risco == "atencao":
            analise = (
                "Sua projeção até o fim do mês ainda fecha no positivo, "
                "mas bem apertado. O ritmo de gastos está perto do limite "
                "do que está entrando."
            )
            recomendacoes = [
                "Evite gastos não essenciais nos próximos dias.",
                "Revise as principais saídas do mês e veja o que pode ser reduzido.",
                "Acompanhe o consultor financeiro PIX para ajustar o ritmo de gastos.",
            ]
        elif nivel_risco == "alerta":
            analise = (
                "Se o ritmo de saídas continuar igual, há risco de fechar o mês "
                "no vermelho ou muito próximo de zero. É um cenário de alerta."
            )
            recomendacoes = [
                "Reduza imediatamente gastos variáveis e de lazer.",
                "Segure compras que não sejam realmente essenciais.",
                "Use o modo consultor financeiro para identificar onde cortar gastos.",
            ]
        else:  # critico
            analise = (
                "Pelo ritmo atual, a projeção indica que você pode terminar o mês "
                "no negativo de forma mais pesada. É um cenário crítico."
            )
            recomendacoes = [
                "Corte tudo que não for essencial até recuperar o equilíbrio.",
                "Avalie renegociar dívidas ou parcelamentos, se houver.",
                "Busque aumentar entradas (trabalhos extras, recebíveis antecipados).",
            ]

        payload = {
            "saldo_atual": float(saldo_atual),
            "entradas_mes": float(entradas),
            "saidas_mes": float(saidas),
            "previsao_fim_mes": float(previsao_fim_mes),
            "nivel_risco": nivel_risco,
            "analise": analise,
            "recomendacoes": recomendacoes,
            "debug_error": debug_error,
        }

        return JSONResponse(
            content=jsonable_encoder(payload, custom_encoder={Decimal: float})
        )

    except Exception as e:
        debug_error = str(e)
        payload = {
            "saldo_atual": 0.0,
            "entradas_mes": 0.0,
            "saidas_mes": 0.0,
            "previsao_fim_mes": 0.0,
            "nivel_risco": "indisponivel",
            "analise": (
                "Não consegui calcular a previsão de saldo neste momento. "
                "Tente novamente em alguns instantes."
            ),
            "recomendacoes": [
                "Atualize a página do painel pix e tente novamente.",
                "Se o problema persistir, fale com o suporte Aurea Gold.",
            ],
            "debug_error": debug_error,
        }
        return JSONResponse(
            content=jsonable_encoder(payload, custom_encoder={Decimal: float}),
            status_code=200,
        )

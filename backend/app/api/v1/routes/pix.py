from datetime import datetime
import calendar
from decimal import Decimal
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction


router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

# TODO: depois ligar com auth/jwt e X-User-Email
USER_FIXO_ID = 1


@router.get("/balance")
def get_balance(db: Session = Depends(get_db)):
    """
    Retorna o saldo PIX calculado:
    - entradas somam
    - saídas subtraem

    Normalizado para o painel SuperAureaHome:
    {
      "saldo": number,
      "source": "lab" | "real",
      "updated_at": ISO8601
    }
    """
    try:
        rows = (
            db.query(PixTransaction)
            .filter(PixTransaction.user_id == USER_FIXO_ID)
            .all()
        )

        saldo = 0.0
        for t in rows:
            valor = float(t.valor)
            if t.tipo == "entrada":
                saldo += valor
            else:
                saldo -= valor

        source = "real"
    except Exception as e:
        print("[AUREA PIX] erro ao calcular saldo:", e)
        saldo = 0.0
        source = "lab"

    payload = {
        "saldo": saldo,
        "source": source,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }

    return JSONResponse(
        content=jsonable_encoder(payload, custom_encoder={Decimal: float})
    )


@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    """
    Retorna as últimas transações do usuário.
    """
    txs = (
        db.query(PixTransaction)
        .filter(PixTransaction.user_id == USER_FIXO_ID)
        .order_by(PixTransaction.id.desc())
        .limit(20)
        .all()
    )

    result = [
        {
            "id": t.id,
            "tipo": t.tipo,
            "valor": float(t.valor),
            "descricao": t.descricao or "",
        }
        for t in txs
    ]

    return result

@router.get("/forecast")
def get_forecast(db: Session = Depends(get_db)):
    """
    Faz uma projeção simples do saldo até o fim do mês com base nas
    entradas e saídas PIX do usuário.

    Retorna:
    {
      "saldo_atual": number,
      "entradas_mes": number,
      "saidas_mes": number,
      "previsao_fim_mes": number,
      "nivel_risco": "ok" | "atencao" | "alerta" | "critico",
      "analise": str,
      "recomendacoes": [str, ...]
    }
    """
    try:
        rows = (
            db.query(PixTransaction)
            .filter(PixTransaction.user_id == USER_FIXO_ID)
            .all()
        )

        entradas = 0.0
        saidas = 0.0
        for t in rows:
            valor = float(t.valor)
            if t.tipo == "entrada":
                entradas += valor
            else:
                saidas += valor

        saldo_atual = entradas - saidas

        # Dados de calendário (mês atual, UTC)
        agora = datetime.utcnow()
        dia_atual = max(agora.day, 1)
        dias_mes = calendar.monthrange(agora.year, agora.month)[1]

        # Média diária de saídas e projeção até o fim do mês
        if dia_atual > 0:
            media_saidas_dia = saidas / dia_atual
        else:
            media_saidas_dia = 0.0

        previsao_saidas_total = media_saidas_dia * dias_mes
        previsao_fim_mes = entradas - previsao_saidas_total

        # Classificação de risco simples
        if previsao_fim_mes >= 0:
            # Se ainda sobra pelo menos 20% das entradas, ok
            if entradas > 0 and previsao_fim_mes >= 0.2 * entradas:
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
                "Se possível, direcione parte do saldo para uma reserva recorrente."
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
                "Acompanhe o consultor financeiro PIX para ajustar o ritmo de gastos."
            ]
        elif nivel_risco == "alerta":
            analise = (
                "Se o ritmo de saídas continuar igual, há risco de fechar o mês "
                "no vermelho ou muito próximo de zero. É um cenário de alerta."
            )
            recomendacoes = [
                "Reduza imediatamente gastos variáveis e de lazer.",
                "Segure compras que não sejam realmente essenciais.",
                "Use o modo consultor financeiro para identificar onde cortar gastos."
            ]
        else:  # critico
            analise = (
                "Pelo ritmo atual, a projeção indica que você pode terminar o mês "
                "no negativo de forma mais pesada. É um cenário crítico."
            )
            recomendacoes = [
                "Corte tudo que não for essencial até recuperar o equilíbrio.",
                "Avalie renegociar dívidas ou parcelamentos, se houver.",
                "Busque aumentar entradas (trabalhos extras, recebíveis antecipados)."
            ]

        payload = {
            "saldo_atual": saldo_atual,
            "entradas_mes": entradas,
            "saidas_mes": saidas,
            "previsao_fim_mes": previsao_fim_mes,
            "nivel_risco": nivel_risco,
            "analise": analise,
            "recomendacoes": recomendacoes,
        }

        return JSONResponse(
            content=jsonable_encoder(payload, custom_encoder={Decimal: float})
        )
    except Exception as e:
        print("[AUREA PIX] erro ao calcular forecast:", e)
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
                "Se o problema persistir, fale com o suporte Aurea Gold."
            ],
        "debug_error": str(e),
        }
        return JSONResponse(
            content=jsonable_encoder(payload, custom_encoder={Decimal: float}),
            status_code=200,
        )

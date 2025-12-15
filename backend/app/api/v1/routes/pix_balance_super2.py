from datetime import date, timedelta, datetime
import calendar

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models.user_main import User

# mesmo padrão da rota original de balance

from sqlalchemy import text
import json, base64
from typing import Optional

def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _jwt_sub_unverified(token: str) -> Optional[str]:
    # DEV: pega 'sub' sem validar assinatura
    try:
        _h, p, _s = token.split('.', 2)
    except ValueError:
        return None
    try:
        payload = json.loads(_b64url_decode(p).decode('utf-8'))
    except Exception:
        return None
    return payload.get('sub')

def _resolve_user_id(db, request, x_user_email: Optional[str]):
    auth = request.headers.get('authorization') or request.headers.get('Authorization')
    if auth and auth.lower().startswith('bearer '):
        sub = _jwt_sub_unverified(auth.split(' ',1)[1].strip())
        if sub:
            row = db.execute(text('SELECT id FROM users WHERE username=:u LIMIT 1'), {'u': sub}).fetchone()
            if row:
                return int(row[0])
    if x_user_email:
        row = db.execute(text('SELECT id FROM users WHERE email=:e LIMIT 1'), {'e': x_user_email}).fetchone()
        if row:
            return int(row[0])
    return None
router = APIRouter(prefix="/api/v1/pix", tags=["pix"])


@router.get("/balance/super2")
def get_pix_balance_super2(
    x_user_email: str = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    """
    Versão Super2 da rota /api/v1/pix/balance.

    - Usa o mesmo cálculo de saldo, entradas e saídas da rota original.
    - Adiciona um campo `ultimos_7d` para o painel Super2.
    """

    # --- mesmo começo da get_pix_balance ---
    user = db.query(User).filter(User.email == x_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    entradas = (
        db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
        .filter(
            PixTransaction.user_id == user.id,
            PixTransaction.tipo.in_(["recebimento", "entrada"]),
        )
        .scalar()
        or 0.0
    )

    saidas = (
        db.query(func.coalesce(func.sum(PixTransaction.valor), 0.0))
        .filter(
            PixTransaction.user_id == user.id,
            PixTransaction.tipo.in_(["envio", "saida"]),
        )
        .scalar()
        or 0.0
    )

    saldo = float(entradas - saidas)

    # --- mock simples dos últimos 7 dias (por enquanto tudo zero) ---
    hoje = date.today()
    ultimos_7d = []
    for i in range(6, -1, -1):
        d = hoje - timedelta(days=i)
        ultimos_7d.append(
            {
                "dia": d.isoformat(),
                "entradas": 0.0,
                "saidas": 0.0,
            }
        )

    return {
        "saldo_atual": float(saldo),
        "entradas_mes": float(entradas),
        "saidas_mes": float(saidas),
        "ultimos_7d": ultimos_7d,
    }

@router.get("/forecast_lab_old")
def get_pix_forecast(
    x_user_email: str = Header(..., alias="X-User-Email"),
    db: Session = Depends(get_db),
):
    """
    Projeta o saldo até o fim do mês com base nas entradas/saídas PIX do usuário.
    """
    try:
        user = db.query(User).filter(User.email == x_user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="user_not_found")

        rows = (
            db.query(PixTransaction)
            .filter(PixTransaction.user_id == user.id)
            .all()
        )

        entradas = 0.0
        saidas = 0.0
        for t in rows:
            valor = float(t.valor)
            if t.tipo in ["recebimento", "entrada"]:
                entradas += valor
            elif t.tipo in ["envio", "saida"]:
                saidas += valor

        saldo_atual = entradas - saidas

        agora = datetime.utcnow()
        dia_atual = max(agora.day, 1)
        dias_mes = calendar.monthrange(agora.year, agora.month)[1]

        if dia_atual > 0:
            media_saidas_dia = saidas / dia_atual
        else:
            media_saidas_dia = 0.0

        previsao_saidas_total = media_saidas_dia * dias_mes
        previsao_fim_mes = entradas - previsao_saidas_total

        if previsao_fim_mes >= 0:
            if entradas > 0 and previsao_fim_mes >= 0.2 * entradas:
                nivel_risco = "ok"
            else:
                nivel_risco = "atencao"
        else:
            if previsao_fim_mes >= -200:
                nivel_risco = "alerta"
            else:
                nivel_risco = "critico"

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
        else:
            analise = (
                "Pelo ritmo atual, a projeção indica que você pode terminar o mês "
                "no negativo de forma mais pesada. É um cenário crítico."
            )
            recomendacoes = [
                "Corte tudo que não for essencial até recuperar o equilíbrio.",
                "Avalie renegociar dívidas ou parcelamentos, se houver.",
                "Busque aumentar entradas (trabalhos extras, recebíveis antecipados).",
            ]

        return {
            "saldo_atual": float(saldo_atual),
            "entradas_mes": float(entradas),
            "saidas_mes": float(saidas),
            "previsao_fim_mes": float(previsao_fim_mes),
            "nivel_risco": nivel_risco,
            "analise": analise,
            "recomendacoes": recomendacoes,
        }
    except Exception as e:
        print("[AUREA PIX] erro ao calcular forecast:", e)
        return {
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
            "debug_error": str(e),
        }

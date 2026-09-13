import logging
logger = logging.getLogger("aurea.pix")
from app.core.rate_limit import limiter
from datetime import datetime, date, timedelta
import calendar
from decimal import Decimal
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Request, APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pix_transaction import PixTransaction
from app.models import User
from app.utils.authz import require_customer
from app.utils.authz import require_customer



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

def _ultimos_7d_dates() -> list:
    """Janela fixa de 7 dias: hoje e os 6 dias anteriores, em ordem crescente."""
    hoje = date.today()
    return [hoje - timedelta(days=i) for i in range(6, -1, -1)]

def _empty_ultimos_7d() -> list:
    return [
        {"dia": d.isoformat(), "entradas": 0.0, "saidas": 0.0, "saldo_dia": 0.0}
        for d in _ultimos_7d_dates()
    ]

def _ultimos_7d_from_ledger(db: Session, user_id: int) -> list:
    from app.models.pix_ledger import PixLedger

    dias = _ultimos_7d_dates()
    day_map = {
        d.isoformat(): {"dia": d.isoformat(), "entradas": 0.0, "saidas": 0.0, "saldo_dia": 0.0}
        for d in dias
    }

    rows = (
        db.query(PixLedger)
        .filter(PixLedger.user_id == user_id)
        .order_by(PixLedger.id.desc())
        .limit(500)
        .all()
    )

    for row in rows:
        dt = row.created_at
        if dt is None:
            continue
        dia = dt.date().isoformat()
        if dia not in day_map:
            continue
        amount = float(row.amount or 0)
        if row.kind == "credit":
            day_map[dia]["entradas"] += amount
        elif row.kind == "debit":
            day_map[dia]["saidas"] += amount

    ultimos_7d = [day_map[d.isoformat()] for d in dias]
    for item in ultimos_7d:
        item["saldo_dia"] = item["entradas"] - item["saidas"]
    return ultimos_7d

router = APIRouter(prefix="/api/v1/pix", tags=["pix"])

@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db),
    current_user = Depends(require_customer),
):
    try:
        from app.models.pix_ledger import PixLedger
        from sqlalchemy import func, case
        from decimal import Decimal

        result = (
            db.query(
                func.coalesce(
                    func.sum(
                        case(
                            (PixLedger.kind == "credit", PixLedger.amount),
                            else_=-PixLedger.amount,
                        )
                    ),
                    0,
                )
            )
            .filter(PixLedger.user_id == current_user.id)
            .scalar()
        )

        saldo = float(Decimal(result or 0))

        return {
            "saldo": saldo,
            "source": "real",
            "ultimos_7d": _ultimos_7d_from_ledger(db, current_user.id),
        }

    except Exception as e:
        print("[AUREA PIX] erro ao calcular saldo:", e)
        return {
            "saldo": 0.0,
            "source": "lab",
            "ultimos_7d": _empty_ultimos_7d(),
        }



@router.get("/history")
def get_history(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Retorna as últimas transações PIX do usuário autenticado."""

    try:
        user_id = getattr(current_user, "id", 1)

        txs = (
            db.query(PixTransaction)
            .filter(PixTransaction.user_id == user_id)
            .order_by(PixTransaction.id.desc())
            .limit(50)
            .all()
        )

        result = [
            {
                "id": t.id,
                "tipo": t.tipo,
                "valor": float(getattr(t, "valor", 0) or 0),
                "descricao": getattr(t, "descricao", None) or "",
                "taxa_percentual": float(getattr(t, "taxa_percentual", 0) or 0),
                "taxa_valor": float(getattr(t, "taxa_valor", 0) or 0),
                "valor_liquido": float(
                    getattr(t, "valor_liquido", getattr(t, "valor", 0)) or 0
                ),
                "criado_em": getattr(t, "created_at", None),
            }
            for t in txs
        ]


        return JSONResponse(
            content=jsonable_encoder(result, custom_encoder={Decimal: float})
        )
    except Exception as e:
        print("[AUREA PIX] erro ao carregar histórico:", e)
        return JSONResponse(content=[], status_code=200)

@router.get("/list")
def get_list(
    limit: int = 50,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Lista curta de movimentações PIX para home/painéis rápidos."""
    try:
        safe_limit = max(1, min(int(limit or 50), 100))

        txs = (
            db.query(PixTransaction)
            .filter(PixTransaction.user_id == current_user.id)
            .order_by(PixTransaction.id.desc())
            .limit(safe_limit)
            .all()
        )

        result = [
            {
                "id": t.id,
                "tipo": t.tipo,
                "valor": float(getattr(t, "valor", 0) or 0),
                "descricao": getattr(t, "descricao", None) or "",
                "taxa_percentual": float(getattr(t, "taxa_percentual", 0) or 0),
                "taxa_valor": float(getattr(t, "taxa_valor", 0) or 0),
                "valor_liquido": float(
                    getattr(t, "valor_liquido", getattr(t, "valor", 0)) or 0
                ),
                "created_at": getattr(t, "created_at", None),
            }
            for t in txs
        ]

        return JSONResponse(
            content=jsonable_encoder(result, custom_encoder={Decimal: float})
        )
    except Exception as e:
        print("[AUREA PIX] erro ao carregar lista PIX:", e)
        return JSONResponse(content=[], status_code=200)

@router.get("/forecast")
def get_forecast(
    db: Session = Depends(get_db),
    current_user = Depends(require_customer),
):
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
            .filter(PixTransaction.user_id == current_user.id)
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
        logger.exception("pix_forecast_failed")
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

from fastapi import Request, HTTPException
from time import perf_counter
from app.schemas.pix_send import (
    PixSendIntentAckRequest,
    PixSendIntentAckResponse,
    PixSendIntentRequest,
    PixSendIntentResponse,
    PixSendRequest,
    PixSendResponse,
)
from app.services.pix_send_intent_service import (
    PixSendIntentAckError,
    acknowledge_pix_send_intent,
    reserve_pix_send_intent,
)
from app.services.pix_service import send_pix
from app.core.rate_limit import Limiter
from app.core.observability import PIX_SEND_TOTAL, PIX_SEND_DURATION_SECONDS


@router.post("/send", response_model=PixSendResponse)
@limiter.limit("10/minute")
def post_pix_send(
    request: Request,
    body: PixSendRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_customer),
):
    start = perf_counter()
    outcome = "error"
    try:
        idempotency_key = request.headers.get("Idempotency-Key")

        result = send_pix(
            db=db,
            user_id=current_user.id,
            valor=body.valor,
            chave_pix=body.chave_pix,
            descricao=body.descricao or "PIX",
            idempotency_key=idempotency_key,
        )        # Se vier dict, pode ser replay (200) ou conflito/in_progress (409)
        if isinstance(result, dict):
            code = result.get("code")

            # conflito / em processamento
            if code in ("IDEMPOTENCY_KEY_REUSE_DIFFERENT_PAYLOAD", "IDEMPOTENCY_IN_PROGRESS"):
                outcome = "error"
                return JSONResponse(
                    content=jsonable_encoder(result, custom_encoder={Decimal: float}),
                    status_code=409,
                )

            # replay concluído (não aplicar response_model aqui)
            outcome = "replay"
            return JSONResponse(
                content=jsonable_encoder(result, custom_encoder={Decimal: float}),
                status_code=200,
                headers={"X-Idempotency-Replayed": "true"},
            )

        outcome = "success"
        return PixSendResponse(
            id=result.id,
            valor=result.valor,
            taxa_percentual=result.taxa_percentual,
            taxa_valor=result.taxa_valor,
            valor_liquido=result.valor_liquido,
            status="success",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("pix_send_failed")
        raise HTTPException(status_code=500, detail="Erro interno ao enviar PIX")
    finally:
        dur = perf_counter() - start
        try:
            PIX_SEND_TOTAL.labels(outcome=outcome).inc()
            PIX_SEND_DURATION_SECONDS.labels(outcome=outcome).observe(dur)
        except Exception:
            pass


@router.post("/send/intent", response_model=PixSendIntentResponse)
@limiter.limit("10/minute")
def post_pix_send_intent(
    request: Request,
    body: PixSendIntentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_customer),
):
    """
    Reserva/recupera/renova a intent server-side de um envio PIX (M2).

    Nunca recebe user_id/fingerprint do chamador: o usuário vem sempre de
    current_user (JWT verificado) e o fingerprint é recalculado aqui a
    partir do payload já validado por este schema — nunca do JSON cru.

    Ver backend/app/services/pix_send_intent_service.py para o contrato
    completo (fail-closed em toda ambiguidade; nunca gera uma segunda
    send_key enquanto a intent anterior estiver pending).
    """
    try:
        result = reserve_pix_send_intent(
            db=db,
            user_id=current_user.id,
            valor=body.valor,
            chave_pix=body.chave_pix,
            descricao=body.descricao or "PIX",
            force_new=body.force_new,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if result.get("force_new_rejected"):
        return JSONResponse(
            content=jsonable_encoder(result),
            status_code=409,
        )

    return result


@router.post("/send/intent/ack", response_model=PixSendIntentAckResponse)
@limiter.limit("10/minute")
def post_pix_send_intent_ack(
    request: Request,
    body: PixSendIntentAckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_customer),
):
    """
    Confirma (ack) que a send_key da intent atual foi genuinamente
    processada com sucesso — verificado sempre server-side contra o
    mecanismo real de idempotência do PIX (`pix-send:`), nunca contra a
    alegação do chamador de que "recebeu 200". Idempotente: chamar de
    novo uma intent já acknowledged não falha.
    """
    try:
        result = acknowledge_pix_send_intent(
            db=db,
            user_id=current_user.id,
            send_key=body.send_key,
        )
    except PixSendIntentAckError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return result

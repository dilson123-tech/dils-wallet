from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.pix_transaction import PixTransaction

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

class UserMessage(BaseModel):
    message: str
    user_id: int = 1

class AIResponse(BaseModel):
    answer: str
    saldo_atual: float | None = None
    resumo_pix: dict | None = None

def get_pix_context(db: Session, user_id: int):
    """
    Busca todas as transações PIX do usuário, calcula saldo e gera resumo.
    """
    txs = (
        db.query(PixTransaction)
        .filter(PixTransaction.user_id == user_id)
        .order_by(PixTransaction.id.desc())
        .all()
    )

    saldo = 0.0
    enviados_total = 0.0
    recebidos_total = 0.0
    ultimas_transacoes = []

    for t in txs:
        valor = float(t.valor)
        if t.tipo == "entrada":
            saldo += valor
            recebidos_total += valor
        else:
            saldo -= valor
            enviados_total += valor

        ultimas_transacoes.append({
            "id": t.id,
            "tipo": t.tipo,
            "valor": valor,
            "descricao": t.descricao,
            "timestamp": getattr(t, "timestamp", None)
        })

    resumo = {
        "saldo_atual": round(saldo, 2),
        "total_enviado": round(enviados_total, 2),
        "total_recebido": round(recebidos_total, 2),
        "qtd_transacoes": len(txs),
        "ultimas_transacoes": ultimas_transacoes[:5],
    }

    return resumo

@router.post("/chat", response_model=AIResponse)
def chat_with_ai(body: UserMessage, db: Session = Depends(get_db)):
    """
    VERSÃO MOCK / OFFLINE
    - Não chama OpenAI.
    - Gera resposta sozinha usando o histórico PIX.
    - Serve pra ativar Aurea IA 3.0 no front mesmo sem chave.
    """

    try:
        contexto_pix = get_pix_context(db, body.user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar contexto PIX: {e}"
        )

    saldo = contexto_pix["saldo_atual"]
    total_enviado = contexto_pix["total_enviado"]
    total_recebido = contexto_pix["total_recebido"]
    qtd = contexto_pix["qtd_transacoes"]

    resposta_ia = (
        f"Análise financeira Aurea IA 3.0 ✅\n\n"
        f"Saldo atual disponível via PIX: R$ {saldo:.2f}.\n"
        f"Total recebido: R$ {total_recebido:.2f}.\n"
        f"Total enviado: R$ {total_enviado:.2f}.\n"
        f"Movimentações registradas: {qtd}.\n\n"
        f"Pergunta do usuário: \"{body.message}\"\n\n"
        f"Visão: você está ok, mas monitora os envios. "
        f"Se quiser, posso projetar gasto médio diário e avisar quando você exagerar."
    )

    return AIResponse(
        answer=resposta_ia,
        saldo_atual=saldo,
        resumo_pix=contexto_pix,
    )

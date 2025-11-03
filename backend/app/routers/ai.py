from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

class ChatRequest(BaseModel):
    message: str
    user_id: int | None = None

class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(req: ChatRequest):
    msg = req.message.lower().strip()

    if "resumo" in msg or "hoje" in msg:
        return {"reply": "Seu saldo atual é R$ 490,00, com 20 transações no histórico. Nenhuma entrada nas últimas 24h."}
    elif "saldo" in msg:
        return {"reply": "Você tem R$ 490,00 disponíveis em conta PIX."}
    elif "entradas" in msg:
        return {"reply": "Entradas totais: R$ 1.400,50 nas últimas transações."}
    elif "saídas" in msg or "gastos" in msg:
        return {"reply": "Saídas totais até agora: R$ 910,50, sendo R$ 0,00 nas últimas 24h."}
    else:
        return {"reply": "Posso te ajudar com saldo, entradas, saídas ou resumo do dia."}

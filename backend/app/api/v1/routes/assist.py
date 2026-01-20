from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

class Ask(BaseModel):
    msg: str
    user_id: int | None = None

@router.post("/assist")
def assist(a: Ask):
    # stub: aqui plugaremos o provedor da IA 3.0
    return {
        "reply": f"Recebi: {a.msg}. Em breve, IA 3.0 com contexto financeiro.",
        "suggestions": ["Ver extrato", "Resumo de gastos", "Enviar PIX"]
    }

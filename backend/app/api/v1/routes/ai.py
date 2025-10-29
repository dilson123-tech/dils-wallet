from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from openai import AsyncOpenAI

router = APIRouter(prefix="/ai", tags=["ai"])

# ============ Configuração OpenAI ============
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

# ============ Schemas ============
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# ============ Função principal ============
async def call_openai(message: str) -> str:
    """Chama o modelo GPT real (IA 3.0 do Aurea Bank)"""
    try:
        completion = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é a Aurea IA 3.0, assistente bancária premium do Aurea Bank. "
                        "Responda de forma clara, cordial e profissional, com foco em finanças, PIX e suporte ao cliente. "
                        "Não use emojis. Seja concisa e empática, estilo concierge de banco de luxo."
                    ),
                },
                {"role": "user", "content": message},
            ],
            temperature=0.4,
            max_tokens=400,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao chamar OpenAI: {e}")

# ============ Endpoint ============
@router.post("/chat", response_model=ChatResponse)
async def chat_ai(body: ChatRequest):
    """Endpoint público usado pelo front AureaAssistant"""
    try:
        resposta = await call_openai(body.message)
        return ChatResponse(reply=resposta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

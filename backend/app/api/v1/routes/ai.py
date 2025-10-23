import os
import openai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["AI 2.0"])
MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# configura cliente no estilo legacy (compatível com todas versões)
openai.api_key = os.getenv("OPENAI_API_KEY")
if os.getenv("OPENAI_API_BASE"):
    openai.api_base = os.getenv("OPENAI_API_BASE")

class PromptIn(BaseModel):
    prompt: str

@router.get("/ping")
def ai_ping():
    if not openai.api_key:
        raise HTTPException(status_code=503, detail="IA desativada: defina OPENAI_API_KEY no Railway.")
    return {"status": "ok", "model": MODEL_DEFAULT}

@router.post("/process")
def ai_process(body: PromptIn):
    if not openai.api_key:
        raise HTTPException(status_code=503, detail="IA desativada: defina OPENAI_API_KEY no Railway.")
    try:
        response = openai.ChatCompletion.create(
            model=MODEL_DEFAULT,
            messages=[{"role": "user", "content": body.prompt}],
            temperature=0.4,
            max_tokens=120,
        )
        text = response.choices[0].message["content"].strip()
        return {"response": text}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI error: {e}")

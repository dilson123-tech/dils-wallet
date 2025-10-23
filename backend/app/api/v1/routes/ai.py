import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter(tags=["AI 2.0"])
MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class PromptIn(BaseModel):
    prompt: str

def _client():
    # precisa da key
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="IA desativada: defina OPENAI_API_KEY no Railway.")
    # compat: se usou OPENAI_API_BASE, mapeia para o env esperado pelo SDK
    if os.getenv("OPENAI_API_BASE") and not os.getenv("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = os.getenv("OPENAI_API_BASE")
    # usa apenas envs; evita kwargs que geram conflito (ex.: proxies)
    return OpenAI()

@router.get("/ping")
def ai_ping():
    try:
        _ = _client()
        return {"status": "ok", "model": MODEL_DEFAULT}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI ping error: {e}")

@router.post("/process")
def ai_process(body: PromptIn):
    try:
        client = _client()
        resp = client.chat.completions.create(
            model=MODEL_DEFAULT,
            messages=[{"role": "user", "content": body.prompt}],
            temperature=0.4,
            max_tokens=120,
        )
        return {"response": resp.choices[0].message.content.strip()}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI error: {e}")

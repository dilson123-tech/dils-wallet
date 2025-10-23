import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter(tags=["AI 2.0"])
MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class PromptIn(BaseModel):
    prompt: str

def _client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="IA desativada: defina OPENAI_API_KEY no Railway.")
    return OpenAI(api_key=api_key)  # sem proxies/base/org/etc

@router.get("/ping")
def ai_ping():
    try:
        _ = _client()
        return {"status": "ok", "model": MODEL_DEFAULT}
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
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI error: {e}")

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
    base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    org  = os.getenv("OPENAI_ORG_ID") or None
    proj = os.getenv("OPENAI_PROJECT_ID") or None
    # Constrói cliente compatível com chaves sk-proj- (projeto)
    return OpenAI(api_key=api_key, base_url=base, organization=org, project=proj)

@router.get("/ping")
def ai_ping():
    try:
        _ = _client()  # só valida credenciais
        return {"status": "ok", "model": MODEL_DEFAULT}
    except HTTPException as he:
        # passa o erro como veio
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
        text = resp.choices[0].message.content.strip()
        return {"response": text}
    except HTTPException as he:
        raise he
    except Exception as e:
        # devolve JSON SEMPRE
        raise HTTPException(status_code=502, detail=f"AI error: {e}")

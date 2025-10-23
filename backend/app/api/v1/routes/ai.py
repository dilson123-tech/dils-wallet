import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# OpenAI SDK v1.x
from openai import OpenAI

router = APIRouter(tags=["AI 2.0"])

MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class PromptIn(BaseModel):
    prompt: str

@router.post("/process")
def ai_process(body: PromptIn):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"response": "IA desativada: defina OPENAI_API_KEY no Railway para habilitar."}

    base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    client = OpenAI(api_key=api_key, base_url=base)

    try:
        resp = client.chat.completions.create(
            model=MODEL_DEFAULT,
            messages=[{"role": "user", "content": body.prompt}],
            temperature=0.4,
            max_tokens=120,
        )
        text = resp.choices[0].message.content.strip()
        return {"response": text}
    except Exception as e:
        # manda erro pro cliente de forma legível
        raise HTTPException(status_code=500, detail=f"AI error: {e}")

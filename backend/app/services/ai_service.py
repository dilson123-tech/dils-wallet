from __future__ import annotations
import os
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # evita quebrar se a lib não estiver instalada no primeiro run
    OpenAI = None  # type: ignore

MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class AIUnavailable(RuntimeError):
    ...

async def generate_ai_response(prompt: str, user_id: Optional[str] = None) -> str:
    """
    Retorna texto de IA. Se OPENAI_API_KEY não existir, informa que a IA está desativada.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return "IA desativada: defina OPENAI_API_KEY no Railway para habilitar."

    client = OpenAI(api_key=api_key)

    # conversa mínima; ajuste system conforme sua persona
    msgs = [
        {"role": "system", "content": "Você é o assistente Aurea 2.0. Responda curto e prático."},
        {"role": "user",   "content": prompt.strip()},
    ]

    try:
        resp = client.chat.completions.create(model=MODEL_DEFAULT, messages=msgs, temperature=0.4, max_tokens=300)
        text = (resp.choices[0].message.content or "").strip()
        return text or "Sem conteúdo."
    except Exception as e:
        # Nunca vaze stack para o cliente
        return f"Falha ao processar IA: {type(e).__name__}"

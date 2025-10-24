import os
from openai import OpenAI
from app.services.ai_guardrails import aurea_system_prompt

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=_OPENAI_API_KEY, base_url=_OPENAI_API_BASE)

def chat(prompt: str, system: str | None = None, temperature: float = 0.2, max_tokens: int | None = 300):
    sys = system or aurea_system_prompt()
    resp = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content

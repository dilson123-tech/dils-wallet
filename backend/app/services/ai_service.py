import os
from openai import OpenAI

MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def get_ai_text(prompt: str) -> str:
    """
    Retorna resposta da IA Aurea Bank 2.0 via OpenAI.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "IA desativada: defina OPENAI_API_KEY no Railway para habilitar."

    # Cliente limpo — sem proxies/base/org extras
    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model=MODEL_DEFAULT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=200,
    )

    return resp.choices[0].message.content.strip()

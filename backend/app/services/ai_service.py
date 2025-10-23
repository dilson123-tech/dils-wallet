import os
from openai import OpenAI

MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def get_ai_text(prompt: str) -> str:
    """
    Retorna texto da IA. Se OPENAI_API_KEY não existir, informa que a IA está desativada.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "IA desativada: defina OPENAI_API_KEY no Railway para habilitar."

    client = OpenAI(api_key=api_key)  # sem proxies/base/org/etc
    resp = client.chat.completions.create(
        model=MODEL_DEFAULT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()

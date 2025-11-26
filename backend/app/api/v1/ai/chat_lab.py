from fastapi import APIRouter, Header
from pydantic import BaseModel
from datetime import datetime
import httpx

router = APIRouter()


class ChatPayload(BaseModel):
    message: str


"""
IA 3.0 Premium — versão LAB
-----------------------------------------
Camada inteligente que organiza a resposta em três níveis:

1) Interpretação do pedido
2) Busca de dados reais (saldo, histórico, entradas, saídas)
3) Resposta Aurea Gold Premium estruturada

Essa versão é 100% segura. Não altera nada do painel.
Só observa e responde melhor.
"""


async def fetch_backend_data(user_email: str, tipo: str):
    base = "http://127.0.0.1:8000"

    endpoints = {
        "saldo": "/api/v1/pix/balance",
        "entradas_mes": "/api/v1/pix/balance",
        "saidas_mes": "/api/v1/pix/balance",
        "historico": "/api/v1/pix/history",
    }

    url = base + endpoints[tipo]

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers={"X-User-Email": user_email})
        r.raise_for_status()
        return r.json()


def classify_intent(msg: str) -> str:
    txt = msg.lower()

    if "saldo" in txt:
        return "saldo"
    if "entradas" in txt:
        return "entradas_mes"
    if "saídas" in txt or "saidas" in txt:
        return "saidas_mes"
    if "histórico" in txt or "historico" in txt:
        return "historico"

    return "geral"


def format_response(intent: str, data: dict, msg: str) -> str:
    agora = datetime.now().strftime("%d/%m %H:%M")

    # Bloco 1: interpretação
    interpretacao = f"🧠 *Interpretação*: você pediu **{msg.lower()}**.\n"

    if intent == "saldo":
        valor = data.get("saldo_atual", data.get("saldo", 0))
        corpo = f"💰 *Saldo atual*: **R$ {valor:.2f}**.\n"
        resumo = "📌 *Resumo*: seu saldo está sincronizado com o painel Aurea Gold."
        return f"🟡 **IA 3.0 Premium** — {agora}\n{interpretacao}{corpo}{resumo}"

    if intent == "entradas_mes":
        ent = data.get("entradas_mes", 0)
        corpo = f"📥 *Entradas no mês*: **R$ {ent:.2f}**.\n"
        resumo = "📌 *Resumo*: suas entradas foram analisadas com base no extrato Pix."
        return f"🟡 **IA 3.0 Premium** — {agora}\n{interpretacao}{corpo}{resumo}"

    if intent == "saidas_mes":
        sai = data.get("saidas_mes", 0)
        corpo = f"📤 *Saídas no mês*: **R$ {sai:.2f}**.\n"
        resumo = "📌 *Resumo*: suas saídas foram processadas pela IA 3.0."
        return f"🟡 **IA 3.0 Premium** — {agora}\n{interpretacao}{corpo}{resumo}"

    if intent == "historico":
        qtd = len(data.get("historico", []))
        corpo = f"📘 *Operações no histórico*: **{qtd}**.\n"
        resumo = "📌 *Resumo*: histórico verificado e estruturado automaticamente."
        return f"🟡 **IA 3.0 Premium** — {agora}\n{interpretacao}{corpo}{resumo}"

    return (
        "✨ IA 3.0 Premium\n"
        "Entendi sua pergunta, mas ela envolve algo mais geral.\n"
        "Pode pedir saldo, entradas, saídas ou histórico."
    )


@router.post("/chat_lab")
async def chat_lab(payload: ChatPayload, x_user_email: str = Header(None)):
    msg = payload.message

    intent = classify_intent(msg)

    if intent == "geral":
        return {
            "reply": "Entendi, mas preciso de algo específico: saldo, entradas, saídas ou histórico."
        }

    data = await fetch_backend_data(x_user_email, intent)
    reply = format_response(intent, data, msg)

    return {"reply": reply}

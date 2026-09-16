from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import httpx

from app.core.rate_limit import limiter


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
        "saldo": "/api/v1/pix/balance?days=7",
        "entradas_mes": "/api/v1/pix/balance?days=7",
        "saidas_mes": "/api/v1/pix/balance?days=7",
        "historico": "/api/v1/pix/history",
        "saude_financeira": "/api/v1/pix/balance?days=7",
    }

    url = base + endpoints[tipo]

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers={"X-User-Email": user_email})
        r.raise_for_status()
        return r.json()

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

    if (
        "saúde financeira" in txt
        or "saude financeira" in txt
        or "como estou financeiramente" in txt
        or "minha situação financeira" in txt
        or "minha situacao financeira" in txt
    ):
        return "saude_financeira"

    if "saldo" in txt:
        return "saldo"
    if "entradas" in txt:
        return "entradas_mes"
    if "saídas" in txt or "saidas" in txt:
        return "saidas_mes"
    if "histórico" in txt or "historico" in txt:
        return "historico"

    return "geral"

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
    """
    Gera a resposta de texto da IA 3.0 Premium, já formatada para o front.
    """
    agora = datetime.now().strftime("%d/%m %H:%M")
    interpretacao = f"🧠 *Interpretação*: você pediu **{msg.lower()}**.\n"

    if intent == "saldo":
        valor = data.get("saldo_atual", data.get("saldo", 0.0)) or 0.0
        valor_fmt = f"{valor:.2f}".replace(".", ",")
        corpo = f"💰 *Saldo atual*: **R$ {valor_fmt}**.\n"
        resumo = "📌 *Resumo*: seu saldo está sincronizado com o painel Aurea Gold."
        return (
            f"🟡 **IA 3.0 Premium** — {agora}\n"
            f"{interpretacao}{corpo}{resumo}"
        )

        ent_fmt = f"{ent:.2f}".replace(".", ",")
        corpo = f"📥 *Entradas no mês*: **R$ {ent_fmt}**.\n"
        ent = data.get("entradas_mes", data.get("entradas", 0.0)) or 0.0
        corpo = f"�� *Entradas no mês*: **R$ {ent:.2f}**.\n"
        resumo = "📌 *Resumo*: suas entradas foram analisadas com base no extrato Pix."
        return (
            f"🟡 **IA 3.0 Premium** — {agora}\n"
            f"{interpretacao}{corpo}{resumo}"
        )
        sai_fmt = f"{sai:.2f}".replace(".", ",")
        corpo = f"📤 *Saídas no mês*: **R$ {sai_fmt}**.\n"
    if intent == "saidas_mes":
        sai = data.get("saidas_mes", data.get("saidas", 0.0)) or 0.0
        corpo = f"📤 *Saídas no mês*: **R$ {sai:.2f}**.\n"
        resumo = "📌 *Resumo*: suas saídas foram processadas pela IA 3.0."
        return (
            f"🟡 **IA 3.0 Premium** — {agora}\n"
            f"{interpretacao}{corpo}{resumo}"
        )

    if intent == "historico":
        qtd = len(data.get("historico", []))
        corpo = f"📘 *Operações no histórico*: **{qtd}**.\n"
        resumo = "📌 *Resumo*: histórico verificado e estruturado automaticamente."
        return (
            f"🟡 **IA 3.0 Premium** — {agora}\n"
            f"{interpretacao}{corpo}{resumo}"
        )

    if intent == "saude_financeira":
        saldo = data.get("saldo_atual", data.get("saldo", 0.0)) or 0.0
        entradas = data.get("entradas_mes", data.get("entradas", 0.0)) or 0.0
        saidas = data.get("saidas_mes", data.get("saidas", 0.0)) or 0.0
        net = entradas - saidas

        if saldo < 0 and net <= 0:
            diagnostico = "⚠️ Sua saúde financeira está sensível: saldo negativo e mais saídas que entradas."
            dica = "Priorize reduzir gastos e evitar novos envios de PIX até normalizar."
        elif saldo >= 0 and net < 0:
            diagnostico = "🟠 Você está no positivo, mas gastando mais do que entra."
            dica = "Vale revisar despesas para não escorregar pro vermelho."
        elif saldo >= 0 and net >= 0:
            diagnostico = "🟢 Saúde financeira estável: mais entradas que saídas."
            dica = "Considere formar reserva."
        else:
            diagnostico = "ℹ️ Situação financeira mista, vale olhar o extrato com calma."
            dica = "Use o painel Aurea Gold para acompanhar mais de perto."

        corpo = f"{diagnostico}\n💡 Dica da IA: {dica}\n"
        resumo = "📌 *Resumo*: análise automática feita com base em saldo, entradas e saídas."

        return (
            f"🟡 **IA 3.0 Premium** — {agora}\n"
            f"{interpretacao}{corpo}{resumo}"
        )

    # fallback geral
    corpo = "ℹ️ Não identifiquei um pedido específico de saldo, entradas, saídas ou histórico."
    resumo = (
        "📌 *Resumo*: tente perguntar algo como "
        "'meu saldo hoje', 'entradas do mês', 'saídas do mês' ou 'meu histórico Pix'."
    )
    return (
        f"🟡 **IA 3.0 Premium** — {agora}\n"
        f"{interpretacao}{corpo}\n{resumo}"
    )

@router.post("/chat_lab")
@limiter.limit("30/minute")
async def chat_lab(request: Request, payload: ChatPayload, x_user_email: str = Header(None)):
    """
    Endpoint LAB da IA 3.0 Premium.
    Não altera nada no painel oficial, só lê dados reais e responde melhor.
    """
    msg = payload.message.strip()
    intent = classify_intent(msg)

    # Caso seja algo muito genérico, não bate no backend,
    # só orienta o usuário sobre o que a IA 3.0 sabe fazer.
    if intent == "geral":
        reply = (
            "✨ IA 3.0 Premium\n"
            "Entendi sua pergunta, mas ela envolve algo mais geral.\n"
            "Pode pedir saldo, entradas, saídas, histórico ou saúde financeira."
        )
        return {"reply": reply, "intent": intent}

    if not x_user_email:
        raise HTTPException(status_code=400, detail="X-User-Email header is required")

    # Busca dados reais no backend PIX (saldo, entradas, saídas, histórico)
    data = await fetch_backend_data(x_user_email, intent)

    # Monta resposta Premium organizada
    reply = format_response(intent, data, msg)

    return {"reply": reply, "intent": intent}

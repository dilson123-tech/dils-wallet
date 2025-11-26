from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
from urllib import request, error as urlerror  # noqa: F401

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["ai"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def _normalize(text: str) -> str:
    """
    Normaliza o texto para facilitar a detecção de palavras-chave.
    Remove diferenças simples de acentuação.
    """
    t = text.lower()
    replacements = {
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for k, v in replacements.items():
        t = t.replace(k, v)
    return t


def _fmt_brl(v: Optional[float]) -> str:
    if v is None:
        return "R$ 0,00"
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "R$ 0,00"
    return ("R$ " + f"{n:.2f}").replace(".", ",")


async def _fetch_internal_json(
    path: str, x_user_email: Optional[str]
) -> Optional[dict]:
    """
    Faz uma chamada interna para a própria API (localhost:8000),
    reaproveitando toda a lógica já existente de PIX.
    Em caso de erro, retorna None sem derrubar a IA.
    """
    url = f"http://127.0.0.1:8000{path}"
    headers = {"Content-Type": "application/json"}
    if x_user_email:
        headers["X-User-Email"] = x_user_email

    req = request.Request(url, headers=headers, method="GET")

    loop = asyncio.get_running_loop()

    def _do_request() -> Optional[dict]:
        try:
            with request.urlopen(req, timeout=2.5) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw)
        except Exception:
            return None

    return await loop.run_in_executor(None, _do_request)


async def _get_pix_balance(
    x_user_email: Optional[str],
) -> Optional[dict]:
    return await _fetch_internal_json("/api/v1/pix/balance?days=7", x_user_email)


async def _get_pix_history(
    x_user_email: Optional[str],
) -> Optional[list]:
    data = await _fetch_internal_json("/api/v1/pix/history", x_user_email)
    if isinstance(data, list):
        return data
    # alguns formatos podem vir como {"items": [...]}
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return items
    return None


def _build_saldo_reply(balance: dict) -> str:
    saldo = _fmt_brl(balance.get("saldo_atual"))
    ent = _fmt_brl(balance.get("entradas_mes"))
    sai = _fmt_brl(balance.get("saidas_mes"))

    return (
        "📌 Visão geral do seu saldo atual\n\n"
        f"- Saldo disponível agora: {saldo}\n"
        f"- Entradas no mês: {ent}\n"
        f"- Saídas no mês: {sai}\n\n"
        "Isso é exatamente o que o painel Super2 mostra no topo: o valor real que "
        "você tem para usar, já considerando as movimentações recentes."
    )


def _build_entradas_reply(balance: dict) -> str:
    ent = _fmt_brl(balance.get("entradas_mes"))
    return (
        "📥 Entradas do mês\n\n"
        f"- Total de entradas no mês: {ent}\n\n"
        "Essas entradas somam tudo o que entrou via PIX e outros créditos. No painel, "
        "você enxerga esse número junto com o saldo para saber se está em modo de "
        "acumular ou só manter a conta rodando."
    )


def _build_saidas_reply(balance: dict) -> str:
    sai = _fmt_brl(balance.get("saidas_mes"))
    return (
        "📤 Saídas do mês\n\n"
        f"- Total de saídas no mês: {sai}\n\n"
        "As saídas representam pagamentos, transferências e débitos gerais. Comparar "
        "entradas x saídas ajuda a ver se o mês está mais saudável ou se é hora de "
        "pisar no freio em alguns gastos."
    )


def _build_history_reply(history: list) -> str:
    if not history:
        return (
            "Neste momento não encontrei movimentações recentes de PIX para montar "
            "um histórico. Assim que novas entradas ou saídas acontecerem, esse "
            "resumo passa a ficar mais interessante."
        )

    total_envios = 0.0
    total_recebidos = 0.0
    for item in history:
        tipo = str(item.get("tipo", "")).lower()
        try:
            valor = float(item.get("valor") or 0)
        except (TypeError, ValueError):
            valor = 0.0
        if "env" in tipo:
            total_envios += valor
        elif "rec" in tipo or "ent" in tipo:
            total_recebidos += valor

    resumo_env = _fmt_brl(total_envios)
    resumo_rec = _fmt_brl(total_recebidos)

    return (
        "📑 Resumo recente de PIX\n\n"
        f"- Total aproximado enviado: {resumo_env}\n"
        f"- Total aproximado recebido: {resumo_rec}\n\n"
        "Esse é um resumo simplificado. No painel Super2 você consegue ver o gráfico "
        "dos últimos dias e, em versões futuras, a IA 3.0 vai cruzar esse histórico "
        "com a sua rotina para sugerir alertas e oportunidades."
    )


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    payload: ChatRequest,
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
):
    """
    IA 3.0 da Aurea Gold — versão Premium com explicação organizada
    e, sempre que possível, usando dados reais de PIX do próprio painel.
    """

    raw_msg = payload.message.strip()
    norm_msg = _normalize(raw_msg)

    user_hint = (
        f"\n\nAtendo você usando o cadastro: {x_user_email}."
        if x_user_email
        else ""
    )

    intro = (
        "Olá! Eu sou a IA 3.0 da Aurea Gold.\n\n"
        "Estou aqui para te ajudar com saldos, PIX, movimentações e dúvidas do dia a dia, "
        "sempre de um jeito simples e direto.\n"
    )

    tema_reply: str
    tema_label: str = "sua dúvida"

    # tenta carregar dados de PIX só quando for relevante
    balance: Optional[dict] = None
    history: Optional[list] = None

    if any(p in norm_msg for p in ["saldo", "quanto tenho", "quanto eu tenho"]):
        tema_label = "saldo"
        balance = await _get_pix_balance(x_user_email)
        if balance:
            tema_reply = _build_saldo_reply(balance)
        else:
            tema_reply = (
                "Você quer entender melhor o saldo.\n\n"
                "No painel Super2, o saldo do topo já considera as movimentações "
                "mais recentes e mostra quanto você tem disponível agora para usar.\n\n"
                "Se o sistema não conseguiu carregar os dados neste momento, tente "
                "atualizar a página ou verificar a conexão."
            )

    elif any(p in norm_msg for p in ["entrada", "entradas", "receb", "ganho", "ganhos"]):
        tema_label = "entradas"
        balance = await _get_pix_balance(x_user_email)
        if balance:
            tema_reply = _build_entradas_reply(balance)
        else:
            tema_reply = (
                "Você perguntou sobre as entradas.\n\n"
                "As entradas somam tudo o que entrou na sua conta via PIX e outros créditos. "
                "No painel Super2, o campo 'Entradas (Mês)' mostra esse total. "
                "Se os dados não estiverem disponíveis agora, tente recarregar o painel."
            )

    elif any(p in norm_msg for p in ["saida", "saidas", "gasto", "gastos", "paguei", "pagamento"]):
        tema_label = "saídas"
        balance = await _get_pix_balance(x_user_email)
        if balance:
            tema_reply = _build_saidas_reply(balance)
        else:
            tema_reply = (
                "Você perguntou sobre as saídas.\n\n"
                "As saídas são todos os valores que saíram da sua conta: pagamentos, transferências "
                "e outros débitos. No painel Super2, o campo 'Saídas (Mês)' concentra esse número.\n\n"
                "Se os dados não carregarem agora, vale tentar novamente em alguns instantes."
            )

    elif any(p in norm_msg for p in ["historico", "historico pix", "ultimas movimentacoes", "movimentacao"]):
        tema_label = "histórico de PIX"
        history = await _get_pix_history(x_user_email)
        tema_reply = _build_history_reply(history or [])

    elif "pix" in norm_msg:
        tema_label = "PIX"
        tema_reply = (
            "Você quer saber mais sobre o PIX na Aurea Gold.\n\n"
            "O PIX é o meio mais rápido para enviar e receber valores. Pelo painel Super2, "
            "o botão 'Enviar PIX' é o atalho direto para iniciar uma transferência.\n\n"
            "A ideia da IA 3.0 é, no futuro, acompanhar essas operações em tempo real, "
            "te avisando de movimentos importantes e ajudando a evitar erros."
        )

    elif any(p in norm_msg for p in ["emprestimo", "cartao", "credito", "debito"]):
        tema_label = "produtos financeiros (cartão / empréstimo)"
        tema_reply = (
            "Você mencionou produtos como cartão ou empréstimo.\n\n"
            "Essas áreas ainda não estão habilitadas no Aurea Gold, mas fazem parte da visão "
            "de futuro da plataforma.\n\n"
            "Por enquanto, posso te ajudar principalmente com saldo, entradas, saídas, histórico "
            "e uso do PIX dentro do painel."
        )

    else:
        tema_reply = (
            "Você fez uma pergunta mais geral.\n\n"
            "Nesta versão, eu respondo melhor sobre temas como saldo, entradas, saídas, "
            "histórico PIX e funcionamento básico do painel Aurea Gold.\n\n"
            "Se quiser, pode tentar reformular a pergunta citando um desses pontos, e eu te "
            "entrego uma explicação mais direta."
        )

    resumo_final = f"\n\nResumo rápido: estou te ajudando agora com {tema_label}."

    final_reply = (
        f"{intro}"
        f"Você perguntou: \"{raw_msg}\".\n\n"
        f"{tema_reply}"
        f"{resumo_final}"
        f"{user_hint}"
    )

    return ChatResponse(reply=final_reply)

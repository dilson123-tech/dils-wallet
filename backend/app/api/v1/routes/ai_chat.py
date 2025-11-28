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

    # IA 3.0 – resumo do mês no PIX / consultor financeiro
    if any(
        frase in norm_msg
        for frase in [
            "resumo do mês",
            "resumo do mes",
            "fechamento do mês",
            "fechamento do mes",
            "balanço do mês",
            "balanco do mes",
            "como foi meu mês",
            "como foi meu mes no pix",
        ]
    ):
        if not x_user_email:
            return {
                "reply": (
                    "✨ IA 3.0 Premium – Resumo do mês no PIX\n\n"

                    "Para montar o resumo do mês, preciso que o app envie o header "
                    "X-User-Email com o seu e-mail Aurea Gold."
                )
            }

        balance = await _get_pix_balance(x_user_email)
        balance = await _get_pix_balance(x_user_email)
        _reply = _ia3_build_consulting_reply(balance)
        return {"reply": _reply}

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

    # IA 3.0 – Modo consultor financeiro focado em PIX (usa resumo do mês)
    elif any(
        p in norm_msg
        for p in [
            "o que voce me recomenda fazer com meu pix",
            "o que voce recomenda fazer com meu pix",
            "o que me recomenda fazer com meu pix",
            "recomenda fazer com meu pix",
            "recomenda fazer com meu pix esse mes",
            "to gastando muito",
            "to gastando muito no pix",
            "tô gastando muito",
            "estou gastando muito",
            "estou gastando muito no pix",
            "planejar meu pix esse mes",
            "organizar meu pix esse mes",
            "resumo do mes no pix",
            "resumo do meu pix",
            "me mostra um resumo do mes no pix",
            "faz um resumo do meu pix",
            "faz um resumo do mes no pix",
            "faz um resumo do mes do pix",
            "faz um resumo dos pix deste mes",
        ]
    ):
        tema_label = "modo consultor financeiro"
        balance = await _get_pix_balance(x_user_email)
        tema_reply = _ia3_build_consulting_reply(balance)

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

    # IA 3.0 – modo consultor financeiro no PIX (usa resumo do mês)
    elif any(
        p in norm_msg
        for p in [
            "recomenda fazer com meu pix",
            "recomenda fazer com meu pix esse mes",
            "o que recomendas fazer com meu pix",
            "to gastando muito",
            "to gastando muito no pix",
            "estou gastando muito",
            "estou gastando muito no pix",
            "planejar meu pix esse mes",
            "organizar meu pix esse mes",
            "resumo do mes no pix",
            "resumo do mês no pix",
            "me mostra um resumo do mes no pix",
        ]
    ):
        tema_label = "modo consultor financeiro"
        balance = await _get_pix_balance(x_user_email)
        tema_reply = _ia3_build_consulting_reply(balance)

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


"""
Bloco de apoio para IA 3.0 – Resumo do mês no PIX

Este código não altera nenhuma rota existente.
Ele só acrescenta funções helper que podem ser chamadas
de dentro do endpoint de IA quando quisermos ativar
o "resumo do mês".
"""


def _ia3_get_month_range_now():
    """
    Retorna (início_do_mês, início_próximo_mês) em UTC
    para filtrar transações do mês atual.
    """
    from datetime import datetime

    hoje = datetime.utcnow()
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if hoje.month == 12:
        inicio_prox = hoje.replace(
            year=hoje.year + 1,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    else:
        inicio_prox = hoje.replace(
            month=hoje.month + 1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    return inicio_mes, inicio_prox


def _ia3_get_pix_month_summary(user_email: str) -> dict:
    """
    Versão definitiva e robusta do resumo do mês.

    Nunca deve derrubar a API:
    - Se não conseguir importar SessionLocal ou PixTransaction → retorna tudo 0.
    - Se a query der erro → retorna tudo 0.
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import func

    zeros = {
        "entradas_mes": 0.0,
        "saidas_mes": 0.0,
        "net_mes": 0.0,
        "qtd_transacoes": 0,
    }

    # Tenta importar SessionLocal em caminhos diferentes
    try:
        try:
            from app.db.session import SessionLocal  # se existir app/db/session.py
        except Exception:
            from app.database.session import SessionLocal  # fallback comum
    except Exception as e:
        print("IA3 resumo_mes: não consegui importar SessionLocal:", e)
        return zeros

    # Tenta importar PixTransaction em caminhos diferentes
    try:
        try:
            from app.models.pix_transaction import PixTransaction
        except Exception:
            from app.models.pix import PixTransaction
    except Exception as e:
        print("IA3 resumo_mes: não consegui importar PixTransaction:", e)
        return zeros

    inicio_mes, inicio_prox = _ia3_get_month_range_now()
    db: Session = SessionLocal()
    try:
        base_query = (
            db.query(
                PixTransaction.kind,
                func.sum(PixTransaction.amount).label("total"),
                func.count().label("qtd"),
            )
            .filter(
                PixTransaction.user_email == user_email,
                PixTransaction.created_at >= inicio_mes,
                PixTransaction.created_at < inicio_prox,
            )
            .group_by(PixTransaction.kind)
        )

        entradas = 0.0
        saidas = 0.0
        total_qtd = 0

        for row in base_query:
            kind = (row.kind or "").lower()
            valor = float(row.total or 0)
            qtd = int(row.qtd or 0)
            total_qtd += qtd

            if kind == "entrada":
                entradas += valor
            elif kind == "saida":
                saidas += valor

        net = entradas - saidas

        return {
            "entradas_mes": float(entradas),
            "saidas_mes": float(saidas),
            "net_mes": float(net),
            "qtd_transacoes": int(total_qtd),
        }
    except Exception as e:
        print("IA3 resumo_mes: erro ao consultar transações:", e)
        return zeros
    finally:
        db.close()



def _ia3_build_consulting_reply(balance: dict | None) -> str:
    """Monta a resposta da IA 3.0 em modo consultor financeiro PIX, com nível de risco do mês."""
    if not balance:
        return (
            "Olá! Eu sou a IA 3.0 da Aurea Gold.\n\n"
            "Para te ajudar como consultor financeiro no PIX, eu preciso enxergar o resumo do seu mês. "
            "Por enquanto não encontrei os dados de saldo, entradas e saídas.\n\n"
            "Tenta novamente em alguns instantes ou verifica se o painel Super2 está carregando os valores normalmente."
        )

    def _num(val) -> float:
        try:
            return float(val or 0)
        except Exception:
            return 0.0

    # Tentativas de campos que já usamos no saldo/entradas/saídas
    saldo_atual = _num(
        balance.get("saldo_atual")
        or balance.get("saldo")
        or balance.get("available")
    )
    entradas_mes = _num(
        balance.get("entradas_mes")
        or balance.get("total_entradas_mes")
        or balance.get("entradas")
    )
    saidas_mes = _num(
        balance.get("saidas_mes")
        or balance.get("total_saidas_mes")
        or balance.get("saidas")
    )
    resultado = entradas_mes - saidas_mes  # Entradas - Saídas

    def fmt_brl(v: float) -> str:
        # Formata em estilo brasileiro: R$ 9.015,99
        s = f"{v:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"

    # Classificação de risco do mês
    if resultado >= 0:
        nivel = "🟢 Nível tranquilo"
        comentario = (
            "Você fechou o mês no positivo ou muito próximo do equilíbrio. "
            "Do ponto de vista de PIX, sua relação entre entradas e saídas está saudável. "
            "Vale manter esse padrão, guardando uma parte das entradas como reserva."
        )
    elif resultado >= -1000:
        nivel = "🟡 Nível de atenção"
        comentario = (
            "Você está fechando o mês levemente no negativo via PIX. "
            "Não é um desastre, mas já indica que alguns gastos podem ser ajustados. "
            "Vale revisar PIX recorrentes, transferências por impulso e compras não essenciais."
        )
    else:
        nivel = "🔴 Alerta vermelho"
        comentario = (
            "Você está fechando o mês bem no negativo via PIX. "
            "Saiu muito mais do que entrou, o que tende a pressionar seu caixa nos próximos meses. "
            "Aqui é importante cortar gastos supérfluos, negociar contas maiores e, se possível, "
            "aumentar entradas (freelas, vendas, serviços)."
        )

    texto = (
        "Olá! Eu sou a IA 3.0 da Aurea Gold.\n\n"
        "Estou aqui para te ajudar com saldos, PIX, movimentações e dúvidas do dia a dia, sempre de um jeito simples e direto.\n"
        f"Você perguntou: \"to gastando muito no pix esse mes\".\n\n"
        "✨ IA 3.0 – Consultor financeiro PIX\n"
        "Olhei o resumo do seu mês no PIX e montei uma visão geral:\n\n"
        f"- Saldo atual (aprox.): {fmt_brl(saldo_atual)}\n"
        f"- Entradas no mês via PIX: {fmt_brl(entradas_mes)}\n"
        f"- Saídas no mês via PIX: {fmt_brl(saidas_mes)}\n"
        f"- Resultado do mês (Entradas - Saídas): {fmt_brl(resultado)}\n\n"
        "Resumo de risco do mês:\n"
        f"{nivel}: {comentario}\n\n"
        "O que isso significa na prática:\n"
        "Se o resultado está negativo, o ideal é reduzir gastos por impulso, revisar assinaturas e priorizar contas essenciais. "
        "Se estiver positivo, é uma boa hora para organizar uma reserva e planejar metas.\n\n"
        "Se quiser, pode perguntar também por 'entradas do mês', 'saídas do mês' ou 'histórico do PIX' que eu trago mais detalhes.\n\n"
        "Resumo rápido: estou te ajudando agora com modo consultor financeiro.\n\n"
        f"Atendo você usando o cadastro: {balance.get('email') or 'seu usuário Aurea Gold'}."
    )
    return texto

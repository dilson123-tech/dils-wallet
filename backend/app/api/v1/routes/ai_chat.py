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
    _ia3_m = payload.message.lower()  # IA 3.0 – resumo do mês no PIX
    if any(
        frase in _ia3_m
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
        _resumo = _ia3_get_pix_month_summary(x_user_email)
        _reply = _ia3_build_monthly_summary_reply(_resumo)
        return {"reply": _reply}
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
    Calcula o resumo do mês atual para o usuário:
    - entradas_mes
    - saidas_mes
    - net_mes
    - qtd_transacoes

    IMPORTANTE:
    - Ajustar o model e os campos conforme o seu projeto real.
    - Por padrão estou assumindo um model PixTransaction com:
      user_email, kind ("entrada"/"saida"), amount, created_at.
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import func

    from app.db.session import SessionLocal
    from app.models.pix_transaction import PixTransaction  # ajuste se o nome for outro

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
            if row.kind == "entrada":
                entradas = float(row.total or 0)
            elif row.kind == "saida":
                saidas = float(row.total or 0)
            total_qtd += row.qtd or 0

        net = entradas - saidas

        return {
            "entradas_mes": entradas,
            "saidas_mes": saidas,
            "net_mes": net,
            "qtd_transacoes": total_qtd,
        }
    finally:
        db.close()


def _ia3_build_monthly_summary_reply(resumo: dict) -> str:
    """
    Monta a resposta de texto da IA 3.0
    para o 'Resumo do mês no PIX'.
    """
    entradas = resumo.get("entradas_mes", 0.0)
    saidas = resumo.get("saidas_mes", 0.0)
    net = resumo.get("net_mes", 0.0)
    qtd = resumo.get("qtd_transacoes", 0)

    def _fmt_brl(v: float) -> str:
        return "R$ " + f"{v:.2f}".replace(".", ",")

    direcao = "superávit" if net >= 0 else "déficit"
    emoji = "📈" if net >= 0 else "📉"

    return (
        "✨ IA 3.0 Premium – Resumo do mês no PIX\n\n"
        f"{emoji} Entradas do mês: {_fmt_brl(entradas)}\n"
        f"💸 Saídas do mês: {_fmt_brl(saidas)}\n"
        f"🧮 Resultado do mês: {_fmt_brl(net)} ({direcao})\n"
        f"🧾 Quantidade de transações: {qtd}\n\n"
        "Visão da IA 3.0:\n"
        "- Se as entradas estão fortes, você pode planejar reservas ou investimentos.\n"
        "- Se as saídas estão altas, vale revisar onde está indo o dinheiro.\n"
        "- Use esse resumo junto com o painel Aurea Gold para decidir os próximos passos."
    )

def _ia3_get_pix_month_summary(user_email: str) -> dict:
    """
    Versão robusta que evita quebrar a API caso o model ou a query
    não estejam exatamente como esperado.

    Retorna um dicionário com:
    - entradas_mes
    - saidas_mes
    - net_mes
    - qtd_transacoes
    """
    from sqlalchemy.orm import Session
    from sqlalchemy import func
    from app.db.session import SessionLocal

    zeros = {
        "entradas_mes": 0.0,
        "saidas_mes": 0.0,
        "net_mes": 0.0,
        "qtd_transacoes": 0,
    }

    # Tentativa flexível de importar o model
    try:
        try:
            from app.models.pix_transaction import PixTransaction  # caminho 1
        except Exception:
            from app.models.pix import PixTransaction  # caminho 2 (ajuste se precisar)
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
            if row.kind == "entrada":
                entradas = float(row.total or 0)
            elif row.kind == "saida":
                saidas = float(row.total or 0)
            total_qtd += row.qtd or 0

        net = entradas - saidas

        return {
            "entradas_mes": entradas,
            "saidas_mes": saidas,
            "net_mes": net,
            "qtd_transacoes": total_qtd,
        }
    except Exception as e:
        print("IA3 resumo_mes: erro ao consultar transações:", e)
        return zeros
    finally:
        db.close()

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
            from app.database.session import SessionLocal  # fallback comum (ajuste se seu projeto usar outro)
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
            if row.kind == "entrada":
                entradas = float(row.total or 0)
            elif row.kind == "saida":
                saidas = float(row.total or 0)
            total_qtd += row.qtd or 0

        net = entradas - saidas

        return {
            "entradas_mes": entradas,
            "saidas_mes": saidas,
            "net_mes": net,
            "qtd_transacoes": total_qtd,
        }
    except Exception as e:
        print("IA3 resumo_mes: erro ao consultar transações:", e)
        return zeros
    finally:
        db.close()


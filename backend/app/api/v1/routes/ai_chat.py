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



def _ia3_build_consulting_reply(resumo: dict) -> str:
    """Monta o texto de consultoria financeira usando o resumo do mês."""
    def _fmt_brl(v) -> str:
        try:
            n = float(v or 0.0)
        except Exception:
            n = 0.0
        return "R$ " + f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    entradas = float(resumo.get("entradas_mes", 0.0) or 0.0)
    saidas = float(resumo.get("saidas_mes", 0.0) or 0.0)
    net = float(resumo.get("net_mes", 0.0) or 0.0)
    qtd = int(resumo.get("qtd_transacoes", 0) or 0)

    linhas = []
    linhas.append("Visão do mês no PIX:")
    linhas.append(f"- Entradas do mês: {_fmt_brl(entradas)}.")
    linhas.append(f"- Saídas do mês: {_fmt_brl(saidas)}.")
    linhas.append(f"- Resultado do mês: {_fmt_brl(net)}.")
    linhas.append(f"- Quantidade de transações: {qtd}.")

    linhas.append("\nRecomendações básicas para este mês:")

    if qtd == 0:
        linhas.append(
            "- Ainda não há movimentações registradas. "
            "Use o Aurea Gold normalmente e volte aqui depois de alguns PIX."
        )
    else:
        if saidas > entradas:
            linhas.append(
                "- Você está gastando mais do que entra. "
                "Tente revisar gastos variáveis e evitar PIX grandes até equilibrar."
            )
        elif saidas > entradas * 0.9:
            linhas.append(
                "- Suas saídas estão quase no mesmo nível das entradas. "
                "Vale segurar um pouco os gastos até o fim do mês."
            )

        if entradas > 0 and saidas < entradas * 0.7:
            linhas.append(
                "- Suas entradas estão em nível saudável. "
                "Considere separar uma parte fixa para reserva ou objetivos de curto prazo."
            )

        if not any("Você está gastando mais" in l or "quase no mesmo nível" in l for l in linhas):
            linhas.append(
                "- Seus números estão em faixa neutra. "
                "Acompanhe pelo painel Super2 e evite aumentar os gastos sem necessidade."
            )

    linhas.append(
        "\nUse essas orientações junto com o painel Aurea Gold para decidir os próximos passos."
    )

    return "\n".join(linhas)


# === IA 3.0 – helper atualizado para modo consultor financeiro (resumo do mês) ===
def _ia3_build_consulting_reply(resumo):
    """
    Monta a resposta em modo consultor financeiro usando o resumo mensal do PIX.
    Espera um dict parecido com:
      - entradas_mes / entradas
      - saidas_mes / saidas
      - saldo_mes / saldo / saldo_atual
    Mas é tolerante se alguma chave vier faltando.
    """

    if not resumo:
        return (
            "Vou te ajudar com o seu mês no PIX assim que eu tiver dados consolidados.\n\n"
            "Por enquanto não encontrei movimentações suficientes para montar um fechamento. "
            "Se você já começou a usar o Aurea Gold hoje, é normal ainda não aparecer nada. "
            "Tente novamente depois de fazer algumas entradas e saídas via PIX."
        )

    # Tenta ler valores com fallback em nomes diferentes
    def _num(value):
        try:
            return float(value or 0)
        except Exception:
            return 0.0

    entradas = _num(
        resumo.get("entradas_mes")
        or resumo.get("entradas")
        or resumo.get("total_entradas")
    )
    saidas = _num(
        resumo.get("saidas_mes")
        or resumo.get("saidas")
        or resumo.get("total_saidas")
    )
    saldo = _num(
        resumo.get("saldo_mes")
        or resumo.get("saldo")
        or resumo.get("saldo_atual")
        or (entradas - saidas)
    )

    # Classificação do mês
    if entradas <= 0 and saidas <= 0:
        status = "sem_movimento"
        faixa_label = "mês quase sem movimento"
        resumo_status = (
            "Você teve pouca ou nenhuma movimentação via PIX neste mês. "
            "É um cenário neutro: não há riscos, mas também não há volume para analisar."
        )
        recomendacoes = [
            "Usar o Aurea Gold como conta principal para concentrar seus recebimentos.",
            "Registrar pelo menos um fluxo real de entradas e saídas para a IA acompanhar.",
        ]
    else:
        gasto_ratio = None
        if entradas > 0:
            gasto_ratio = saidas / entradas

        if gasto_ratio is None:
            # Entradas zero mas saídas > 0 → claramente crítico
            status = "estourado"
            faixa_label = "mês crítico no PIX"
            resumo_status = (
                "Você teve saídas relevantes sem um volume claro de entradas. "
                "Isso indica risco de depender de outras fontes para cobrir o caixa."
            )
            recomendacoes = [
                "Reduzir gastos imediatos via PIX até equilibrar as entradas.",
                "Definir um valor mínimo de entrada mensal antes de assumir novos compromissos.",
            ]
        elif gasto_ratio < 0.4:
            status = "muito_saudavel"
            faixa_label = "mês muito saudável"
            resumo_status = (
                "Suas saídas ficaram bem abaixo das entradas. "
                "O mês está no azul com folga, com boa margem para reserva ou investimento."
            )
            recomendacoes = [
                "Separar uma parte fixa das entradas para reserva (ex.: 20% todo mês).",
                "Definir uma meta de saldo mínimo para manter sempre no Aurea Gold.",
            ]
        elif gasto_ratio <= 0.8:
            status = "controlado"
            faixa_label = "mês controlado"
            resumo_status = (
                "Suas saídas ficaram em um nível confortável em relação às entradas. "
                "O mês está sob controle, mas ainda existe espaço para otimizar gastos."
            )
            recomendacoes = [
                "Rever pequenos gastos recorrentes via PIX e cortar o que não é essencial.",
                "Definir um teto de saídas mensal e acompanhar no painel Super2.",
            ]
        elif saidas <= entradas:
            status = "no_limite"
            faixa_label = "mês no limite"
            resumo_status = (
                "Suas saídas ficaram muito próximas do total de entradas. "
                "Qualquer gasto extra pode colocar o mês no vermelho."
            )
            recomendacoes = [
                "Congelar novos gastos via PIX até abrir mais folga no saldo.",
                "Acompanhar o painel Super2 semanalmente para ajustar o ritmo de gastos.",
            ]
        else:
            status = "estourado"
            faixa_label = "mês estourado"
            resumo_status = (
                "As saídas superaram as entradas neste mês. "
                "Isso indica um cenário de atenção máxima com o fluxo de PIX."
            )
            recomendacoes = [
                "Priorizar apenas pagamentos essenciais via PIX até recuperar o saldo.",
                "Planejar o próximo mês com um limite de saídas menor do que as entradas esperadas.",
            ]

    # Monta texto final em formato consultor Aurea Gold
    linhas = []

    linhas.append("📊 Fechamento do seu mês no PIX – modo consultor Aurea Gold 3.0\n")

    linhas.append(
        f"- Entradas no mês: R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    linhas.append(
        f"- Saídas no mês:   R$ {saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    linhas.append(
        f"- Saldo do mês:    R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    linhas.append("")

    linhas.append(f"Situação geral: {faixa_label}.")
    linhas.append(resumo_status)
    linhas.append("")

    linhas.append("Recomendo para este mês:")
    for rec in recomendacoes:
        linhas.append(f"- {rec}")

    linhas.append("")
    linhas.append(
        "Lembrete: esta análise é focada apenas nos movimentos do seu Aurea Gold via PIX. "
        "Ela não substitui um planejamento financeiro completo, mas já te dá um radar "
        "para acompanhar seu mês de forma prática."
    )

    # status fica só interno por enquanto (não expomos como JSON aqui)
    return "\n".join(linhas)
def _ia3_build_consulting_reply(balance):
    """Gera uma resposta em modo consultor financeiro usando o resumo do mês no PIX.

    `balance` pode ser um dict ou um objeto com atributos como:
    - saldo_atual / saldo / saldo_disponivel
    - entradas_mes / entradas_30d / entradas
    - saidas_mes / saidas_30d / saidas
    - net_mes (resultado do mês)
    """

    if not balance:
        return (
            "✨ IA 3.0 – Consultor financeiro PIX\n"
            "Ainda não consegui carregar o resumo do seu mês no PIX.\n\n"
            "Mesmo assim, algumas orientações gerais ajudam bastante:\n"
            "- Tente separar uma parte fixa de tudo o que entra como reserva.\n"
            "- Evite PIX por impulso: compras rápidas, lanches, pequenos gastos que somam muito no mês.\n"
            "- Sempre que possível, concentre as contas em poucos dias do mês pra ter mais previsibilidade.\n\n"
            "Quando o painel Super2 estiver com os dados carregados, posso analisar melhor seu comportamento "
            "de entradas e saídas ao longo do mês."
        )

    # Acessa tanto dict quanto objeto simples
    def _get(b, *keys):
        if isinstance(b, dict):
            for k in keys:
                if k in b and b[k] is not None:
                    return b[k]
        else:
            for k in keys:
                v = getattr(b, k, None)
                if v is not None:
                    return v
        return None

    def fmt_brl(v):
        try:
            v_float = float(v)
        except (TypeError, ValueError):
            return "—"
        s = f"{v_float:,.2f}"
        # Formata no padrão brasileiro: 1.234,56
        return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

    saldo_atual = _get(balance, "saldo_atual", "saldo", "saldo_disponivel")
    entradas_mes = _get(balance, "entradas_mes", "entradas_30d", "entradas")
    saidas_mes = _get(balance, "saidas_mes", "saidas_30d", "saidas")
    net_mes = _get(balance, "net_mes")

    if net_mes is None and entradas_mes is not None and saidas_mes is not None:
        try:
            net_mes = float(entradas_mes) - float(saidas_mes)
        except (TypeError, ValueError):
            net_mes = None

    saldo_txt = fmt_brl(saldo_atual) if saldo_atual is not None else "—"
    entradas_txt = fmt_brl(entradas_mes) if entradas_mes is not None else "—"
    saidas_txt = fmt_brl(saidas_mes) if saidas_mes is not None else "—"
    net_txt = fmt_brl(net_mes) if net_mes is not None else "—"

    orientacao = []

    if net_mes is None:
        orientacao.append(
            "Não consegui calcular exatamente se você fechou o mês no positivo ou negativo, "
            "mas já vale olhar se as saídas não estão crescendo mais rápido do que as entradas."
        )
    else:
        try:
            nm = float(net_mes)
        except (TypeError, ValueError):
            nm = 0.0

        if nm < 0:
            orientacao.append(
                "Você fechou o mês **no negativo**: saiu mais dinheiro do que entrou nos seus PIX."
            )
            orientacao.append(
                "O ideal agora é reduzir gastos por impulso, revisar assinaturas e priorizar contas essenciais."
            )
        elif nm > 0:
            orientacao.append(
                "Você fechou o mês **no positivo**: entrou mais dinheiro do que saiu nos seus PIX."
            )
            orientacao.append(
                "Aproveite para separar uma parte desse resultado para reserva, investimentos ou metas importantes."
            )
        else:
            orientacao.append(
                "Seu mês ficou praticamente **no zero a zero** entre entradas e saídas no PIX."
            )
            orientacao.append(
                "Qualquer aumento de gasto sem aumento de entrada pode te levar para o negativo no próximo mês, "
                "então vale acompanhar de perto."
            )

    texto_orientacao = " ".join(orientacao)

    return (
        "✨ IA 3.0 – Consultor financeiro PIX\n"
        "Olhei o resumo do seu mês no PIX e montei uma visão geral:\n\n"
        f"- Saldo atual (aprox.): {saldo_txt}\n"
        f"- Entradas no mês via PIX: {entradas_txt}\n"
        f"- Saídas no mês via PIX: {saidas_txt}\n"
        f"- Resultado do mês (Entradas - Saídas): {net_txt}\n\n"
        "O que isso significa na prática:\n"
        f"{texto_orientacao}\n\n"
        "Se quiser, pode perguntar também por 'entradas do mês', 'saídas do mês' ou 'histórico do PIX' "
        "que eu trago mais detalhes."
    )


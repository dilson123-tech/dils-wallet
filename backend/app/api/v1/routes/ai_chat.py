import textwrap
from fastapi import APIRouter, Header, Request
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
from urllib import request, error as urlerror  # noqa: F401


from sqlalchemy import text
import json, base64
from typing import Optional

def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _jwt_sub_unverified(token: str) -> Optional[str]:
    # DEV: pega 'sub' sem validar assinatura
    try:
        _h, p, _s = token.split('.', 2)
    except ValueError:
        return None
    try:
        payload = json.loads(_b64url_decode(p).decode('utf-8'))
    except Exception:
        return None
    return payload.get('sub')

def _resolve_user_id(db, request, x_user_email: Optional[str]):
    auth = request.headers.get('authorization') or request.headers.get('Authorization')
    if auth and auth.lower().startswith('bearer '):
        sub = _jwt_sub_unverified(auth.split(' ',1)[1].strip())
        if sub:
            row = db.execute(text('SELECT id FROM users WHERE username=:u LIMIT 1'), {'u': sub}).fetchone()
            if row:
                return int(row[0])
    if x_user_email:
        row = db.execute(text('SELECT id FROM users WHERE email=:e LIMIT 1'), {'e': x_user_email}).fetchone()
        if row:
            return int(row[0])
    return None
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



def _email_from_auth_header(auth_header):
    """
    Extrai 'sub' (email/username) do JWT para usar como X-User-Email quando o client não envia.
    Não derruba a IA se falhar.
    """
    if not auth_header:
        return None
    ah = str(auth_header).strip()
    if not ah:
        return None
    token = ah.split(None, 1)[1].strip() if ah.lower().startswith("bearer ") else ah

    try:
        import os
        from jose import jwt, JWTError

        secret = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "dev-secret"
        alg = os.getenv("JWT_ALG") or os.getenv("JWT_ALGORITHM") or os.getenv("ALGORITHM") or "HS256"

        payload = jwt.decode(token, secret, algorithms=[alg])
        sub = payload.get("sub")
        return str(sub) if sub else None
    except Exception:
        return None



async def _fetch_internal_json(
    path: str,
    x_user_email: Optional[str],
    auth_header: Optional[str] = None,
) -> Optional[dict]:
    """
    Faz uma chamada interna para a própria API (localhost:8000),
    reaproveitando toda a lógica já existente de PIX.
    Em caso de erro, retorna None sem derrubar a IA.
    """
    url = f"http://127.0.0.1:8000{path}"

    # Headers mínimos e consistentes p/ chamadas internas
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if x_user_email:
        headers["X-User-Email"] = x_user_email

    # Encaminha Authorization do request original (aceita token cru ou 'Bearer <token>')
    if auth_header:
        ah = auth_header.strip()
        if not ah.lower().startswith("bearer "):
            ah = "Bearer " + ah
        headers["Authorization"] = ah

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
    authorization: Optional[str],
) -> Optional[dict]:
    if not x_user_email and authorization:
        x_user_email = _email_from_auth_header(authorization)
    return await _fetch_internal_json("/api/v1/pix/balance", x_user_email, authorization)


async def _get_pix_history(
    x_user_email: Optional[str],
    authorization: Optional[str],
) -> Optional[list]:
    if not x_user_email and authorization:
        x_user_email = _email_from_auth_header(authorization)
    data = await _fetch_internal_json("/api/v1/pix/history", x_user_email, authorization)

    # casos: lista direta
    if isinstance(data, list):
        return data

    # casos: dict com history/items/dias
    if isinstance(data, dict):
        h = data.get("history")
        if isinstance(h, list):
            return h
        items = data.get("items")
        if isinstance(items, list):
            return items
        # "dias" é agregado, não é transação; então aqui a gente não usa para gasto mais/histórico detalhado
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



def _build_gasto_mais_reply(history: list) -> str:
    # Considera "saídas" como transações tipo envio/pagamento/saida ou qualquer valor > 0
    saidas = []
    for tx in history or []:
        try:
            v = float(tx.get("valor") or 0.0)
        except Exception:
            v = 0.0
        tipo = (tx.get("tipo") or "").lower()
        if v > 0 and (tipo in ("envio", "pagamento", "saida", "saída") or tipo):
            saidas.append({**tx, "_valor_num": v, "_tipo": tipo})

    if not saidas:
        return (
            "Ainda não encontrei **saídas** no seu histórico PIX.\n\n"
            "Assim que você fizer envios/pagamentos, eu consigo te dizer onde está gastando mais."
        )

    # total + maior gasto
    total = sum(x["_valor_num"] for x in saidas)
    maior = max(saidas, key=lambda x: x["_valor_num"])

    # agrupa por descricao (quando existir)
    grupos = {}
    for tx in saidas:
        desc = (tx.get("descricao") or "Sem descrição").strip()
        grupos[desc] = grupos.get(desc, 0.0) + tx["_valor_num"]

    top_grupos = sorted(grupos.items(), key=lambda kv: kv[1], reverse=True)[:3]
    top_tx = sorted(saidas, key=lambda x: x["_valor_num"], reverse=True)[:3]

    def fmt_brl(n: float) -> str:
        return ("R$ " + f"{n:.2f}").replace(".", ",")

    linhas = []
    linhas.append("📌 Onde você está gastando mais (baseado no histórico PIX)\n")
    linhas.append(f"• Total de saídas no período: **{fmt_brl(total)}**")
    linhas.append(f"• Maior gasto individual: **{fmt_brl(maior['_valor_num'])}** — {maior.get('descricao','(sem descrição)')}")
    linhas.append("\n🏷️ Top “categorias” (por descrição):")
    for desc, soma in top_grupos:
        linhas.append(f"• {desc}: **{fmt_brl(soma)}**")

    linhas.append("\n💸 Top 3 transações:")
    for tx in top_tx:
        ts = (tx.get("timestamp") or "").replace("T", " ")
        linhas.append(f"• {fmt_brl(tx['_valor_num'])} — {tx.get('descricao','(sem descrição)')} — {ts}")

    linhas.append("\nSe você quiser, eu também consigo te dizer **em quais dias** saiu mais dinheiro.")
    return "\n".join(linhas)


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    payload: ChatRequest,
    request: Request,
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
):
    """
    IA 3.0 da Aurea Gold — versão Premium com explicação organizada
    e, sempre que possível, usando dados reais de PIX do próprio painel.
    """
    auth = request.headers.get('authorization') or request.headers.get('Authorization')

    raw_msg = payload.message.strip()
    norm_msg = _normalize(raw_msg)
    # atalhos diretos para perguntas de entradas/saídas do mês no PIX
    if any(
        p in norm_msg
        for p in [
            "entradas do mes no pix",
            "entradas do mês no pix",
            "entradas no pix esse mes",
            "entradas no pix esse mês",
        ]
    ):
        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
        if balance:
            reply = _build_entradas_reply(balance)
        else:
            reply = (
                "Não consegui ler as entradas do mês via PIX agora.\n\n"
                "Tente novamente em alguns instantes ou confira direto no painel Super2."
            )
        return {"reply": reply, "tema": "entradas_mes_pix"}

    if any(
        p in norm_msg
        for p in [
            "saidas do mes no pix",
            "saídas do mês no pix",
            "gastos do mes no pix",
            "gastos do mês no pix",
        ]
    ):
        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
        if balance:
            reply = _build_saidas_reply(balance)
        else:
            reply = (
                "Não consegui ler as saídas do mês via PIX agora.\n\n"
                "Tente novamente em alguns instantes ou confira direto no painel Super2."
            )
        return {"reply": reply, "tema": "saidas_mes_pix"}


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

        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
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


        # Atalhos diretos para botões do painel Super2:
    # "Entradas do mês no PIX" e "Histórico/Saídas do mês"
    try:
        if any(
            p in norm_msg
            for p in [
                "entradas do mes no pix",
                "entradas do mês no pix",
                "entradas no pix esse mes",
                "entradas no pix esse mês",
            ]
        ):
            resumo = _ia3_get_pix_month_summary(x_user_email)
            if resumo:
                reply = _ia3_build_entradas_mes_reply(resumo)
            else:
                reply = (
                    "Não consegui carregar agora as entradas do mês via PIX.\n\n"
                    "Tente novamente em alguns instantes ou confira as entradas no painel Super2."
                )
            return {"reply": reply, "tema": "entradas_mes_pix"}

        if any(
            p in norm_msg
            for p in [
                "saidas do mes no pix",
                "saídas do mês no pix",
                "gastos do mes no pix",
                "gastos do mês no pix",
            ]
        ):
            resumo = _ia3_get_pix_month_summary(x_user_email)
            if resumo:
                reply = _ia3_build_saidas_mes_reply(resumo)
            else:
                reply = (
                    "Não consegui carregar agora as saídas do mês via PIX.\n\n"
                    "Tente novamente em alguns instantes ou confira as saídas no painel Super2."
                )
            return {"reply": reply, "tema": "saidas_mes_pix"}
    except Exception:
        # Se der qualquer erro interno, não quebra a API:
        reply = (
            "Não consegui processar agora os dados de ENTRADAS/SAÍDAS do mês via PIX.\n\n"
            "Tente novamente em alguns instantes ou confira os valores direto no painel Super2."
        )
        return {"reply": reply, "tema": "erro_pix_mes"}

    if any(p in norm_msg for p in ["saldo", "quanto tenho", "quanto eu tenho"]):
        tema_label = "saldo"
        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
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
        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
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
        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
        if balance:
            tema_reply = _build_saidas_reply(balance)
        else:
            tema_reply = (
                "Você perguntou sobre as saídas.\n\n"
                "As saídas são todos os valores que saíram da sua conta: pagamentos, transferências "
                "e outros débitos. No painel Super2, o campo 'Saídas (Mês)' concentra esse número.\n\n"
                "Se os dados não carregarem agora, vale tentar novamente em alguns instantes."
            )

    elif any(p in norm_msg for p in ["onde gasto mais", "onde eu gasto mais", "onde gasto", "gasto mais", "meus gastos", "maiores gastos"]):
        tema_label = "onde_gasto_mais"
        history = await _get_pix_history(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
        tema_reply = _build_gasto_mais_reply(history or [])
    elif any(p in norm_msg for p in ["historico", "historico pix", "ultimas movimentacoes", "movimentacao"]):
        tema_label = "histórico de PIX"
        history = await _get_pix_history(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
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
        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
        tema_reply = _ia3_build_consulting_reply(balance)
        intro = ""

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
        balance = await _get_pix_balance(x_user_email, request.headers.get('authorization') or request.headers.get('Authorization'))
        tema_reply = _ia3_build_consulting_reply(balance)

    else:
        tema_reply = (
            "Você fez uma pergunta mais geral.\n\n"
            "Nesta versão, eu respondo melhor sobre temas como saldo, entradas, saídas, "
            "histórico PIX e funcionamento básico do painel Aurea Gold.\n\n"
            "Se quiser, pode tentar reformular a pergunta citando um desses pontos, e eu te "
            "entrego uma explicação mais direta."
        )

    # Montagem final da resposta
    if tema_label == "modo consultor financeiro":
        # No modo consultor, o helper já monta todo o texto (intro, pergunta, resumo, etc.)
        final_reply = f"{tema_reply}{user_hint}"
    else:
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


def _ia3_build_entradas_mes_reply(resumo: dict) -> str:
    """Resposta IA 3.0 focada nas ENTRADAS do mês via PIX."""
    saldo_atual = resumo["saldo_atual"]
    entradas = resumo["entradas_mes"]
    saidas = resumo["saidas_mes"]
    resultado_mes = resumo["resultado_mes"]

    def fmt_brl(v: float) -> str:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return (
        "💰 IA 3.0 da Aurea Gold\n\n"
        "Aqui está o panorama das **entradas do mês via PIX**:\n\n"
        f"• Entradas no mês (PIX): **{fmt_brl(entradas)}**\n"
        f"• Saídas no mês (PIX): {fmt_brl(saidas)}\n"
        f"• Resultado do mês (PIX): {fmt_brl(resultado_mes)}\n"
        f"• Saldo atual na carteira PIX: {fmt_brl(saldo_atual)}\n\n"
        "O que isso quer dizer:\n"
        "- Se as entradas estão fortes, está entrando bastante dinheiro via PIX.\n"
        "- Se estiver baixo, pode ser sinal de que você precisa reforçar vendas, cobranças e recorrências.\n\n"
        "Se quiser, posso te ajudar também com **saídas do mês no PIX** ou ativar o "
        "**modo consultor financeiro** para um diagnóstico mais completo do seu mês."
    )


def _ia3_build_saidas_mes_reply(resumo: dict) -> str:
    """Resposta IA 3.0 focada nas SAÍDAS do mês via PIX."""
    saldo_atual = resumo["saldo_atual"]
    entradas = resumo["entradas_mes"]
    saidas = resumo["saidas_mes"]
    resultado_mes = resumo["resultado_mes"]

    def fmt_brl(v: float) -> str:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return (
        "💳 IA 3.0 da Aurea Gold\n\n"
        "Aqui está o panorama das **saídas do mês via PIX**:\n\n"
        f"• Saídas no mês (PIX): **{fmt_brl(saidas)}**\n"
        f"• Entradas no mês (PIX): {fmt_brl(entradas)}\n"
        f"• Resultado do mês (PIX): {fmt_brl(resultado_mes)}\n"
        f"• Saldo atual na carteira PIX: {fmt_brl(saldo_atual)}\n\n"
        "Como interpretar:\n"
        "- Se as saídas estão muito altas, pode ser sinal de gastos puxados no mês.\n"
        "- Se estiver equilibrado com as entradas, o fluxo está mais controlado.\n"
        "- Se o resultado do mês estiver negativo, vale revisar onde está indo a maior parte do dinheiro.\n\n"
        "Se quiser, posso ligar o **modo consultor financeiro** para te dar um diagnóstico completo "
        "do mês e recomendações práticas sobre como organizar melhor seus PIX."
    )
# === IA 3.0 – Laboratório de Pagamentos ===

@router.post("/pagamentos_lab")
async def pagamentos_lab(payload: dict, x_user_email: str = Header(None)):
    msg = (payload.get("message") or "").strip()
    norm = (msg or "").lower()

    # Versão LAB: responde com textos explicativos, ainda sem dados reais de contas
    if "risco" in norm and "atras" in norm and "conta" in norm:
        reply = (
            "🧠 IA 3.0 da Aurea Gold — Risco de atraso\n\n"
            "Olhei para a ideia das suas contas e vencimentos e, nesta versão de laboratório,\n"
            "ainda estou usando dados de exemplo. Quando eu estiver ligada às suas contas reais,\n"
            "vou analisar vencimentos dos próximos dias, comparar com o saldo da Carteira PIX\n"
            "e classificar se o cenário está tranquilo, em atenção ou em alerta de atraso.\n\n"
            "Por enquanto, use o painel de Pagamentos para ver:\n"
            "- Contas de hoje,\n"
            "- Contas dos próximos 7 dias,\n"
            "- Contas cadastradas do mês.\n\n"
            "Se quiser, pode perguntar também: 'quanto vou pagar de contas esta semana?'\n"
            "ou 'quais contas faz sentido pagar hoje?'."
        )
    elif "semana" in norm and "conta" in norm:
        reply = (
            "🧠 IA 3.0 da Aurea Gold — Contas desta semana\n\n"
            "Na versão completa, eu vou somar todas as contas que vencem nos próximos 7 dias,\n"
            "comparar com o saldo da Carteira PIX e te mostrar o peso dessa semana no seu caixa.\n\n"
            "Aqui no laboratório, o painel mostra um exemplo de como isso fica organizado,\n"
            "com vencimentos em 'Hoje', 'Próximos 7 dias' e 'Este mês'.\n\n"
            "A ideia é que você consiga bater o olho e entender:\n"
            "- quantas contas vêm na semana,\n"
            "- o valor total,\n"
            "- e quanto deve sobrar de saldo depois dos pagamentos."
        )
    elif "pagar hoje" in norm or "faz sentido pagar hoje" in norm:
        reply = (
            "🧠 IA 3.0 da Aurea Gold — Ordem sugerida de pagamento\n\n"
            "Quando eu estiver ligada às suas contas reais, vou montar uma ordem inteligente\n"
            "de pagamento para o dia, priorizando:\n"
            "- contas atrasadas ou perto do vencimento,\n"
            "- contas essenciais (moradia, luz, água, internet, trabalho),\n"
            "- impacto no saldo da Carteira PIX.\n\n"
            "Na prática, a ideia é eu te dizer algo como:\n"
            "1) quais contas pagar primeiro,\n"
            "2) quais podem esperar alguns dias,\n"
            "3) e qual fica o saldo provável depois disso.\n\n"
            "Nesta fase LAB, você já consegue visualizar essa lógica no painel,\n"
            "mas ainda sem cálculos reais ligados ao seu cadastro."
        )
    else:
        reply = (
            "💬 IA 3.0 da Aurea Gold — Painel de Pagamentos (LAB)\n\n"
            "Aqui eu vou te ajudar a responder três grandes perguntas:\n"
            "- Tenho risco de atrasar alguma conta?\n"
            "- Quanto vou pagar de contas esta semana?\n"
            "- Quais contas faz sentido pagar hoje?\n\n"
            "Nesta versão de laboratório, estou explicando como vou funcionar quando estiver\n"
            "ligada às suas contas reais e ao saldo da Carteira PIX.\n"
            "Use o painel para ir se acostumando com a visão de vencimentos e organização."
        )

    return {"reply": reply, "tema": "pagamentos_lab"}


# === Alias de compatibilidade para IA 3.0 (consultor financeiro) ===
# Alguns pontos da codebase ainda chamam ia3_build_consulting_replyv (com "v").
# Este alias só repassa para a função oficial ia3_build_consulting_reply.
def ia3_build_consulting_replyv(*args, **kwargs):
    """Alias de compatibilidade: delega para ia3_build_consulting_reply."""
    return ia3_build_consulting_reply(*args, **kwargs)


from app.api.v1.ai import build_ia_headline_panel
from fastapi import Header

# === IA 3.0 – Endpoint LAB do Headline (Painel 3) ===

# === IA 3.0 – Insight oficial do PIX (dados reais) ===
@router.post("/ai/pix-insight")
async def ia_pix_insight(x_user_email: str = Header(None)):
    """IA 3.0 lendo o extrato oficial de PIX do usuário logado.

    Consulta a tabela pix_transactions filtrando pelo usuário
    e devolve um resumo numérico + interpretação pronta para o painel.
    """

    def _to_float(value):
        try:
            return float(value or 0)
        except Exception:
            return 0.0

    if not x_user_email:
        # Mantém padrão de resposta JSON em vez de exception
        return {
            "nivel": "erro",
            "headline": "Não consegui identificar o usuário para a IA do PIX",
            "subheadline": "O cabeçalho X-User-Email não foi enviado.",
            "resumo": "Envie o X-User-Email no header da requisição para eu conseguir localizar o extrato oficial.",
            "metricas": {
                "total_transacoes": 0,
                "entradas_brutas": 0.0,
                "saidas_brutas": 0.0,
                "taxas_totais": 0.0,
                "saldo_liquido_estimado": 0.0,
                "entradas_7d": 0.0,
                "saidas_7d": 0.0,
                "entradas_mes": 0.0,
                "saidas_mes": 0.0,
            },
        }

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == x_user_email).first()
        if not user:
            return {
                "nivel": "erro",
                "headline": "Usuário não encontrado para IA do PIX",
                "subheadline": "Não achei nenhum usuário com esse e-mail cadastrado na Aurea Gold.",
                "resumo": f"E-mail recebido: {x_user_email!r}. Verifique se é o mesmo usado no cadastro/login.",
                "metricas": {
                    "total_transacoes": 0,
                    "entradas_brutas": 0.0,
                    "saidas_brutas": 0.0,
                    "taxas_totais": 0.0,
                    "saldo_liquido_estimado": 0.0,
                    "entradas_7d": 0.0,
                    "saidas_7d": 0.0,
                    "entradas_mes": 0.0,
                    "saidas_mes": 0.0,
                },
            }

        # Busca últimas N transações oficiais de PIX desse usuário
        limite = 200
        txs = (
            db.query(PixTransaction)
            .filter(PixTransaction.user_id == user.id)
            .order_by(PixTransaction.timestamp.desc())
            .limit(limite)
            .all()
        )

        if not txs:
            return {
                "nivel": "vazio",
                "headline": "Ainda não encontrei movimentações oficiais de PIX",
                "subheadline": "Assim que sua carteira começar a registrar envios e recebimentos, eu passo a analisar os dados reais.",
                "resumo": "Sem transações PIX para este usuário no histórico consultado.",
                "metricas": {
                    "total_transacoes": 0,
                    "entradas_brutas": 0.0,
                    "saidas_brutas": 0.0,
                    "taxas_totais": 0.0,
                    "saldo_liquido_estimado": 0.0,
                    "entradas_7d": 0.0,
                    "saidas_7d": 0.0,
                    "entradas_mes": 0.0,
                    "saidas_mes": 0.0,
                },
            }

        now = datetime.utcnow()
        inicio_mes = datetime(now.year, now.month, 1)
        sete_dias_atras = now - timedelta(days=7)

        entradas_total = 0.0
        saidas_total = 0.0
        taxas_total = 0.0

        entradas_7d = 0.0
        saidas_7d = 0.0
        entradas_mes = 0.0
        saidas_mes = 0.0

        for tx in txs:
            valor = _to_float(tx.valor)
            taxa = _to_float(tx.taxa_valor)
            ts = tx.timestamp or now

            # Normaliza tipo
            tipo = (tx.tipo or "").lower()

            if tipo.startswith("rec"):  # recebido
                entradas_total += valor
                if ts >= sete_dias_atras:
                    entradas_7d += valor
                if ts >= inicio_mes:
                    entradas_mes += valor
            else:
                # trata como saída/envio
                saidas_total += valor
                if ts >= sete_dias_atras:
                    saidas_7d += valor
                if ts >= inicio_mes:
                    saidas_mes += valor

            taxas_total += taxa

        saldo_liquido_estimado = entradas_total - saidas_total - taxas_total

        # Classificação simples de nível com base no saldo e no fluxo recente
        if saldo_liquido_estimado <= 0 and (entradas_7d - saidas_7d) < 0:
            nivel = "critico"
            headline = "Alerta máximo na Carteira PIX"
            subheadline = "Os dados oficiais indicam fluxo recente negativo e saldo pressionado."
        elif saldo_liquido_estimado < 500:
            nivel = "atencao"
            headline = "Caixa do PIX apertado"
            subheadline = "O saldo estimado está baixo em relação às movimentações recentes."
        else:
            nivel = "ok"
            headline = "PIX saudável pelos dados oficiais"
            subheadline = "O saldo estimado e o fluxo recente estão sob controle."

        resumo = (
            "Analisando as últimas "
            f"{len(txs)} transações oficiais de PIX desse usuário, "
            "considerando entradas, saídas e taxas registradas na tabela pix_transactions."
        )

        return {
            "nivel": nivel,
            "headline": headline,
            "subheadline": subheadline,
            "resumo": resumo,
            "metricas": {
                "total_transacoes": len(txs),
                "entradas_brutas": round(entradas_total, 2),
                "saidas_brutas": round(saidas_total, 2),
                "taxas_totais": round(taxas_total, 2),
                "saldo_liquido_estimado": round(saldo_liquido_estimado, 2),
                "entradas_7d": round(entradas_7d, 2),
                "saidas_7d": round(saidas_7d, 2),
                "entradas_mes": round(entradas_mes, 2),
                "saidas_mes": round(saidas_mes, 2),
            },
        }
    finally:
        db.close()

@router.post("/headline")
@router.post("/headline-lab")
async def ia_headline_lab(x_user_email: str = Header(None)):
    """Versão LAB do Headline IA 3.0.

    Usa números de exemplo para não depender do ledger real.
    Depois plugamos nos dados reais do painel Super2.
    """

    # Números de exemplo para o modo LAB (simulação de fluxo PIX)
    saldo_atual = 1280.0
    entradas_7d = 4500.0
    saidas_7d = 4230.0
    entradas_mes = 4500.0
    saidas_mes = 4230.0
    total_contas_7d = 980.0
    qtd_contas_7d = 3
    entradas_previstas = 0.0

    # Retorno direto em formato JSON: textos + números
    return {
        "nivel": "ok",
        "headline": "Aurea Gold – Headline LAB funcionando",
        "subheadline": "Simulação de crédito inteligente com IA 3.0 em ambiente LAB.",
        "resumo": "Endpoint /api/v1/ai/headline-lab respondeu com sucesso em ambiente LAB.",
        "destaques": [
            "Status do Painel 3 operacional (LAB)",
            "Integração backend → IA 3.0 ok",
            "Pronto para ligar com dados reais depois",
        ],
        "recomendacao": "Agora é só conectar o Painel 3 e depois evoluir a lógica da IA.",
        "saldo_atual": saldo_atual,
        "entradas_mes": entradas_mes,
        "saidas_mes": saidas_mes,
        "entradas_7d": entradas_7d,
        "saidas_7d": saidas_7d,
        "total_contas_7d": total_contas_7d,
        "qtd_contas_7d": qtd_contas_7d,
        "entradas_previstas": entradas_previstas,
    }


from typing import List, Literal, Optional
from pydantic import BaseModel


class IAHeadlineResponse(BaseModel):
    nivel: Literal["ok", "atencao", "critico"]
    headline: str
    subheadline: str
    resumo: str
    destaques: List[str]
    recomendacao: str


def _format_brl(value: float) -> str:
    """
    Formata número em estilo BR: R$ 1.234,56
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_ia_headline_panel(
    *,
    saldo_atual: float,
    entradas_7d: float,
    saidas_7d: float,
    entradas_mes: float,
    saidas_mes: float,
    total_contas_7d: float,
    qtd_contas_7d: int,
    entradas_previstas: float = 0.0,
) -> IAHeadlineResponse:
    """
    Decide o 'clima do dia' do Aurea Gold (ok / atencao / critico)
    e monta o card do Painel 3 (IA 3.0 – Headline + detalhes).
    """

    # Proteção pra não dividir por zero
    if total_contas_7d <= 0:
        cobertura_contas = float("inf")
    else:
        cobertura_contas = saldo_atual / max(total_contas_7d, 0.01)

    diff_mes = entradas_mes - saidas_mes

    # 👇 Regrinha simples de classificação:
    # - ok: tem folga pra pagar as contas da semana e o mês fecha positivo
    # - atencao: tá no limite, pouca folga ou mês quase empatando
    # - critico: falta saldo pra contas ou mês fechando bem no negativo
    if cobertura_contas >= 1.4 and diff_mes >= 0:
        nivel = "ok"
    elif cobertura_contas >= 0.8 and diff_mes >= -0.1 * max(entradas_mes, 1.0):
        nivel = "atencao"
    else:
        nivel = "critico"

    saldo_fmt = _format_brl(saldo_atual)
    entradas_7d_fmt = _format_brl(entradas_7d)
    saidas_7d_fmt = _format_brl(saidas_7d)
    entradas_mes_fmt = _format_brl(entradas_mes)
    saidas_mes_fmt = _format_brl(saidas_mes)
    diff_mes_fmt = _format_brl(diff_mes)
    total_contas_7d_fmt = _format_brl(total_contas_7d)
    entradas_previstas_fmt = _format_brl(entradas_previstas)

    if nivel == "ok":
        headline = "Hoje seu Aurea Gold está saudável 🟢"
        subheadline = "Seu saldo e seus Pix estão sob controle."
        resumo = (
            "No geral, suas movimentações de hoje estão equilibradas.\n"
            "Você tem margem para usar o Aurea Gold com segurança, "
            "sem risco imediato de aperto nos próximos dias."
        )
        destaques = [
            f"Saldo disponível: {saldo_fmt}",
            f"Entradas nos últimos 7 dias: {entradas_7d_fmt}",
            f"Saídas nos últimos 7 dias: {saidas_7d_fmt}",
            f"Contas próximas do vencimento (7 dias): {qtd_contas_7d}",
        ]
        recomendacao = (
            "Você pode continuar usando o Aurea Gold com calma. "
            "Se quiser, eu te mostro onde otimizar pequenos gastos para guardar mais."
        )

    elif nivel == "atencao":
        headline = "Atenção: seu Aurea Gold está no limite 🟡"
        subheadline = "Ainda não é crise, mas vale cuidado nos próximos dias."
        resumo = (
            "Suas saídas recentes estão se aproximando das entradas.\n"
            "Se mantiver o ritmo atual, você pode ficar com pouco saldo "
            "antes das próximas entradas caírem."
        )
        destaques = [
            f"Saldo disponível hoje: {saldo_fmt}",
            f"Entradas no mês: {entradas_mes_fmt}",
            f"Saídas no mês: {saidas_mes_fmt}",
            f"Diferença entre entradas e saídas: {diff_mes_fmt}",
            f"Contas a vencer nos próximos 7 dias: {qtd_contas_7d} (total: {total_contas_7d_fmt})",
        ]
        recomendacao = (
            "Segura um pouco nos gastos variáveis (ex.: delivery e supérfluos) "
            "até passar os próximos vencimentos. "
            "Se quiser, eu listo agora onde você mais está gastando via Pix."
        )

    else:  # critico
        headline = "Alerta vermelho: risco de aperto financeiro 🔴"
        subheadline = (
            "Do jeito que está, você pode ficar sem saldo "
            "antes das próximas entradas."
        )
        resumo = (
            "Suas saídas superaram suas entradas recentes e o saldo está baixo "
            "em relação às contas que vão vencer.\n"
            "Se nada mudar, há risco real de atraso ou de ficar sem saldo para cobrir tudo."
        )
        destaques = [
            f"Saldo atual: {saldo_fmt}",
            f"Contas a vencer nos próximos 7 dias: {qtd_contas_7d} (total: {total_contas_7d_fmt})",
            f"Entradas previstas (salário/recebíveis): {entradas_previstas_fmt}",
            f"Déficit estimado se nada mudar: {diff_mes_fmt}",
        ]
        recomendacao = (
            "Priorize as contas essenciais (água, luz, aluguel e dívidas com juros altos).\n"
            "Se quiser, eu organizo um plano rápido: o que pagar primeiro, "
            "o que pode negociar e onde cortar gastos no Pix."
        )

    return IAHeadlineResponse(
        nivel=nivel,
        headline=headline,
        subheadline=subheadline,
        resumo=resumo,
        destaques=destaques,
        recomendacao=recomendacao,
        saldo_atual=saldo_atual,
        entradas_mes=entradas_mes,
        saidas_mes=saidas_mes,
        entradas_7d=entradas_7d,
        saidas_7d=saidas_7d,
        total_contas_7d=total_contas_7d,
        qtd_contas_7d=qtd_contas_7d,
        entradas_previstas=entradas_previstas,
    )

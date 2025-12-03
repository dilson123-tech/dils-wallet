import React, { useEffect, useState } from "react";

type ReservaPainelResponse = {
  periodo: string;
  label_periodo: string;
  receitas: {
    id: number;
    origem: string;
    valor: number;
    data: string;
    status: string;
  }[];
  reservas: {
    id: number;
    cliente: string;
    recurso: string;
    data: string;
    horario: string;
    status: string;
  }[];
  totais: {
    receitas_confirmadas: number;
    reservas_periodo: number;
  };
};

type ReservasIAInsightResponse = {
  reply: string;
};

export default function PanelReservasIA3Lab() {
  const [dadosHoje, setDadosHoje] = useState<ReservaPainelResponse | null>(null);
  const [dados7d, setDados7d] = useState<ReservaPainelResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [iaReply, setIaReply] = useState<string | null>(null);

  useEffect(() => {
    const carregar = async () => {
      try {
        setLoading(true);
        setError(null);

        const base = import.meta.env.VITE_API_BASE;
        const email = import.meta.env.VITE_USER_EMAIL;

        const makeFetch = async (periodo: string) => {
          const res = await fetch(
            `${base}/api/v1/reservas/painel?periodo=${periodo}`,
            {
              headers: {
                "X-User-Email": email ?? "",
              },
            }
          );

          if (!res.ok) {
            throw new Error(
              `Falha ao buscar painel de reservas (${periodo}, status ${res.status})`
            );
          }

          return (await res.json()) as ReservaPainelResponse;
        };

        const [hoje, seteDias] = await Promise.all([
          makeFetch("hoje"),
          makeFetch("7d"),
        ]);

        setDadosHoje(hoje);
        setDados7d(seteDias);

        // IA 3.0 – insights de reservas (LAB)
        try {
          const iaRes = await fetch(`${base}/api/v1/ai/reservas_insights_lab`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-User-Email": email ?? "",
            },
            body: JSON.stringify({ periodo: "hoje" }),
          });

          if (iaRes.ok) {
            const iaJson = (await iaRes.json()) as ReservasIAInsightResponse;
            if (iaJson && typeof iaJson.reply === "string") {
              setIaReply(iaJson.reply);
            }
          } else {
            console.warn(
              `Falha ao buscar insights da IA de reservas (status ${iaRes.status}).`
            );
          }
        } catch (iaErr) {
          console.warn("Erro ao chamar IA de reservas (LAB).", iaErr);
        }
      } catch (err) {
        console.error(err);
        setError(
          err instanceof Error
            ? err.message
            : "Erro inesperado ao carregar dados de reservas."
        );
      } finally {
        setLoading(false);
      }
    };

    carregar();
  }, []);

  const dados = dadosHoje;

  const totalReceitas = dados?.totais.receitas_confirmadas ?? 0;
  const qtdReservas = dados?.totais.reservas_periodo ?? 0;
  const ticketMedio = qtdReservas ? totalReceitas / qtdReservas : 0;

  const totalReceitasHoje = totalReceitas;
  const totalReceitas7d = dados7d?.totais.receitas_confirmadas ?? 0;
  const mediaDiaria7d =
    totalReceitas7d > 0 ? totalReceitas7d / 7 : 0;
  const variacaoPerc =
    mediaDiaria7d > 0
      ? ((totalReceitasHoje - mediaDiaria7d) / mediaDiaria7d) * 100
      : null;
  const projecaoMes =
    mediaDiaria7d > 0 ? mediaDiaria7d * 30 : 0;

  const maiorReserva = dados?.receitas.reduce<
    { origem: string; valor: number } | null
  >((acc, r) => {
    if (!acc || r.valor > acc.valor) {
      return { origem: r.origem, valor: r.valor };
    }
    return acc;
  }, null);

  const reservasConfirmadas =
    dados?.receitas.filter((r) => r.status === "confirmada").length ?? 0;
  const reservasPendentes =
    dados?.receitas.filter((r) => r.status === "pendente").length ?? 0;
  const reservasCanceladas =
    dados?.receitas.filter((r) => r.status === "cancelada").length ?? 0;

  let insightNivel = "Sem dados suficientes para analisar o dia.";
  if (!loading && !error && dados) {
    if (qtdReservas === 0 || totalReceitas === 0) {
      insightNivel =
        "Dia fraco de reservas: sem faturamento relevante nas reservas do período.";
    } else if (ticketMedio < 300) {
      insightNivel =
        "Dia moderado: volume de reservas presente, mas ticket médio ainda baixo. Há espaço para melhorar o valor das reservas.";
    } else if (ticketMedio < 700) {
      insightNivel =
        "Dia saudável: reservas com bom ticket médio. Vale acompanhar se esse padrão se mantém ao longo da semana.";
    } else {
      insightNivel =
        "Dia forte: reservas com ticket médio elevado. Ótimo momento para consolidar relacionamento com esses clientes e tentar upgrades.";
    }
  }

  const periodoLabel = dados?.label_periodo ?? "Período";
  const textoAnaliseDia = iaReply ?? insightNivel;

  return (
    <div className="w-full max-w-5xl bg-zinc-950 text-zinc-50 border border-amber-500/50 rounded-2xl p-4 md:p-6 shadow-[0_0_40px_rgba(251,191,36,0.20)]">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.25em] text-amber-400">
            Painel 3 • IA 3.0 LAB
          </p>
          <h2 className="text-lg md:text-xl font-semibold text-zinc-50">
            Inteligência de Reservas &amp; Receitas
          </h2>
          <p className="text-xs md:text-sm text-zinc-400">
            Período analisado:{" "}
            <span className="text-amber-300 font-medium">
              {periodoLabel}
            </span>
            . Dados em tempo real da API <span className="font-mono">/reservas/painel</span>.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            API ON
          </span>
          <span className="inline-flex items-center gap-1 rounded-full border border-fuchsia-400/40 bg-fuchsia-500/10 px-2 py-0.5 text-[10px] font-medium text-fuchsia-300">
            IA 3.0 • Modo Insight
          </span>
        </div>
      </div>

      {loading && (
        <p className="text-xs md:text-sm text-zinc-400">
          Carregando dados de reservas e receitas para análise inteligente...
        </p>
      )}

      {error && !loading && (
        <p className="text-xs md:text-sm text-red-400">
          Erro ao carregar dados: {error}
        </p>
      )}

      {!loading && !error && dados && (
        <div className="space-y-4">
          {/* Linha de métricas principais */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="rounded-xl border border-amber-500/40 bg-gradient-to-br from-zinc-900 via-zinc-950 to-zinc-950 p-3">
              <p className="text-[11px] text-zinc-400 uppercase tracking-wide">
                Receita do período
              </p>
              <p className="mt-1 text-lg md:text-xl font-semibold text-emerald-400">
                {totalReceitas.toLocaleString("pt-BR", {
                  style: "currency",
                  currency: "BRL",
                })}
              </p>
              <p className="mt-1 text-[11px] text-zinc-500">
                Soma das reservas confirmadas em{" "}
                <span className="text-zinc-300">{periodoLabel.toLowerCase()}</span>.
              </p>
            </div>

            <div className="rounded-xl border border-amber-500/40 bg-gradient-to-br from-zinc-900 via-zinc-950 to-zinc-950 p-3">
              <p className="text-[11px] text-zinc-400 uppercase tracking-wide">
                Ticket médio por reserva
              </p>
              <p className="mt-1 text-lg md:text-xl font-semibold text-cyan-400">
                {ticketMedio.toLocaleString("pt-BR", {
                  style: "currency",
                  currency: "BRL",
                })}
              </p>
              <p className="mt-1 text-[11px] text-zinc-500">
                Baseado em{" "}
                <span className="text-zinc-300">{qtdReservas}</span>{" "}
                reservas no período.
              </p>
            </div>

            <div className="rounded-xl border border-amber-500/40 bg-gradient-to-br from-zinc-900 via-zinc-950 to-zinc-950 p-3">
              <p className="text-[11px] text-zinc-400 uppercase tracking-wide">
                Reserva mais forte
              </p>
              {maiorReserva ? (
                <>
                  <p className="mt-1 text-xs font-medium text-zinc-50 line-clamp-2">
                    {maiorReserva.origem}
                  </p>
                  <p className="mt-1 text-lg md:text-xl font-semibold text-fuchsia-400">
                    {maiorReserva.valor.toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    })}
                  </p>
                  <p className="mt-1 text-[11px] text-zinc-500">
                    Principal contribuição para o faturamento do período.
                  </p>
                </>
              ) : (
                <p className="mt-1 text-xs text-zinc-400">
                  Ainda não há reservas com valor registrado neste período.
                </p>
              )}
            </div>
          </div>

          {/* Resumo de status e visão rápida */}
          <div className="mt-3 rounded-xl border border-amber-500/30 bg-zinc-950/60 px-3 py-2 md:px-4 md:py-3">
            <p className="text-[11px] text-zinc-400 uppercase tracking-wide mb-1">
              Resumo de reservas no período
            </p>
            <div className="flex flex-wrap gap-3 text-[11px] md:text-xs text-zinc-300">
              <span>
                Confirmadas:{" "}
                <span className="text-emerald-300 font-medium">
                  {reservasConfirmadas}
                </span>
              </span>
              <span>
                Pendentes:{" "}
                <span className="text-amber-300 font-medium">
                  {reservasPendentes}
                </span>
              </span>
              <span>
                Canceladas:{" "}
                <span className="text-red-300 font-medium">
                  {reservasCanceladas}
                </span>
              </span>
              <span>
                Total:{" "}
                <span className="text-zinc-100 font-medium">
                  {qtdReservas}
                </span>
              </span>
            </div>
            <p className="mt-2 text-[11px] md:text-xs text-zinc-400">
              Você tem{" "}
              <span className="text-zinc-100 font-medium">
                {qtdReservas}
              </span>{" "}
              reservas registradas neste período, somando{" "}
              <span className="text-emerald-300 font-medium">
                {totalReceitas.toLocaleString("pt-BR", {
                  style: "currency",
                  currency: "BRL",
                })}
              </span>
              .
            </p>
          </div>

          {/* Tendência & Projeção */}
          <div className="mt-3 rounded-xl border border-cyan-500/40 bg-gradient-to-r from-cyan-900/40 via-zinc-950 to-fuchsia-900/10 px-3 py-3 md:px-4 md:py-3">
            <p className="text-[11px] text-cyan-200 uppercase tracking-wide mb-1">
              Tendência &amp; Projeção
            </p>
            <p className="text-[11px] md:text-xs text-zinc-200">
              {variacaoPerc === null
                ? "Ainda não há base suficiente para comparar com os últimos 7 dias."
                : variacaoPerc >= 0
                ? `A receita de hoje está aproximadamente ${variacaoPerc.toFixed(
                    0
                  )}% acima da média diária dos últimos 7 dias.`
                : `A receita de hoje está aproximadamente ${Math.abs(
                    variacaoPerc
                  ).toFixed(
                    0
                  )}% abaixo da média diária dos últimos 7 dias.`}
            </p>
            {projecaoMes > 0 && (
              <p className="mt-1 text-[11px] md:text-xs text-zinc-400">
                Mantendo o ritmo médio dos últimos 7 dias, você deve fechar um
                mês típico com cerca de{" "}
                <span className="text-emerald-300 font-medium">
                  {projecaoMes.toLocaleString("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  })}
                </span>{" "}
                em reservas faturadas.
              </p>
            )}
          </div>

          {/* Card IA 3.0 – Insight textual */}
          <div className="rounded-2xl border border-fuchsia-500/50 bg-gradient-to-br from-fuchsia-900/60 via-cyan-900/40 to-zinc-950 p-4 md:p-5">
            <p className="text-[11px] uppercase tracking-[0.25em] text-fuchsia-200 mb-1">
              IA 3.0 • Análise do dia
            </p>
            <p className="text-sm md:text-base text-zinc-50 leading-relaxed whitespace-pre-line">
              {textoAnaliseDia}
            </p>
            <p className="mt-3 text-[11px] text-zinc-300 whitespace-pre-line">
              Esta é uma visão LAB, baseada apenas nos dados de reservas e
              receitas. Na versão completa, a IA 3.0 também vai cruzar
              informações de PIX, contas a pagar e histórico para recomendar
              ações práticas para o seu caixa.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

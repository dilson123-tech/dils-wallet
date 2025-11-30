import React, { useEffect, useMemo, useState } from "react";
import {
  fetchPainelReservasLab,
  type PainelReservasPeriodo,
  type PainelReservasResponseDTO,
} from "./api";

type Receita = {
  id: number;
  origem: string;
  valor: number;
  data: string;
  status: "confirmada" | "pendente";
};

type Reserva = {
  id: number;
  cliente: string;
  recurso: string;
  data: string;
  horario: string;
  status: "ativa" | "cancelada" | "concluída";
};

type Periodo = PainelReservasPeriodo;

type RecursoResumo = {
  recurso: string;
  reservas_periodo: number;
  receita_confirmada: number;
};

const receitasMock: Receita[] = [
  {
    id: 1,
    origem: "Reserva Sala Reunião 01",
    valor: 350.0,
    data: "2025-11-29",
    status: "confirmada",
  },
  {
    id: 2,
    origem: "Reserva Auditório Aurea",
    valor: 900.0,
    data: "2025-11-29",
    status: "confirmada",
  },
  {
    id: 3,
    origem: "Reserva Espaço Premium",
    valor: 520.5,
    data: "2025-11-28",
    status: "pendente",
  },
  {
    id: 4,
    origem: "Reserva Coworking Flex",
    valor: 180.0,
    data: "2025-11-23",
    status: "confirmada",
  },
  {
    id: 5,
    origem: "Reserva Estacionamento VIP",
    valor: 75.0,
    data: "2025-11-10",
    status: "confirmada",
  },
];

const reservasMock: Reserva[] = [
  {
    id: 11,
    cliente: "Empresa Alpha LTDA",
    recurso: "Sala Reunião 01",
    data: "2025-11-29",
    horario: "09:00 - 11:00",
    status: "ativa",
  },
  {
    id: 12,
    cliente: "Tech Beta Solutions",
    recurso: "Auditório Aurea",
    data: "2025-11-29",
    horario: "14:00 - 18:00",
    status: "ativa",
  },
  {
    id: 13,
    cliente: "StartUp Gama",
    recurso: "Espaço Premium",
    data: "2025-11-30",
    horario: "19:00 - 22:00",
    status: "concluída",
  },
  {
    id: 14,
    cliente: "Cowork People",
    recurso: "Coworking Flex",
    data: "2025-11-23",
    horario: "08:00 - 18:00",
    status: "concluída",
  },
  {
    id: 15,
    cliente: "Logística Delta",
    recurso: "Vaga Estacionamento VIP",
    data: "2025-11-10",
    horario: "Dia todo",
    status: "cancelada",
  },
];

const currency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
});

// mesmo conceito do backend, para destacar "hoje"
const HOJE_FIXO = "2025-11-29";

function dentroDoPeriodo(data: string, periodo: Periodo): boolean {
  if (periodo === "hoje") {
    return data === HOJE_FIXO;
  }
  if (periodo === "7d") {
    return data >= "2025-11-23";
  }
  return data >= "2025-10-30";
}

function classStatusReceita(status: Receita["status"]): string {
  if (status === "confirmada") {
    return (
      "inline-flex items-center justify-end gap-1 text-[10px] px-2 py-0.5 " +
      "rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/40"
    );
  }
  return (
    "inline-flex items-center justify-end gap-1 text-[10px] px-2 py-0.5 " +
    "rounded-full bg-amber-500/10 text-amber-200 border border-amber-500/40"
  );
}

function classStatusReserva(status: Reserva["status"]): string {
  if (status === "ativa") {
    return (
      "inline-flex items-center justify-end gap-1 text-[10px] px-2 py-0.5 " +
      "rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/40"
    );
  }
  if (status === "concluída") {
    return (
      "inline-flex items-center justify-end gap-1 text-[10px] px-2 py-0.5 " +
      "rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/40"
    );
  }
  return (
    "inline-flex items-center justify-end gap-1 text-[10px] px-2 py-0.5 " +
    "rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/40"
  );
}

export default function PanelReceitasReservasLab() {
  const [periodo, setPeriodo] = useState<Periodo>("hoje");
  const [remote, setRemote] = useState<PainelReservasResponseDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // carrega da API sempre que mudar o período
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchPainelReservasLab(periodo)
      .then((data) => {
        if (!isMounted) return;
        setRemote(data);
      })
      .catch((err) => {
        console.error("Erro ao buscar painel de reservas:", err);
        if (!isMounted) return;
        setError(
          "Falha ao carregar dados da API. Usando dados de laboratório locais."
        );
        setRemote(null);
      })
      .finally(() => {
        if (!isMounted) return;
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [periodo]);

  // fonte de dados: API se existir, senão mocks
  const receitasBase: Receita[] =
    remote?.receitas ?? (receitasMock as Receita[]);
  const reservasBase: Reserva[] =
    remote?.reservas ?? (reservasMock as Reserva[]);

  // ordenação: mais recentes primeiro, e dentro da mesma data, maior valor primeiro
  const receitasOrdenadas = useMemo(() => {
    return [...receitasBase].sort((a, b) => {
      if (a.data === b.data) {
        return b.valor - a.valor;
      }
      return a.data < b.data ? 1 : -1;
    });
  }, [receitasBase]);

  const reservasOrdenadas = useMemo(() => {
    return [...reservasBase].sort((a, b) => {
      if (a.data === b.data) {
        return a.horario.localeCompare(b.horario);
      }
      return a.data < b.data ? 1 : -1;
    });
  }, [reservasBase]);

  // fallback de totais caso API não traga nada
  const totalReceitasFallback = useMemo(() => {
    return receitasMock
      .filter(
        (r) => r.status === "confirmada" && dentroDoPeriodo(r.data, periodo)
      )
      .reduce((acc, r) => acc + r.valor, 0);
  }, [periodo]);

  const reservasPeriodoFallback = useMemo(() => {
    return reservasMock.filter((r) => dentroDoPeriodo(r.data, periodo)).length;
  }, [periodo]);

  const totais = remote?.totais ?? {
    receitas_confirmadas: totalReceitasFallback,
    reservas_periodo: reservasPeriodoFallback,
  };

  const labelPeriodoLocal =
    periodo === "hoje"
      ? "Hoje"
      : periodo === "7d"
      ? "Últimos 7 dias"
      : "Últimos 30 dias";

  const labelPeriodo = remote?.label_periodo ?? labelPeriodoLocal;

  const statusFonte =
    loading
      ? "Carregando dados da API reservas_lab..."
      : remote
      ? "Dados vindo da API reservas_lab (LAB)."
      : "Dados locais de laboratório.";

  // --- Painel 2: resumo por recurso (LAB) ---
  const resumoPorRecurso: RecursoResumo[] = useMemo(() => {
    const map = new Map<string, RecursoResumo>();

    for (const res of reservasBase) {
      if (!dentroDoPeriodo(res.data, periodo)) continue;

      let item = map.get(res.recurso);
      if (!item) {
        item = {
          recurso: res.recurso,
          reservas_periodo: 0,
          receita_confirmada: 0,
        };
        map.set(res.recurso, item);
      }

      item.reservas_periodo += 1;

      // heurística LAB: tenta achar receita ligada ao mesmo recurso e data
      const receitaMatch = receitasBase.find(
        (r) =>
          r.status === "confirmada" &&
          r.data === res.data &&
          r.origem.toLowerCase().includes(res.recurso.toLowerCase())
      );
      if (receitaMatch) {
        item.receita_confirmada += receitaMatch.valor;
      }
    }

    return Array.from(map.values()).sort(
      (a, b) => b.receita_confirmada - a.receita_confirmada
    );
  }, [reservasBase, receitasBase, periodo]);

  const totalRecursos = resumoPorRecurso.length;

  return (
    <div className="w-full flex justify-center">
      <div className="w-full max-w-5xl bg-zinc-950 text-zinc-50 border border-amber-500/50 rounded-2xl p-4 md:p-6 shadow-[0_0_40px_rgba(251,191,36,0.20)]">
        {/* Header */}
        <div className="flex flex-col gap-2 mb-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <div>
              <span className="text-[10px] uppercase tracking-[0.2em] text-amber-400/70">
                Aurea Gold • LAB
              </span>
              <h1 className="text-xl md:text-2xl font-semibold text-zinc-50">
                Painel Receitas &amp; Reservas
                <span className="ml-2 text-[11px] font-normal text-amber-400/80 align-middle">
                  (painel 1 • laboratório)
                </span>
              </h1>
              <p className="text-xs md:text-sm text-zinc-400 max-w-2xl">
                Visão rápida das receitas geradas por reservas e do uso dos
                recursos (salas, auditórios, espaços premium). Nesta versão LAB
                os dados são simulados.
              </p>
            </div>

            {/* seletor de período */}
            <div className="inline-flex items-center rounded-full border border-zinc-700 bg-zinc-900/80 p-1 text-[11px]">
              <button
                type="button"
                className={
                  "px-3 py-1 rounded-full transition " +
                  (periodo === "hoje"
                    ? "bg-amber-500 text-zinc-950 font-semibold"
                    : "text-zinc-300 hover:bg-zinc-800")
                }
                onClick={() => setPeriodo("hoje")}
              >
                Hoje
              </button>
              <button
                type="button"
                className={
                  "px-3 py-1 rounded-full transition " +
                  (periodo === "7d"
                    ? "bg-amber-500 text-zinc-950 font-semibold"
                    : "text-zinc-300 hover:bg-zinc-800")
                }
                onClick={() => setPeriodo("7d")}
              >
                7 dias
              </button>
              <button
                type="button"
                className={
                  "px-3 py-1 rounded-full transition " +
                  (periodo === "30d"
                    ? "bg-amber-500 text-zinc-950 font-semibold"
                    : "text-zinc-300 hover:bg-zinc-800")
                }
                onClick={() => setPeriodo("30d")}
              >
                30 dias
              </button>
            </div>
          </div>

          <p className="text-[11px] text-zinc-500">
            Período selecionado:{" "}
            <span className="text-amber-300 font-medium">{labelPeriodo}</span>.
            <span className="ml-2 text-[10px] text-zinc-500">
              {statusFonte}
              {error && (
                <span className="ml-1 text-rose-400 font-medium">
                  ({error})
                </span>
              )}
            </span>
          </p>
        </div>

        {/* Cards principais */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
          <div className="rounded-2xl border border-amber-500/40 bg-gradient-to-br from-zinc-900 to-zinc-950 p-4 flex flex-col gap-2 shadow-[0_0_24px_rgba(251,191,36,0.20)]">
            <span className="text-[11px] uppercase tracking-[0.18em] text-amber-400/80">
              Receitas no período
            </span>
            <div className="text-2xl md:text-3xl font-semibold text-amber-300">
              {currency.format(totais.receitas_confirmadas)}
            </div>
            <p className="text-[11px] text-zinc-400">
              Somente reservas confirmadas dentro do período selecionado.
            </p>
          </div>

          <div className="rounded-2xl border border-emerald-500/30 bg-zinc-900/80 p-4 flex flex-col gap-2">
            <span className="text-[11px] uppercase tracking-[0.18em] text-emerald-400/80">
              Reservas no período
            </span>
            <div className="text-2xl font-semibold text-emerald-300">
              {totais.reservas_periodo}
            </div>
            <p className="text-[11px] text-zinc-400">
              Quantidade de reservas registradas no período (todas as
              situações).
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-700/70 bg-zinc-900/80 p-4 flex flex-col gap-2">
            <span className="text-[11px] uppercase tracking-[0.18em] text-zinc-400/80">
              Versão
            </span>
            <div className="text-sm font-semibold text-zinc-100">
              Receitas &amp; Reservas • LAB
            </div>
            <p className="text-[11px] text-zinc-400">
              Painel isolado para experimentos. Depois conectamos ao backend
              oficial de reservas e faturamento.
            </p>
          </div>
        </div>

        {/* Tabelas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
          {/* Receitas */}
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-zinc-50">
                Receitas recentes
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded-full border border-zinc-700 text-zinc-400">
                mock • LAB / API
              </span>
            </div>

            <div className="overflow-auto text-xs">
              <table className="w-full border-collapse min-w-[420px]">
                <thead>
                  <tr className="text-[11px] text-zinc-400 border-b border-zinc-800 bg-zinc-950/60">
                    <th className="text-left py-2 pr-2 font-normal">
                      Origem
                    </th>
                    <th className="text-left py-2 px-2 font-normal">
                      Data
                    </th>
                    <th className="text-right py-2 px-2 font-normal">
                      Valor
                    </th>
                    <th className="text-right py-2 pl-2 font-normal">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {receitasOrdenadas.map((r, idx) => {
                    const isHoje = r.data === HOJE_FIXO;
                    const baseRow =
                      idx % 2 === 0
                        ? "bg-zinc-950/40"
                        : "bg-zinc-900/40";
                    const todayRing = isHoje
                      ? " ring-1 ring-amber-400/70"
                      : "";
                    const title = `Receita de reserva: ${r.origem} • ${r.data} • ${currency.format(
                      r.valor
                    )} • status: ${r.status}`;

                    return (
                      <tr
                        key={r.id}
                        className={
                          "border-b border-zinc-900/60 last:border-0 transition-colors " +
                          baseRow +
                          " hover:bg-zinc-800/70" +
                          todayRing
                        }
                        title={title}
                      >
                        <td className="py-2 pr-2 text-zinc-100">
                          {r.origem}
                        </td>
                        <td className="py-2 px-2 text-zinc-400">
                          {r.data}
                          {isHoje && (
                            <span className="ml-1 text-[9px] text-amber-300 font-semibold uppercase">
                              • hoje
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-2 text-right text-amber-300">
                          {currency.format(r.valor)}
                        </td>
                        <td className="py-2 pl-2 text-right">
                          <span className={classStatusReceita(r.status)}>
                            <span className="text-[8px]">●</span>
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Reservas */}
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4 flex flex-col min-h-0">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-zinc-50">
                Reservas de recursos
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded-full border border-zinc-700 text-zinc-400">
                visão operacional
              </span>
            </div>

            <div className="overflow-auto text-xs">
              <table className="w-full border-collapse min-w-[420px]">
                <thead>
                  <tr className="text-[11px] text-zinc-400 border-b border-zinc-800 bg-zinc-950/60">
                    <th className="text-left py-2 pr-2 font-normal">
                      Cliente
                    </th>
                    <th className="text-left py-2 px-2 font-normal">
                      Recurso
                    </th>
                    <th className="text-left py-2 px-2 font-normal">
                      Data
                    </th>
                    <th className="text-left py-2 px-2 font-normal">
                      Horário
                    </th>
                    <th className="text-right py-2 pl-2 font-normal">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {reservasOrdenadas.map((r, idx) => {
                    const isHoje = r.data === HOJE_FIXO;
                    const baseRow =
                      idx % 2 === 0
                        ? "bg-zinc-950/40"
                        : "bg-zinc-900/40";
                    const todayRing = isHoje
                      ? " ring-1 ring-amber-400/70"
                      : "";
                    const title = `Reserva: ${r.cliente} em ${r.recurso} • ${r.data} • ${r.horario} • status: ${r.status}`;

                    return (
                      <tr
                        key={r.id}
                        className={
                          "border-b border-zinc-900/60 last:border-0 transition-colors " +
                          baseRow +
                          " hover:bg-zinc-800/70" +
                          todayRing
                        }
                        title={title}
                      >
                        <td className="py-2 pr-2 text-zinc-100">
                          {r.cliente}
                        </td>
                        <td className="py-2 px-2 text-zinc-300">
                          {r.recurso}
                        </td>
                        <td className="py-2 px-2 text-zinc-400">
                          {r.data}
                          {isHoje && (
                            <span className="ml-1 text-[9px] text-amber-300 font-semibold uppercase">
                              • hoje
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-2 text-zinc-400">
                          {r.horario}
                        </td>
                        <td className="py-2 pl-2 text-right">
                          <span className={classStatusReserva(r.status)}>
                            <span className="text-[8px]">●</span>
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Painel 2 - resumo por recurso */}
        <div className="mt-6 rounded-2xl border border-amber-500/30 bg-zinc-900/80 p-4 md:p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-semibold text-zinc-50">
                Resumo por recurso
                <span className="ml-2 text-[11px] font-normal text-amber-300/80 align-middle">
                  (Painel 2 • LAB)
                </span>
              </h2>
              <p className="text-[11px] text-zinc-400 max-w-xl">
                Visão consolidada de cada recurso (sala, auditório, espaço
                premium, etc.) com quantidade de reservas no período e receita
                confirmada associada.
              </p>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full border border-amber-500/40 text-amber-300">
              {totalRecursos} recurso(s) no período
            </span>
          </div>

          {resumoPorRecurso.length === 0 ? (
            <div className="text-[11px] text-zinc-400">
              Nenhum recurso com reservas no período selecionado.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
              {resumoPorRecurso.map((item) => (
                <div
                  key={item.recurso}
                  className="rounded-2xl border border-zinc-700/70 bg-zinc-950/70 p-4 flex flex-col gap-2 shadow-[0_0_18px_rgba(24,24,27,0.7)]"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <div className="text-xs font-semibold text-zinc-50">
                        {item.recurso}
                      </div>
                      <div className="text-[10px] text-zinc-400">
                        Recurso monitorado no período selecionado.
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full border border-zinc-700 text-zinc-300">
                      {item.reservas_periodo} reserva(s)
                    </span>
                  </div>

                  <div className="flex items-end justify-between mt-1">
                    <div>
                      <div className="text-[11px] text-zinc-400">
                        Receita confirmada
                      </div>
                      <div className="text-lg font-semibold text-amber-300">
                        {currency.format(item.receita_confirmada)}
                      </div>
                    </div>
                    <div className="text-[10px] text-zinc-500 text-right">
                      * cálculo LAB com base nas reservas e receitas do painel 1.
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

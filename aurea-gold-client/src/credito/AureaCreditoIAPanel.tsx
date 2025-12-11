
import React, { useEffect, useState } from "react";
import { API_BASE, USER_EMAIL } from "../super2/api";

interface CreditoHeadline {
  entradasMes: number;
  saidasMes: number;
  saldoAtual: number;
  nivelRisco: string;
}

function formatBRL(value: number | null | undefined): string {
  const n = typeof value === "number" && !Number.isNaN(value) ? value : 0;
  return n.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function normalizeHeadline(raw: any): CreditoHeadline {
  if (!raw) {
    return {
      entradasMes: 0,
      saidasMes: 0,
      saldoAtual: 0,
      nivelRisco: "Em análise (LAB)",
    };
  }

  const base = raw.data ?? raw;

  const entradas =
    Number(
      base.entradas_mes ??
        base.entradasMes ??
        base.totalEntradas ??
        base.entradas ??
        0
    ) || 0;

  const saidas =
    Number(
      base.saidas_mes ??
        base.saidasMes ??
        base.totalSaidas ??
        base.saidas ??
        0
    ) || 0;

  const saldo =
    Number(
      base.saldo_atual ??
        base.saldoAtual ??
        base.saldo ??
        base.saldoHoje ??
        0
    ) || 0;

  const nivel =
    base.nivel_risco ??
    base.nivelRisco ??
    base.risco_label ??
    base.risco ??
    base.nivel ??
    "Em análise (LAB)";

  return {
    entradasMes: entradas,
    saidasMes: saidas,
    saldoAtual: saldo,
    nivelRisco: String(nivel),
  };
}

function buildDescricaoRisco(
  headline: CreditoHeadline | null,
  comprometimentoPix: number | null
): string {
  if (!headline) {
    return "Análise de risco ainda em modo LAB. Assim que a IA 3.0 analisar seu PIX, o nível aparecerá aqui.";
  }

  const nivelStr = headline.nivelRisco || "Em análise (LAB)";
  let classe = "1";

  const nivelLower = nivelStr.toLowerCase();

  if (nivelLower.includes("criti") || nivelLower.includes("alto")) {
    classe = "3";
  } else if (nivelLower.includes("moderado")) {
    classe = "2";
  } else if (nivelLower.includes("baixo")) {
    classe = "1";
  } else if (comprometimentoPix !== null) {
    if (comprometimentoPix <= 0.4) {
      classe = "1";
    } else if (comprometimentoPix <= 0.7) {
      classe = "2";
    } else {
      classe = "3";
    }
  }

  if (classe === "1") {
    return (
      "Nível 1A - Perfil confortável. Fluxo de PIX saudável, " +
      "gastos sob controle e espaço para crédito com mais tranquilidade."
    );
  }

  if (classe === "2") {
    return (
      "Nível 2B - Risco moderado. Há espaço para crédito, " +
      "mas é importante acompanhar o fluxo mensal e evitar novas dívidas de curto prazo."
    );
  }

  return (
    "Nível 3C - Risco elevado. O comprometimento com PIX está alto " +
    "e novas dívidas podem pressionar ainda mais o caixa. Recomenda-se reforçar reservas antes de assumir crédito."
  );
}

const AureaCreditoIAPanel: React.FC = () => {
  const [headline, setHeadline] = useState<CreditoHeadline | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [labResumo, setLabResumo] = useState<string | null>(null);
  const [simValor, setSimValor] = useState<string>("5.000,00");
  const [simPrazoMeses, setSimPrazoMeses] = useState<string>("12");
  const [simTaxaMes, setSimTaxaMes] = useState<string>("3,0");
  const [simParcela, setSimParcela] = useState<number | null>(null);
  const [simTotalJuros, setSimTotalJuros] = useState<number | null>(null);
  const [simTotalPagar, setSimTotalPagar] = useState<number | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);

        const resp = await fetch(`${API_BASE}/api/v1/ai/ai/headline-lab`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Email": USER_EMAIL,
          },
          body: JSON.stringify({
            message:
              "resumo do painel Aurea Gold para modulo de credito inteligente ia 3.0",
          }),
        });

        if (!resp.ok) {
          throw new Error("Falha ao carregar resumo PIX (headline).");
        }

        const data = await resp.json();
        const normalized = normalizeHeadline(data);

        if (!cancelled) {
          setHeadline(normalized);
          if (data && typeof data.resumo === "string") {
            setLabResumo(data.resumo);
          }
        }
      } catch (err) {
        console.error("Erro ao carregar headline de crédito IA", err);
        if (!cancelled) {
          setError(
            "Não foi possível carregar o resumo PIX neste momento. Usando valores neutros para simulação."
          );
          setHeadline(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, []);


  const handleSimular = () => {
    setSimError(null);
    setSimParcela(null);
    setSimTotalJuros(null);
    setSimTotalPagar(null);

    const valorRaw = simValor.replace(/\./g, "").replace(",", ".");
    const principal = Number(valorRaw);
    const prazo = Number(simPrazoMeses);
    const taxa = Number(simTaxaMes.replace(",", ".")) / 100;

    if (!principal || principal <= 0 || !prazo || prazo <= 0 || !taxa || taxa <= 0) {
      setSimError("Preencha um valor, prazo e taxa válidos para simular.");
      return;
    }

    const parcela = (principal * taxa) / (1 - Math.pow(1 + taxa, -prazo));
    const totalPagar = parcela * prazo;
    const totalJuros = totalPagar - principal;

    setSimParcela(parcela);
    setSimTotalPagar(totalPagar);
    setSimTotalJuros(totalJuros);
  };

  const comprometimentoPix =
    headline && headline.entradasMes > 0
      ? headline.saidasMes / headline.entradasMes
      : null;

  const limiteSugerido =
    headline && headline.entradasMes > 0
      ? Math.max(0, Math.round((headline.entradasMes * 0.3) / 100) * 100)
      : 0;

  let faixaJuros = "— % a — % a.m.";
  const nivelLower = (headline?.nivelRisco || "").toLowerCase();

  if (nivelLower.includes("baixo")) {
    faixaJuros = "1,5% a 3,0% a.m.";
  } else if (nivelLower.includes("moderado")) {
    faixaJuros = "3,0% a 5,0% a.m.";
  } else if (nivelLower.includes("alto") || nivelLower.includes("criti")) {
    faixaJuros = "5,0% a 8,0% a.m.";
  } else if (comprometimentoPix !== null) {
    if (comprometimentoPix <= 0.4) {
      faixaJuros = "1,5% a 3,0% a.m.";
    } else if (comprometimentoPix <= 0.7) {
      faixaJuros = "3,0% a 5,0% a.m.";
    } else {
      faixaJuros = "5,0% a 8,0% a.m.";
    }
  }

  const descricaoRisco = buildDescricaoRisco(headline, comprometimentoPix);

  const saldoAtual = headline?.saldoAtual ?? 0;
  const entradasMes = headline?.entradasMes ?? 0;
  const saidasMes = headline?.saidasMes ?? 0;
  const resultadoMes = entradasMes - saidasMes;

  return (
    <div className="min-h-full flex flex-col gap-4 text-zinc-50 pb-6">
      {/* Cabeçalho */}
      <header className="space-y-1">
        <h1 className="text-lg font-semibold tracking-wide text-amber-300">
          Crédito Inteligente • IA 3.0
        </h1>
        <p className="text-[11px] text-zinc-400 max-w-2xl">
          Módulo de consultoria e simulação financeira. Não é oferta de
          empréstimo real, e não realiza contratação automática. Aqui a IA
          analisa seu fluxo via PIX para sugerir limites saudáveis,
          identificar riscos e simular cenários.
        </p>
      </header>

      {/* Resumo rápido vindo do backend (IA 3.0 / headline PIX) */}
      {loading && (
        <p className="text-[11px] text-amber-300 max-w-3xl mt-1">
          Carregando resumo PIX da IA 3.0 para simulação de crédito...
        </p>
      )}
      {error && !loading && (
        <p className="text-[11px] text-red-400 max-w-3xl mt-1">
          {error}
        </p>
      )}
      {!loading && !error && (
        <div className="text-[11px] text-zinc-300 max-w-3xl mt-1 space-y-1">
          <div>
            <span className="font-semibold">Visão rápida IA 3.0: </span>
            saldo {formatBRL(saldoAtual)}, entradas do mês {formatBRL(entradasMes)},
            saídas do mês {formatBRL(saidasMes)}.{" "}
            <span className="font-semibold">Nível de risco atual:</span>{" "}
            {headline?.nivelRisco || "Em análise (LAB)"}.
          </div>
          {labResumo && (
            <div className="text-[10px] text-amber-300">
              {labResumo}
            </div>
          )}
        </div>
      )}


      {/* Visão geral do fluxo PIX */}
      <section className="rounded-xl border border-amber-500/40 bg-black/60 p-3 space-y-2 text-[11px]">
        <div className="flex items-center justify-between">
          <h2 className="text-[12px] font-semibold text-amber-300">
            Visão geral do fluxo PIX
          </h2>
          <span className="text-[10px] uppercase tracking-[0.18em] text-amber-400">
            Modo simulação
          </span>
        </div>

        <p className="text-zinc-300">
          A IA avalia entradas, saídas, concentração de gastos e comportamento
          mensal para projetar sua capacidade de crédito.
        </p>

        {loading && (
          <p className="text-[10px] text-zinc-400">
            Carregando dados do PIX para análise de crédito...
          </p>
        )}

        {error && <p className="text-[10px] text-amber-300">{error}</p>}

        <div className="mt-2 border border-zinc-700/70 rounded-lg divide-y divide-zinc-700/60">
          <div className="grid grid-cols-2 text-[11px]">
            <div className="px-2 py-2 border-r border-zinc-700/60">
              <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
                Saldo atual estimado
              </div>
              <div className="mt-1 text-sm font-semibold">
                {formatBRL(saldoAtual)}
              </div>
            </div>
            <div className="px-2 py-2">
              <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
                Resultado do mês
              </div>
              <div
                className={`mt-1 text-sm font-semibold ${
                  resultadoMes >= 0 ? "text-emerald-300" : "text-rose-300"
                }`}
              >
                {formatBRL(resultadoMes)}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 text-[11px]">
            <div className="px-2 py-2 border-r border-zinc-700/60">
              <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
                Entradas no mês
              </div>
              <div className="mt-1 font-semibold">
                {formatBRL(entradasMes)}
              </div>
            </div>
            <div className="px-2 py-2">
              <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
                Saídas no mês
              </div>
              <div className="mt-1 font-semibold">
                {formatBRL(saidasMes)}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Análise de risco */}
      <section className="rounded-xl border border-amber-500/40 bg-black/60 p-3 space-y-2 text-[11px]">
        <h2 className="text-[12px] font-semibold text-amber-300">
          Análise de risco (IA 3.0)
        </h2>
        <p className="text-zinc-300">
          A IA classifica o risco do cliente (baixo, moderado, alto) com base no
          histórico de PIX, estabilidade de entradas e comportamento de gastos
          recorrentes.
        </p>

        <div className="mt-2 border border-zinc-700/70 rounded-lg p-2 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-[0.18em] text-zinc-400">
              Nível de risco atual
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full border border-amber-500/60 text-amber-300">
              {headline?.nivelRisco || "Em análise (LAB)"}
            </span>
          </div>
          <p className="text-[11px] text-zinc-200">{descricaoRisco}</p>
          {comprometimentoPix !== null && (
            <p className="text-[10px] text-zinc-400">
              Aproximadamente {(comprometimentoPix * 100).toFixed(0)}% das
              entradas do mês estão comprometidas com saídas via PIX.
            </p>
          )}
        </div>

        <p className="text-[10px] text-zinc-400">
          Nesta fase inicial, mostramos apenas a visão consultiva. Em etapas
          futuras, podemos conectar diretamente com o mesmo motor de IA que
          responde pelo consultor financeiro da Aurea Gold.
        </p>
      </section>

      {/* Limite sugerido & faixa de juros */}
      <section className="rounded-xl border border-amber-500/40 bg-black/60 p-3 space-y-2 text-[11px]">
        <h2 className="text-[12px] font-semibold text-amber-300">
          Limite sugerido & faixa de juros
        </h2>
        <p className="text-zinc-300">
          A IA sugere um limite de crédito saudável e uma faixa de juros
          recomendada, considerando o risco e o fluxo PIX. Os valores abaixo são
          apenas simulações internas da Aurea Gold, não sendo uma oferta de
          crédito.
        </p>

        <div className="mt-2 grid grid-cols-2 gap-2 text-[11px]">
          <div className="rounded-lg border border-zinc-700/70 p-2 space-y-1">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-400">
              Limite indicado*
            </div>
            <div className="text-sm font-semibold">
              {formatBRL(limiteSugerido)}
            </div>
            <p className="text-[10px] text-zinc-400">
              Estimativa baseada em parte das suas entradas via PIX. Quanto
              maior a previsibilidade, maior pode ser o limite.
            </p>
          </div>

          <div className="rounded-lg border border-zinc-700/70 p-2 space-y-1">
            <div className="text-[10px] uppercase tracking-[0.18em] text-zinc-400">
              Faixa de juros
            </div>
            <div className="text-sm font-semibold">{faixaJuros}</div>
            <p className="text-[10px] text-zinc-400">
              Faixa sugerida a partir do perfil de risco. Juros mais baixos
              exigem maior estabilidade de recebimentos e menor probabilidade de
              inadimplência.
            </p>
          </div>
        </div>
        {simError && (
          <p className="mt-2 text-[10px] text-red-400">{simError}</p>
        )}

        {simParcela !== null && simTotalPagar !== null && simTotalJuros !== null && (
          <div className="mt-3 rounded-lg border border-amber-500/60 bg-black/70 p-2 text-[10px] space-y-1">
            <div className="font-semibold text-amber-300">Resultado da simulação</div>
            <div>Parcela aproximada: {formatBRL(simParcela || 0)}</div>
            <div>Total em juros: {formatBRL(simTotalJuros || 0)}</div>
            <div>Total a pagar: {formatBRL(simTotalPagar || 0)}</div>
          </div>
        )}

        <div className="mt-2 rounded-lg border border-emerald-500/40 bg-emerald-500/5 p-2 space-y-1 text-[9px]">
          <div className="font-semibold text-emerald-300">
            Parecer de saúde do crédito • IA 3.0
          </div>
          <p className="text-zinc-200">
            Use este resultado como um raio-x consultivo do seu crédito: quanto
            maior a parcela em relação à sua renda mensal, maior o risco de
            aperto no caixa.
          </p>
          <ul className="list-disc list-inside text-zinc-300 space-y-0.5">
            <li>Busque manter todas as parcelas de crédito abaixo de 25–30% da renda.</li>
            <li>Compare a taxa mensal simulada com a faixa sugerida ({faixaJuros}).</li>
            <li>Se a parcela ficar pesada, ajuste valor solicitado, prazo ou repense o crédito.</li>
          </ul>
          {(() => {
            if (!simParcela || !limiteSugerido) return null;
            const ratio = simParcela / limiteSugerido;

            let nivel = "Saúde do crédito: BAIXO COMPROMETIMENTO";
            let classe = "text-emerald-300";
            let detalhe = "Parcela leve em relação ao limite sugerido. Perfil mais confortável.";

            if (ratio >= 0.25 && ratio < 0.4) {
              nivel = "Saúde do crédito: COMPROMETIMENTO MÉDIO";
              classe = "text-amber-300";
              detalhe = "Parcela começa a pesar. Vale revisar gastos e evitar novos créditos.";
            } else if (ratio >= 0.4) {
              nivel = "Saúde do crédito: COMPROMETIMENTO ALTO";
              classe = "text-red-300";
              detalhe = "Risco elevado de aperto no caixa. Considere reduzir valor ou alongar prazo.";
            }

            return (
              <div className="mt-1">
                <div className={`font-semibold ${classe}`}>
                  {nivel}
                </div>
                <p className="text-zinc-300">
                  {detalhe}
                </p>
              </div>
            );
          })()}
          <p className="text-zinc-400">
            Este módulo é apenas consultivo. Nenhum crédito será contratado
            automaticamente pela Aurea Gold a partir desta tela.
          </p>
        </div>

      </section>

      {/* Simulação rápida */}
      <section className="rounded-xl border border-amber-500/40 bg-black/60 p-3 space-y-3 text-[11px]">
        <h2 className="text-[12px] font-semibold text-amber-300">
          Simulação rápida
        </h2>
        <p className="text-zinc-300">
          Simule um valor de crédito, prazo em meses e uma taxa mensal dentro da
          faixa sugerida para ver parcela aproximada e impacto no fluxo.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <div className="space-y-1">
            <label className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
              Valor desejado (R$)
            </label>
            <input
              type="text"
              value={simValor}
              onChange={(e) => setSimValor(e.target.value)}
              placeholder="Ex.: 5.000,00"
              className="w-full rounded-md border border-zinc-700 bg-black/60 px-2 py-1 text-[11px] outline-none focus:border-amber-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
              Prazo (meses)
            </label>
            <input
              type="number"
              min={1}
              max={60}
              value={simPrazoMeses}
              onChange={(e) => setSimPrazoMeses(e.target.value)}
              className="w-full rounded-md border border-zinc-700 bg-black/60 px-2 py-1 text-[11px] outline-none focus:border-amber-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
              Taxa mensal (%)
            </label>
            <input
              type="number"
              step="0.1"
              min={0.5}
              max={10}
              value={simTaxaMes}
              onChange={(e) => setSimTaxaMes(e.target.value)}
              className="w-full rounded-md border border-zinc-700 bg-black/60 px-2 py-1 text-[11px] outline-none focus:border-amber-500"
            />
            <p className="text-[9px] text-zinc-500">
              Use um valor dentro da faixa sugerida: {faixaJuros}
            </p>
          </div>
        </div>

        {simError && (
          <p className="text-[10px] text-rose-300">
            {simError}
          </p>
        )}

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mt-1">
          <button
            type="button"
            onClick={handleSimular}
            className="w-full md:w-auto rounded-full border border-amber-500/80 bg-amber-500/20 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-200 hover:bg-amber-500/30 transition"
          >
            Simular parcelas
          </button>
          <button
            type="button"
            onClick={() => {
              setSimValor("");
              setSimPrazoMeses("12");
              setSimTaxaMes("3.0");
              setSimParcela(null);
              setSimTotalJuros(null);
              setSimTotalPagar(null);
              setSimError(null);
            }}
            className="w-full md:w-auto rounded-full border border-zinc-600 bg-black/40 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-zinc-300 hover:bg-zinc-800/80 transition"
          >
            Limpar
          </button>
        </div>

        {(simParcela !== null || simTotalPagar !== null) && (
          <div className="mt-3 border border-zinc-700/70 rounded-lg p-2 grid grid-cols-1 md:grid-cols-3 gap-2 text-[11px]">
            <div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
                Parcela aproximada
              </div>
              <div className="mt-1 font-semibold">
                {simParcela !== null ? formatBRL(simParcela) : "--"}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
                Total em juros
              </div>
              <div className="mt-1 font-semibold">
                {simTotalJuros !== null ? formatBRL(simTotalJuros) : "--"}
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-zinc-400">
                Total a pagar
              </div>
              <div className="mt-1 font-semibold">
                {simTotalPagar !== null ? formatBRL(simTotalPagar) : "--"}
              </div>
            </div>
          </div>
        )}

        <p className="text-[9px] text-zinc-500 mt-1">
          Simulação consultiva. Valores aproximados, sem contratação automática
          de crédito pela Aurea Gold.
        </p>
      </section>
    </div>
  );
};

export default AureaCreditoIAPanel;

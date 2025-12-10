
import React, { useEffect, useState } from "react";

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

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);

        const resp = await fetch("/api/v1/ia/headline-lab", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Email": "dilsonpereira231@gmail.com",
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

        <p className="text-[9px] text-zinc-500 mt-1">
          *Valores consultivos. Nenhum crédito será contratado automaticamente
          pela Aurea Gold a partir desta tela.
        </p>
      </section>

      {/* Simulação rápida */}
      <section className="rounded-xl border border-amber-500/40 bg-black/60 p-3 space-y-2 text-[11px]">
        <h2 className="text-[12px] font-semibold text-amber-300">
          Simulação rápida
        </h2>
        <p className="text-zinc-300">
          Nesta área vamos permitir que o cliente simule valores, prazos e veja
          o impacto no fluxo mensal. Por enquanto, esta é apenas uma prévia
          visual.
        </p>

        <button
          type="button"
          disabled
          className="mt-2 w-full rounded-full border border-amber-500/80 bg-amber-500/10 py-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-300 cursor-not-allowed"
        >
          Em breve: simulação com IA
        </button>

        <p className="text-[9px] text-zinc-500 mt-1">
          Este módulo é apenas consultivo. Nenhum crédito será contratado
          automaticamente pela Aurea Gold a partir desta tela.
        </p>
      </section>
    </div>
  );
};

export default AureaCreditoIAPanel;

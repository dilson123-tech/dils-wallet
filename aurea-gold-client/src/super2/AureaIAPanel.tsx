import React from "react";

/**
 * AureaIAPanel
 *
 * Painel oficial da IA 3.0 dentro do app Aurea Gold.
 * Aqui vamos concentrar:
 *  - visão de consultor financeiro
 *  - atalhos de perguntas
 *  - resumo inteligente da conta
 *  - acesso ao chat completo de IA (fase 2)
 */
export default function AureaIAPanel() {
  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* HEADER */}
      <header className="mb-4">
        <div className="text-[10px] uppercase tracking-wide text-zinc-400">
          Aurea Gold • IA 3.0 premium
        </div>
        <h1 className="text-lg md:text-xl font-semibold text-amber-300 mt-1">
          IA 3.0 • Consultor financeiro Aurea
        </h1>
        <p className="text-xs text-zinc-400 mt-1 max-w-xl">
          Esta é a área dedicada à inteligência artificial do app Aurea Gold.
          Aqui o cliente fala com a IA, recebe resumos, alertas e recomendações
          sobre a vida financeira.
        </p>
        <div className="h-px w-32 bg-amber-500 mt-3" />
      </header>

      {/* CARDS RESUMO */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
        <div className="rounded-xl border border-amber-500/40 bg-zinc-950/80 p-3">
          <div className="text-[10px] uppercase tracking-wide text-zinc-400 mb-1">
            Resumo do mês
          </div>
          <p className="text-[11px] text-zinc-200">
            A IA 3.0 vai gerar um resumo em linguagem clara sobre entradas,
            saídas e saldo do PIX no mês.
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-emerald-300 mb-1">
            Oportunidades
          </div>
          <p className="text-[11px] text-emerald-100/80">
            Sugestões de economia, reserva e ajustes no fluxo de caixa pessoal
            ou da empresa.
          </p>
        </div>

        <div className="rounded-xl border border-sky-500/40 bg-sky-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-sky-300 mb-1">
            Alertas
          </div>
          <p className="text-[11px] text-sky-100/80">
            Alertas de risco de atrasos, concentração de gastos e comportamentos
            fora do padrão.
          </p>
        </div>
      </section>

      {/* ATALHOS DE PERGUNTAS */}
      <section className="mb-4">
        <h2 className="text-[11px] uppercase tracking-wide text-zinc-400 mb-2">
          Atalhos de conversa com a IA
        </h2>
        <div className="flex flex-wrap gap-2">
          <button className="px-3 py-2 rounded-full bg-amber-500 text-black text-[11px] font-semibold uppercase tracking-wide">
            Analisar meu mês
          </button>
          <button className="px-3 py-2 rounded-full border border-amber-500/60 text-amber-300 text-[11px] uppercase tracking-wide">
            Tenho risco de atrasar contas?
          </button>
          <button className="px-3 py-2 rounded-full border border-zinc-700 text-zinc-200 text-[11px] uppercase tracking-wide">
            Onde estou gastando mais?
          </button>
          <button className="px-3 py-2 rounded-full border border-zinc-700 text-zinc-200 text-[11px] uppercase tracking-wide">
            Sugira um plano de ação
          </button>
        </div>
      </section>

      {/* BLOCO CHAT / FUTURA INTEGRAÇÃO */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
        <div className="text-[11px] font-semibold text-zinc-200 mb-1">
          Chat de IA 3.0 (em breve)
        </div>
        <p className="text-[11px] text-zinc-400 mb-2">
          Aqui vamos integrar o chat completo da IA 3.0 da Aurea Gold, com
          contexto financeiro do usuário e histórico de PIX.
        </p>
        <div className="h-20 rounded-lg border border-dashed border-zinc-700 bg-black/40 flex items-center justify-center text-[11px] text-zinc-500">
          Área reservada para o chat da IA 3.0.
        </div>
      </section>
    </div>
  );
}

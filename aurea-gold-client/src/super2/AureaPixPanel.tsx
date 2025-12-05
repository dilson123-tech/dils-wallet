import React from "react";

/**
 * AureaPixPanel
 *
 * Primeira versão do painel oficial de PIX do aplicativo Aurea Gold.
 * Aqui vamos, aos poucos, plugar:
 *  - saldo PIX
 *  - entradas / saídas
 *  - gráficos
 *  - atalhos de envio e cobrança
 */
export default function AureaPixPanel() {
  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* HEADER */}
      <header className="mb-4">
        <div className="text-[10px] uppercase tracking-wide text-zinc-400">
          Aurea Gold • Área PIX oficial
        </div>
        <h1 className="text-lg md:text-xl font-semibold text-amber-300 mt-1">
          PIX • Carteira Aurea Gold
        </h1>
        <p className="text-xs text-zinc-400 mt-1 max-w-xl">
          Essa é a visão dedicada do PIX no app Aurea Gold. Vamos evoluir este
          painel para ser a central de transferências, extrato rápido e atalhos.
        </p>
        <div className="h-px w-32 bg-amber-500 mt-3" />
      </header>

      {/* CARDS PRINCIPAIS */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
        <div className="rounded-xl border border-amber-500/40 bg-zinc-950/80 p-3">
          <div className="text-[10px] uppercase tracking-wide text-zinc-400 mb-1">
            Saldo PIX
          </div>
          <div className="text-2xl font-semibold text-amber-300">
            R$ 0,00
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">
            Em breve, esse valor será carregado diretamente do backend Aurea
            Gold, mostrando o saldo em tempo real.
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-emerald-300 mb-1">
            Entradas do mês
          </div>
          <div className="text-lg font-semibold text-emerald-300">
            R$ 0,00
          </div>
          <p className="text-[11px] text-emerald-200/80 mt-1">
            Aqui vamos exibir o total de PIX recebidos no mês atual.
          </p>
        </div>

        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-rose-300 mb-1">
            Saídas do mês
          </div>
          <div className="text-lg font-semibold text-rose-300">
            R$ 0,00
          </div>
          <p className="text-[11px] text-rose-200/80 mt-1">
            Aqui vamos exibir o total de PIX enviados no mês atual.
          </p>
        </div>
      </section>

      {/* AÇÕES RÁPIDAS */}
      <section className="mb-4">
        <h2 className="text-[11px] uppercase tracking-wide text-zinc-400 mb-2">
          Ações rápidas
        </h2>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="px-3 py-2 rounded-full bg-amber-500 text-black text-[11px] font-semibold uppercase tracking-wide"
          >
            Enviar PIX
          </button>
          <button
            type="button"
            className="px-3 py-2 rounded-full border border-amber-500/60 text-amber-300 text-[11px] uppercase tracking-wide"
          >
            Cobrar via PIX
          </button>
          <button
            type="button"
            className="px-3 py-2 rounded-full border border-zinc-700 text-zinc-200 text-[11px] uppercase tracking-wide"
          >
            Ver extrato PIX
          </button>
        </div>
      </section>

      {/* AVISO LAB */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
        <div className="text-[11px] font-semibold text-zinc-200 mb-1">
          Modo LAB ativado
        </div>
        <p className="text-[11px] text-zinc-400">
          Essa tela ainda está em modo laboratório. Os dados estão estáticos,
          servindo como guia visual. Na próxima fase, vamos plugar o backend
          de PIX e a IA 3.0 para análise automática dos movimentos.
        </p>
      </section>
    </div>
  );
}

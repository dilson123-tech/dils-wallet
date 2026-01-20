import React, { useState } from "react";

/**
 * AureaPagamentosPanel
 *
 * Painel oficial de Pagamentos dentro do app Aurea Gold.
 * Aqui vamos concentrar:
 *  - contas a pagar
 *  - assinaturas
 *  - boletos
 *  - histórico de pagamentos
 */
type PagAction = "add-bill" | "subscription" | "boleto" | null;

export default function AureaPagamentosPanel() {
  const [activeAction, setActiveAction] = useState<PagAction>(null);

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* HEADER */}
      <header className="mb-4">
        <div className="text-[10px] uppercase tracking-wide text-zinc-400">
          Aurea Gold • Pagamentos & Contas
        </div>
        <h1 className="text-lg md:text-xl font-semibold text-amber-300 mt-1">
          Pagamentos • Central Aurea Gold
        </h1>
        <p className="text-xs text-zinc-400 mt-1 max-w-xl">
          Esta é a área dedicada a contas, boletos, assinaturas e histórico de
          pagamentos. Aqui o cliente organiza o que precisa pagar e acompanha
          tudo em um só lugar.
        </p>
        <div className="h-px w-32 bg-amber-500 mt-3" />
      </header>

      {/* CARDS PRINCIPAIS */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
        <div className="rounded-xl border border-amber-500/40 bg-zinc-950/80 p-3">
          <div className="text-[10px] uppercase tracking-wide text-zinc-400 mb-1">
            Contas deste mês
          </div>
          <div className="text-2xl font-semibold text-amber-300">
            R$ 0,00
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">
            Vamos listar aqui as contas com vencimento no mês atual, com
            integração futura ao backend de pagamentos e à IA 3.0.
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-emerald-300 mb-1">
            Assinaturas ativas
          </div>
          <div className="text-lg font-semibold text-emerald-300">
            0 serviços
          </div>
          <p className="text-[11px] text-emerald-100/80 mt-1">
            Espaço reservado para Netflix, Spotify, ferramentas de trabalho e
            outras assinaturas recorrentes.
          </p>
        </div>

        <div className="rounded-xl border border-sky-500/40 bg-sky-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-sky-300 mb-1">
            Boletos gerados
          </div>
          <div className="text-lg font-semibold text-sky-300">
            0 em aberto
          </div>
          <p className="text-[11px] text-sky-100/80 mt-1">
            Aqui vamos mostrar boletos emitidos pelo Aurea Gold, com status de
            pago, em aberto e vencido.
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
            onClick={() => setActiveAction("add-bill")}
            className={`px-3 py-2 rounded-full text-[11px] font-semibold uppercase tracking-wide transition active:scale-[0.97] ${
              activeAction === "add-bill"
                ? "bg-amber-500 text-black shadow-[0_0_18px_rgba(251,191,36,0.6)]"
                : "bg-amber-500 text-black/90"
            }`}
          >
            Adicionar conta
          </button>
          <button
            type="button"
            onClick={() => setActiveAction("subscription")}
            className={`px-3 py-2 rounded-full text-[11px] uppercase tracking-wide transition active:scale-[0.97] ${
              activeAction === "subscription"
                ? "border border-emerald-400 bg-black text-emerald-200 shadow-[0_0_14px_rgba(52,211,153,0.5)]"
                : "border border-amber-500/60 text-amber-300 bg-transparent"
            }`}
          >
            Registrar assinatura
          </button>
          <button
            type="button"
            onClick={() => setActiveAction("boleto")}
            className={`px-3 py-2 rounded-full text-[11px] uppercase tracking-wide transition active:scale-[0.97] ${
              activeAction === "boleto"
                ? "border border-sky-300 bg-zinc-900 text-sky-200"
                : "border border-zinc-700 text-zinc-200 bg-transparent"
            }`}
          >
            Gerar boleto (futuro)
          </button>
        </div>

        {/* DETALHES DA AÇÃO SELECIONADA */}
        <div className="mt-3 rounded-xl border border-zinc-800 bg-black/50 p-3 text-[11px] text-zinc-200">
          {!activeAction && (
            <p className="text-zinc-400">
              Toque em uma das ações rápidas para ver os detalhes aqui. Este
              bloco será a base dos formulários e fluxos reais de pagamento do
              Aurea Gold.
            </p>
          )}

          {activeAction === "add-bill" && (
            <>
              <h3 className="font-semibold text-amber-300 mb-1">
                Adicionar conta (modo LAB)
              </h3>
              <p className="text-zinc-300 mb-1">
                Aqui o cliente vai poder cadastrar contas a pagar:
              </p>
              <ul className="list-disc list-inside text-zinc-300 space-y-1">
                <li>nome da conta (água, luz, internet, fornecedor etc.);</li>
                <li>valor e data de vencimento;</li>
                <li>opção de lembrete antecipado;</li>
                <li>marcar como paga depois do pagamento.</li>
              </ul>
              <p className="text-zinc-400 mt-2">
                Na próxima fase, vamos integrar isso ao backend e à IA 3.0 para
                avisar sobre risco de atraso.
              </p>
            </>
          )}

          {activeAction === "subscription" && (
            <>
              <h3 className="font-semibold text-emerald-300 mb-1">
                Registrar assinatura (modo LAB)
              </h3>
              <p className="text-zinc-300 mb-1">
                Espaço dedicado para assinaturas recorrentes:
              </p>
              <ul className="list-disc list-inside text-zinc-300 space-y-1">
                <li>serviços como streaming, SaaS, ferramentas de trabalho;</li>
                <li>valor mensal, data de cobrança e forma de pagamento;</li>
                <li>status ativa/pausada/cancelada;</li>
                <li>resumo mensal do impacto no fluxo de caixa.</li>
              </ul>
              <p className="text-zinc-400 mt-2">
                A IA 3.0 poderá sugerir cortes, renegociações ou alertar sobre
                assinaturas pouco usadas.
              </p>
            </>
          )}

          {activeAction === "boleto" && (
            <>
              <h3 className="font-semibold text-sky-300 mb-1">
                Gerar boleto (futuro)
              </h3>
              <p className="text-zinc-300 mb-1">
                Nesta área vamos integrar com o parceiro financeiro para:
              </p>
              <ul className="list-disc list-inside text-zinc-300 space-y-1">
                <li>emitir boletos para clientes;</li>
                <li>acompanhar status (pago, em aberto, vencido);</li>
                <li>ligar o recebimento direto na carteira Aurea Gold;</li>
                <li>gerar relatórios de cobrança.</li>
              </ul>
              <p className="text-zinc-400 mt-2">
                Tudo pensado para empresas que querem usar o Aurea Gold como
                hub de recebimentos.
              </p>
            </>
          )}
        </div>
      </section>

      {/* MODO LAB / ROADMAP */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
        <div className="text-[11px] font-semibold text-zinc-200 mb-1">
          Modo LAB de Pagamentos
        </div>
        <p className="text-[11px] text-zinc-400 mb-1">
          Este painel ainda está em modo laboratório. Os dados são estáticos e
          servem como guia visual do produto final.
        </p>
        <p className="text-[11px] text-zinc-400">
          Próximos passos: integração com backend de pagamentos, IA 3.0
          analisando risco de atraso e avisos pro cliente diretamente nesta
          tela.
        </p>
      </section>
    </div>
  );
}

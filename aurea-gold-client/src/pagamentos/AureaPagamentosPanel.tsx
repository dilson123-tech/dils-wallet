import React, { useState } from "react";

type PagAction = "add-bill" | "subscription" | "boleto" | null;

export default function AureaPagamentosPanel() {
  const [activeAction, setActiveAction] = useState<PagAction>(null);

  return (
    <section className="w-full max-w-[960px] mx-auto space-y-5 md:space-y-6">
      <header className="ag-surface-elevated px-4 py-5 sm:px-5 sm:py-6">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
          Aurea Gold • Pagamentos
        </div>
        <h1 className="mt-2 text-[1.45rem] sm:text-2xl md:text-3xl font-bold text-[#f4f8ff] leading-tight">
          Central de pagamentos da carteira
        </h1>
        <p className="mt-2 text-sm text-[#bfd0ec] max-w-2xl">
          Contas, boletos, assinaturas e rotinas financeiras do cliente em uma
          área única, com base pronta para evolução operacional real.
        </p>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4">
        <article className="ag-card rounded-[22px] px-4 py-4 sm:px-5 sm:py-5 border border-sky-500/20 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[#86c0ff]">
            Contas deste mês
          </div>
          <div className="mt-2 text-2xl font-semibold text-[#f4f8ff]">
            R$ 0,00
          </div>
          <p className="mt-2 text-[11px] text-[#bfd0ec]">
            Aqui vamos concentrar vencimentos, alertas e compromissos do mês.
          </p>
        </article>

        <article className="ag-card rounded-[22px] px-4 py-4 sm:px-5 sm:py-5 border border-emerald-500/20 bg-[linear-gradient(180deg,rgba(8,34,34,0.96),rgba(7,22,22,0.98))]">
          <div className="text-[10px] uppercase tracking-[0.14em] text-emerald-300">
            Assinaturas
          </div>
          <div className="mt-2 text-xl font-semibold text-[#f4f8ff]">
            0 serviços ativos
          </div>
          <p className="mt-2 text-[11px] text-[#bfd0ec]">
            Streaming, ferramentas de trabalho e despesas recorrentes.
          </p>
        </article>

        <article className="ag-card rounded-[22px] px-4 py-4 sm:px-5 sm:py-5 border border-sky-400/20 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]">
          <div className="text-[10px] uppercase tracking-[0.14em] text-sky-300">
            Boletos gerados
          </div>
          <div className="mt-2 text-xl font-semibold text-[#f4f8ff]">
            0 em aberto
          </div>
          <p className="mt-2 text-[11px] text-[#bfd0ec]">
            Emissão, acompanhamento e histórico de cobrança da carteira.
          </p>
        </article>
      </section>

      <section className="ag-card rounded-[24px] px-4 py-5 sm:px-5 sm:py-6 border border-sky-500/20 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
          Ações rápidas
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setActiveAction("add-bill")}
            className={`px-3 py-2 rounded-full text-[11px] font-semibold uppercase tracking-[0.12em] transition active:scale-[0.97] ${
              activeAction === "add-bill"
                ? "bg-[linear-gradient(135deg,#5aa0ff,#86c0ff)] text-[#06101f] shadow-[0_0_18px_rgba(90,160,255,0.35)]"
                : "border border-sky-500/40 bg-sky-500/10 text-sky-100"
            }`}
          >
            Adicionar conta
          </button>

          <button
            type="button"
            onClick={() => setActiveAction("subscription")}
            className={`px-3 py-2 rounded-full text-[11px] font-semibold uppercase tracking-[0.12em] transition active:scale-[0.97] ${
              activeAction === "subscription"
                ? "bg-[linear-gradient(135deg,#5aa0ff,#86c0ff)] text-[#06101f] shadow-[0_0_18px_rgba(90,160,255,0.35)]"
                : "border border-sky-500/40 bg-sky-500/10 text-sky-100"
            }`}
          >
            Assinaturas
          </button>

          <button
            type="button"
            onClick={() => setActiveAction("boleto")}
            className={`px-3 py-2 rounded-full text-[11px] font-semibold uppercase tracking-[0.12em] transition active:scale-[0.97] ${
              activeAction === "boleto"
                ? "bg-[linear-gradient(135deg,#5aa0ff,#86c0ff)] text-[#06101f] shadow-[0_0_18px_rgba(90,160,255,0.35)]"
                : "border border-sky-500/40 bg-sky-500/10 text-sky-100"
            }`}
          >
            Cobrança por boleto
          </button>
        </div>

        <div className="mt-4 rounded-[18px] border border-sky-500/18 bg-[rgba(8,18,35,0.74)] px-4 py-4 text-sm text-[#bfd0ec]">
          {!activeAction && (
            <p>
              Selecione uma ação para abrir a base operacional desta área. Aqui
              vamos concentrar formulários, alertas e rotinas de pagamento da
              Aurea.
            </p>
          )}

          {activeAction === "add-bill" && (
            <div className="space-y-2">
              <h3 className="text-base font-semibold text-[#f4f8ff]">
                Adicionar conta
              </h3>
              <p>
                Fluxo para cadastrar conta a pagar, valor, vencimento, lembrete
                e status de pagamento.
              </p>
            </div>
          )}

          {activeAction === "subscription" && (
            <div className="space-y-2">
              <h3 className="text-base font-semibold text-[#f4f8ff]">
                Assinaturas recorrentes
              </h3>
              <p>
                Espaço para organizar serviços mensais, acompanhar impacto no
                caixa e preparar alertas automáticos.
              </p>
            </div>
          )}

          {activeAction === "boleto" && (
            <div className="space-y-2">
              <h3 className="text-base font-semibold text-[#f4f8ff]">
                Cobrança com boleto
              </h3>
              <p>
                Base da emissão e acompanhamento de boletos para clientes,
                conectada ao recebimento da carteira.
              </p>
            </div>
          )}
        </div>
      </section>

      <section className="ag-hero px-4 py-5 sm:px-5 sm:py-6 rounded-[28px] border border-sky-500/30 bg-[radial-gradient(circle_at_top_right,rgba(134,192,255,0.16),transparent_20%),linear-gradient(180deg,rgba(10,20,40,0.98),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
          Direção do produto
        </div>
        <h2 className="mt-2 text-xl font-semibold text-[#f4f8ff]">
          Pagamentos como módulo real da Aurea
        </h2>
        <p className="mt-2 text-sm text-[#bfd0ec] max-w-3xl">
          Esta aba deixa de ser painel de rascunho e passa a ser a central de
          contas, boletos, rotinas recorrentes e gestão financeira do cliente.
        </p>
      </section>
    </section>
  );
}

import React from "react";

const gestaoCards = [
  {
    title: "Simulador de taxas",
    subtitle: "Entenda custos e margens das vendas",
    badge: "Operação",
  },
  {
    title: "Link de pagamento",
    subtitle: "Cobrança rápida para clientes por link",
    badge: "Cobrança",
  },
  {
    title: "Cobrar com QR",
    subtitle: "Gere cobrança instantânea com QR Code",
    badge: "PIX",
  },
  {
    title: "Tap to Pay parceiro",
    subtitle: "Aceite pagamento com parceiro homologado",
    badge: "Presencial",
  },
  {
    title: "Recebimentos",
    subtitle: "Acompanhe entradas e liquidações do negócio",
    badge: "Fluxo",
  },
  {
    title: "Taxas especiais",
    subtitle: "Condições comerciais conforme seu volume",
    badge: "Comercial",
  },
];

export default function AureaGestaoPanel() {
  return (
    <section className="w-full max-w-[960px] mx-auto space-y-5 md:space-y-6">
      <header className="ag-surface-elevated px-4 py-5 sm:px-5 sm:py-6">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
          Aurea Gold • Gestão
        </div>
        <h1 className="mt-2 text-[1.45rem] sm:text-2xl md:text-3xl font-bold text-[#f4f8ff] leading-tight">
          Ferramentas do seu negócio
        </h1>
        <p className="mt-2 text-sm text-[#bfd0ec] max-w-2xl">
          Área operacional da Aurea para vendas, cobranças, taxas, recebimentos
          e recursos comerciais. Produto real, pensado para rotina de negócio.
        </p>
      </header>

      <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 md:gap-4">
        {gestaoCards.map((card) => (
          <article
            key={card.title}
            className="ag-card rounded-[22px] px-4 py-4 sm:px-5 sm:py-5 border border-sky-500/20 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]"
          >
            <div className="inline-flex items-center rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-[10px] uppercase tracking-[0.12em] text-sky-200">
              {card.badge}
            </div>
            <h2 className="mt-3 text-lg font-semibold text-[#f4f8ff]">
              {card.title}
            </h2>
            <p className="mt-2 text-sm text-[#bfd0ec] leading-relaxed">
              {card.subtitle}
            </p>
          </article>
        ))}
      </section>

      <section className="ag-hero px-4 py-5 sm:px-5 sm:py-6 rounded-[28px] border border-sky-500/30 bg-[radial-gradient(circle_at_top_right,rgba(134,192,255,0.16),transparent_20%),linear-gradient(180deg,rgba(10,20,40,0.98),rgba(7,15,30,0.98))]">
        <div className="text-[10px] uppercase tracking-[0.16em] text-[#86c0ff]">
          Visão executiva
        </div>
        <h2 className="mt-2 text-xl font-semibold text-[#f4f8ff]">
          Gestão comercial da carteira
        </h2>
        <p className="mt-2 text-sm text-[#bfd0ec] max-w-3xl">
          Aqui vamos concentrar os produtos de operação comercial da Aurea:
          cobrança, links, QR, simuladores, condições e leitura financeira do
          negócio. Esta aba deixa de ser “IA solta” e passa a ser gestão real.
        </p>
      </section>
    </section>
  );
}

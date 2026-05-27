import React, { useState } from "react";

type CtaVariant = "solid" | "outline";

type Plan = {
  id: string;
  name: string;
  tag?: string;
  highlight: string;
  price: string;
  priceNote: string;
  badge?: string;
  isMostPopular?: boolean;
  description: string;
  features: string[];
  cta: string;
  ctaVariant: CtaVariant;
};

const plans: Plan[] = [
  {
    id: "free",
    name: "Free",
    tag: "Comece agora",
    highlight: "Para começar com segurança.",
    price: "R$ 0,00",
    priceNote: "para sempre",
    badge: "Plano atual",
    description:
      "Carteira digital básica para conhecer a Aurea Gold, acompanhar saldo demonstrativo e testar a experiência inicial.",
    features: [
      "Carteira digital Aurea Gold",
      "PIX preparado em ambiente seguro",
      "Extrato simples de movimentações",
      "Saldo demonstrativo sem dinheiro real",
      "Acesso inicial à IA financeira",
      "Avisos educativos de limite, impostos e organização financeira",
    ],
    cta: "Plano atual",
    ctaVariant: "outline",
  },
  {
    id: "pro",
    name: "Pro",
    tag: "Autônomos e MEI",
    highlight: "Para quem vive de PIX no dia a dia.",
    price: "R$ 29,90",
    priceNote: "/ mês",
    badge: "MEI",
    description:
      "Ideal para autônomos, prestadores de serviço e pequenos negócios que precisam organizar recebimentos e enxergar o caixa.",
    features: [
      "Limites operacionais aprimorados",
      "Extrato organizado por dia e tipo",
      "Relatório mensal básico em PDF",
      "Exportação CSV para planilha",
      "Resumo de entradas e saídas do mês",
      "IA financeira com insights simples",
      "Alertas de faturamento para MEI",
    ],
    cta: "Quero o Pro",
    ctaVariant: "outline",
  },
  {
    id: "gold",
    name: "Gold",
    tag: "Mais escolhido",
    highlight: "Para comércio físico e online.",
    price: "R$ 49,90",
    priceNote: "/ mês",
    badge: "Recomendado",
    isMostPopular: true,
    description:
      "Feito para lojas, mercados, salões, clínicas, delivery e negócios que precisam de leitura clara do caixa.",
    features: [
      "Dashboard mensal de entradas e saídas",
      "Relatórios em PDF e CSV para contabilidade",
      "Classificação inteligente de receitas e despesas",
      "Resumo semanal automático por IA",
      "Links e QR Codes de cobrança com descrição",
      "Recibos premium personalizados",
      "Relatório tributário mensal por categoria",
      "Estimativa básica de impostos",
    ],
    cta: "Quero o Aurea Gold",
    ctaVariant: "solid",
  },
  {
    id: "enterprise",
    name: "Empresarial",
    tag: "Escala",
    highlight: "Para operação com mais volume.",
    price: "R$ 99,90",
    priceNote: "/ mês",
    badge: "Avançado",
    description:
      "Para empresas com múltiplos caixas, maior volume de vendas, relatórios gerenciais e futuras integrações.",
    features: [
      "IA Financeira 3.0 com análises avançadas",
      "Relatórios gerenciais e contábeis",
      "Exportações para escritório de contabilidade",
      "Cobranças recorrentes planejadas",
      "Suporte prioritário",
      "Integração via API sob consulta",
      "Visão consolidada para equipes e parceiros",
    ],
    cta: "Falar com a Aurea",
    ctaVariant: "outline",
  },
];

function PlanCard({
  plan,
  selectedPlan,
  onSelect,
}: {
  plan: Plan;
  selectedPlan: string | null;
  onSelect: (name: string) => void;
}) {
  const isCurrent = plan.id === "free";
  const isSolid = plan.ctaVariant === "solid";
  const wasSelected = selectedPlan === plan.name;

  return (
    <article
      className={[
        "relative flex min-h-[420px] flex-col overflow-hidden rounded-[28px] border px-5 py-5 shadow-[0_18px_44px_rgba(0,0,0,0.28)]",
        plan.isMostPopular
          ? "border-[#D4AF37]/70 bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.22),transparent_28%),linear-gradient(180deg,#102D40_0%,#06131D_100%)]"
          : "border-[#D4AF37]/18 bg-[linear-gradient(180deg,#0E2838_0%,#06131D_100%)]",
      ].join(" ")}
    >
      {plan.badge && (
        <div className="mb-3 inline-flex w-fit rounded-full border border-[#D4AF37]/35 bg-[#D4AF37]/12 px-3 py-1 text-[9px] font-black uppercase tracking-[0.18em] text-[#F5C842]">
          {plan.badge}
        </div>
      )}

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[9px] font-black uppercase tracking-[0.22em] text-[#D4AF37]">
            Plano {plan.name}
          </p>
          <h2 className="mt-1 text-[1.18rem] font-black leading-tight tracking-[-0.03em] text-[#F8FAFC]">
            {plan.highlight}
          </h2>
        </div>

        {plan.tag && (
          <span className="shrink-0 rounded-full border border-white/10 bg-white/6 px-2 py-1 text-[8.5px] font-bold uppercase tracking-[0.12em] text-[#C8D0D8]">
            {plan.tag}
          </span>
        )}
      </div>

      <div className="mt-4 flex items-end gap-1">
        <span className="text-[1.78rem] font-black leading-none tracking-[-0.05em] text-[#F5C842]">
          {plan.price}
        </span>
        <span className="pb-1 text-[11px] font-semibold text-[#AFA58F]">
          {plan.priceNote}
        </span>
      </div>

      <p className="mt-3 text-[11.5px] leading-snug text-[#D7D0BE]">
        {plan.description}
      </p>

      <div className="my-4 h-px w-full bg-[linear-gradient(90deg,transparent,rgba(212,175,55,0.38),transparent)]" />

      <ul className="flex flex-1 flex-col gap-2.5">
        {plan.features.map((feature) => (
          <li key={feature} className="flex items-start gap-2 text-[11px] leading-snug text-[#E5E7EB]">
            <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-emerald-300/50 bg-emerald-400/10 text-[10px] font-black text-emerald-200">
              ✓
            </span>
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      <button
        type="button"
        disabled={isCurrent}
        onClick={() => onSelect(plan.name)}
        className={[
          "mt-5 w-full rounded-[18px] px-4 py-3 text-[10.5px] font-black uppercase tracking-[0.18em] transition",
          isCurrent
            ? "cursor-not-allowed border border-white/10 bg-white/8 text-[#AFA58F]"
            : isSolid
              ? "bg-[linear-gradient(180deg,#F5C842_0%,#C99A06_100%)] text-[#0A1F2E] shadow-[0_12px_24px_rgba(212,175,55,0.24)] active:scale-[0.99]"
              : "border border-[#D4AF37]/45 bg-[#D4AF37]/8 text-[#F5C842] active:scale-[0.99]",
        ].join(" ")}
      >
        {isCurrent ? "Plano atual" : wasSelected ? "Interesse registrado" : plan.cta}
      </button>

      {!isCurrent && (
        <p className="mt-2 text-center text-[9.5px] leading-snug text-[#8FA3B4]">
          Não altera plano automaticamente. Fluxo comercial/checkout será ativado em etapa segura.
        </p>
      )}
    </article>
  );
}

export default function PlanosPremium() {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  return (
    <section className="min-h-screen w-full overflow-x-hidden bg-[radial-gradient(circle_at_top,rgba(212,175,55,0.12),transparent_28%),linear-gradient(180deg,#06131D_0%,#02070B_100%)] px-4 py-4 text-white">
      <div className="mx-auto flex w-full max-w-[390px] flex-col gap-4 rounded-[34px] border border-[#D4AF37]/16 bg-[rgba(2,7,11,0.42)] p-2 shadow-[0_18px_52px_rgba(0,0,0,0.32)] md:max-w-6xl md:p-4">
        <header className="rounded-[28px] border border-[#D4AF37]/22 bg-[linear-gradient(180deg,rgba(14,40,56,0.98),rgba(6,19,29,0.98))] px-5 py-5 shadow-[0_18px_46px_rgba(0,0,0,0.34)]">
          <p className="text-[9px] font-black uppercase tracking-[0.24em] text-[#D4AF37]">
            Aurea Gold • Planos
          </p>

          <h1 className="mt-2 max-w-[360px] text-[1.72rem] font-black leading-[0.98] tracking-[-0.055em] text-[#F8FAFC] md:max-w-3xl md:text-4xl">
            Planos para crescer com controle financeiro.
          </h1>

          <p className="mt-3 max-w-[620px] text-[12px] leading-snug text-[#C8D0D8] md:text-sm">
            O PIX do usuário final continua protegido. Os planos liberam camadas de gestão, IA, relatórios e recursos comerciais da Aurea Gold.
          </p>

          <div className="mt-4 grid gap-2 md:grid-cols-3">
            <div className="rounded-[18px] border border-emerald-300/20 bg-emerald-400/10 px-4 py-2.5">
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-emerald-200">
                Plano atual
              </p>
              <p className="mt-1 text-[12px] font-bold text-[#F8FAFC]">
                Free ativo
              </p>
            </div>

            <div className="rounded-[18px] border border-[#D4AF37]/18 bg-[#D4AF37]/8 px-4 py-2.5">
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-[#F5C842]">
                Upgrade
              </p>
              <p className="mt-1 text-[12px] font-bold text-[#F8FAFC]">
                Interesse comercial
              </p>
            </div>

            <div className="rounded-[18px] border border-white/10 bg-white/6 px-4 py-2.5">
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-[#C8D0D8]">
                Segurança
              </p>
              <p className="mt-1 text-[12px] font-bold text-[#F8FAFC]">
                Sem cobrança automática
              </p>
            </div>
          </div>
        </header>

        <div className="rounded-[24px] border border-emerald-300/18 bg-[linear-gradient(180deg,rgba(6,78,59,0.22),rgba(6,19,29,0.78))] px-5 py-3 text-[11px] leading-snug text-emerald-100">
          <span className="font-black text-emerald-200">Transparência:</span>{" "}
          nenhuma cobrança real é feita nesta tela. Assinaturas, checkout e troca de plano entram apenas com fluxo financeiro seguro e parceiro homologado.
        </div>

        {selectedPlan && (
          <div className="rounded-[22px] border border-[#D4AF37]/28 bg-[#D4AF37]/10 px-5 py-3 text-[11px] leading-snug text-[#F5C842]">
            Interesse no plano <span className="font-black">{selectedPlan}</span> registrado nesta sessão. Próximo passo futuro: fluxo comercial com checkout seguro, sem mudança automática agora.
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {plans.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              selectedPlan={selectedPlan}
              onSelect={setSelectedPlan}
            />
          ))}
        </div>

        <footer className="rounded-[22px] border border-white/8 bg-white/5 px-5 py-3 text-[10px] leading-snug text-[#8FA3B4]">
          <p>
            Valores e recursos exibidos servem para apresentação comercial da Aurea Gold em ambiente seguro. A operação financeira real depende de parceiro PSP/BaaS homologado, compliance, KYC/KYB, webhook seguro, conciliação e revisão jurídica.
          </p>
          <p className="mt-2">
            Informações tributárias são apoio gerencial e não substituem contador, consultor fiscal ou profissional habilitado.
          </p>
        </footer>
      </div>
    </section>
  );
}

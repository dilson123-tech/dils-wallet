import React from "react";

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
    highlight: "Para quem está começando com a Aurea Gold.",
    price: "R$ 0,00",
    priceNote: "para sempre",
    badge: "Incluso para todos",
    isMostPopular: false,
    description:
      "Carteira digital básica, ideal para testes, uso pessoal e primeiros recebimentos via PIX.",
    features: [
      "Carteira digital Aurea Gold",
      "PIX com taxa embutida padrão",
      "Extrato simples de movimentações",
      "Saldo em tempo quase real",
      "Acesso limitado à IA financeira",
      "Alerta educativo sobre limite de faturamento para MEI e atenção ao imposto de renda (modo básico).",
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
    badge: "Ideal para MEI",
    isMostPopular: false,
    description:
      "Perfeito para autônomos, prestadores de serviço, micro negócios e MEIs que recebem por PIX o tempo todo.",
    features: [
      "Limites diários aprimorados para recebimentos",
      "Extrato organizado por dia e tipo de operação",
      "Relatório mensal básico em PDF",
      "Exportação de extrato em CSV para planilha",
      "Resumo automático de entradas e saídas do mês",
      "IA financeira com insights simples sobre o fluxo",
      "Resumo mensal preparado para apoiar sua declaração de imposto (MEI/autônomo).",
      "Alertas quando seu faturamento se aproxima dos limites do MEI.",
    ],
    cta: "Quero o Pro",
    ctaVariant: "outline",
  },
  {
    id: "gold",
    name: "Gold",
    tag: "Mais popular",
    highlight: "O plano certo para comércio físico e online.",
    price: "R$ 49,90",
    priceNote: "/ mês",
    badge: "Mais escolhido",
    isMostPopular: true,
    description:
      "Feito para mercados, lojas, salões, clínicas, delivery e negócios que precisam enxergar o caixa com clareza.",
    features: [
      "Dash de entradas e saídas com visão mensal",
      "Relatórios em PDF e CSV prontos para contabilidade",
      "Classificação inteligente de receitas e despesas",
      "Resumo semanal automático enviado por IA",
      "Taxa embutida mais competitiva nas operações",
      "Links e QR Codes de cobrança com descrição",
      "Recibos premium personalizados com nome da loja",
      "Relatório tributário mensal com visão por categoria de receita.",
      "Exportação em PDF/CSV pronta para enviar ao contador.",
      "Estimativa básica de imposto devido com base nas entradas classificadas.",
    ],
    cta: "Quero o Aurea Gold",
    ctaVariant: "solid",
  },
  {
    id: "enterprise",
    name: "Empresarial",
    tag: "Empresas em escala",
    highlight: "Para quem precisa de visão completa do negócio.",
    price: "R$ 99,90",
    priceNote: "/ mês",
    badge: "Operações em volume",
    isMostPopular: false,
    description:
      "Indicado para operações com maior volume de vendas, múltiplos caixas, filiais ou integração com outros sistemas.",
    features: [
      "IA Financeira 3.0 com análises avançadas",
      "Relatórios gerenciais e contábeis detalhados",
      "Exportações especiais para escritório de contabilidade",
      "Links de cobrança recorrente (mensalidade, planos, etc.)",
      "Suporte prioritário para o negócio",
      "Possibilidade de integrações via API (sob consulta)",
      "Taxa embutida ainda mais otimizada",
      "Visão consolidada para times contábeis e escritórios parceiros.",
      "Preparação de lotes de dados para geração de guias e obrigações fiscais (sob consulta).",
    ],
    cta: "Falar com o time Aurea",
    ctaVariant: "outline",
  },
];

interface PlanCardProps extends Plan {}

function PlanCard({
  name,
  tag,
  highlight,
  price,
  priceNote,
  badge,
  isMostPopular,
  description,
  features,
  cta,
  ctaVariant,
}: PlanCardProps) {
  const isSolid = ctaVariant === "solid";
  const isCurrent = name === "Free";
  const buttonLabel = isCurrent ? "Plano atual" : cta;

  return (
    <div
      className={[
        "relative flex flex-col rounded-2xl border bg-gradient-to-b p-4 md:p-5",
        isMostPopular
          ? "border-amber-400/80 from-zinc-900/80 to-black shadow-[0_0_40px_rgba(251,191,36,0.25)]"
          : "border-zinc-800 from-zinc-900 to-black/90",
      ].join(" ")}
    >
      {/* Badge superior */}
      {badge && (
        <div className="absolute -top-3 left-4 rounded-full border border-amber-400/60 bg-black/90 px-3 py-[2px] text-[9px] font-semibold uppercase tracking-[0.18em] text-amber-300">
          {badge}
        </div>
      )}

      {/* Cabeçalho do plano */}
      <div className="mb-3 mt-1 flex flex-col gap-1">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="text-[11px] uppercase tracking-[0.2em] text-amber-400">
              Plano {name}
            </div>
            {tag && (
              <span className="rounded-full border border-zinc-700 bg-zinc-900/80 px-2 py-[1px] text-[9px] uppercase tracking-[0.16em] text-zinc-300">
                {tag}
              </span>
            )}
          </div>
          {isMostPopular && (
            <span className="rounded-full bg-amber-400/90 px-2 py-[1px] text-[9px] font-semibold uppercase tracking-[0.16em] text-black">
              Mais popular
            </span>
          )}
        </div>
        <div className="text-sm font-semibold text-zinc-50">{highlight}</div>
      </div>

      {/* Preço */}
      <div className="mb-3 flex items-baseline gap-1">
        <span className="text-2xl font-semibold text-amber-300">{price}</span>
        <span className="text-xs text-zinc-400">{priceNote}</span>
      </div>

      {/* Descrição */}
      <p className="mb-3 text-[11px] leading-relaxed text-zinc-400">
        {description}
      </p>

      {/* Divider */}
      <div className="mb-3 h-px w-full bg-gradient-to-r from-transparent via-amber-400/40 to-transparent" />

      {/* Lista de benefícios */}
      <ul className="mb-4 flex flex-1 flex-col gap-2">
        {features.map((feature) => (
          <li
            key={feature}
            className="flex items-start gap-2 text-[11px] text-zinc-300"
          >
            <span className="mt-[2px] inline-flex h-3 w-3 items-center justify-center rounded-full border border-emerald-400/80 text-[9px] text-emerald-300">
              ✓
            </span>
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      {/* Botão */}
      <button
        type="button"
        disabled={isCurrent} // depois ligamos isso com o plano real do usuário
        className={[
          "mt-auto w-full rounded-full px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em]",
          isSolid
            ? "bg-amber-400 text-black hover:bg-amber-300 disabled:bg-zinc-700 disabled:text-zinc-400"
            : "border border-amber-400/70 text-amber-200 hover:bg-amber-400/10 disabled:border-zinc-700 disabled:text-zinc-500",
        ].join(" ")}
      >
        {buttonLabel}
      </button>

      {/* Observações específicas por plano */}
      {name === "Gold" && (
        <p className="mt-2 text-[10px] text-zinc-500">
          Recomendado para negócios que já recebem PIX diariamente e querem
          controle real do caixa, com apoio da IA.
        </p>
      )}
      {name === "Empresarial" && (
        <p className="mt-2 text-[10px] text-zinc-500">
          Indicado para quem precisa de relatórios avançados, múltiplos
          usuários e conversa direta com o time Aurea.
        </p>
      )}
    </div>
  );
}

export default function PlanosPremium() {
  return (
    <div className="w-full px-4 py-6">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
        {/* Cabeçalho da tela */}
        <header className="flex flex-col gap-2">
          <div className="text-[11px] uppercase tracking-[0.25em] text-amber-400">
            Aurea Gold • Planos & Assinaturas
          </div>
          <h1 className="text-lg font-semibold text-zinc-50">
            Escolha o plano que acompanha o crescimento do seu negócio.
          </h1>
          <p className="max-w-3xl text-[11px] leading-relaxed text-zinc-400">
            O PIX continua gratuito para o usuário final. Os planos pagos
            destravam IA financeira, relatórios, automações e recursos
            profissionais para você enxergar e cuidar melhor do caixa.
          </p>
          <div className="mt-1 inline-flex items-center gap-2 rounded-full border border-emerald-500/60 bg-emerald-900/20 px-3 py-1 text-[10px] text-emerald-100">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>
              Plano atual (LAB): <span className="font-semibold">Free</span> • upgrade simulado
            </span>
          </div>
        </header>

        {/* Aviso de transparência */}
        <div className="rounded-xl border border-emerald-400/40 bg-emerald-900/10 px-3 py-2 text-[11px] text-emerald-200">
          <span className="mr-1">✅</span>
          Nenhuma taxa é cobrada diretamente na tela de PIX do cliente final.
          As assinaturas servem para liberar painéis, IA e ferramentas de
          gestão financeira.
        </div>

        {/* Grid de planos */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {plans.map((plan) => (
            <PlanCard key={plan.id} {...plan} />
          ))}
        </div>

        {/* Rodapé explicativo + aviso legal */}
        <footer className="mt-2 text-[10px] text-zinc-500 space-y-1">
          <p>
            Valores ilustrativos em ambiente de laboratório. Vida: assim que
            definirmos parceiros oficiais (PSP, gateway, bancos), ajustamos
            essa tabela para refletir custos reais, taxas embutidas e margens
            da Aurea Gold.
          </p>
          <p className="text-[9px] text-zinc-500">
            As estimativas e informações tributárias apresentadas nesta tela
            têm caráter informativo e dependem dos dados movimentados na
            própria Aurea Gold. Elas não substituem a orientação de um
            contador ou consultor fiscal. Para obrigações oficiais, guias ou
            declarações, consulte um profissional habilitado.
          </p>
        </footer>
      </div>
    </div>
  );
}

import { useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  QrCode,
  Link2,
  CreditCard,
  ArrowDownCircle,
  BarChart3,
  CalendarDays,
  Package,
  CircleHelp,
  Percent,
} from "lucide-react";

type GestaoPage =
  | "pix_qr"
  | "link"
  | "tappay"
  | "receber"
  | "relatorios"
  | "agenda"
  | "produtos"
  | "ajuda"
  | "taxas";

type ToolCard = {
  key: GestaoPage;
  icon: LucideIcon;
  title: string;
  subtitle: string;
  description: string;
  detail: string;
  actionLabel: string;
};

const toolCards: ToolCard[] = [
  {
    key: "pix_qr",
    icon: QrCode,
    title: "Pix e QR",
    subtitle: "Gerar cobrança",
    description: "Crie cobranças Pix, QR Code e BR Code em ambiente seguro.",
    detail:
      "Fluxo preparado para cobrança real quando houver PSP/BaaS homologado. Enquanto isso, permanece em modo seguro, sem liquidação financeira real.",
    actionLabel: "Preparar cobrança",
  },
  {
    key: "link",
    icon: Link2,
    title: "Link",
    subtitle: "Receber por link",
    description: "Gere links de pagamento para vender com mais agilidade.",
    detail:
      "Área pensada para link de cobrança com rastreio, status e conciliação futura via parceiro financeiro homologado.",
    actionLabel: "Criar link demo",
  },
  {
    key: "tappay",
    icon: CreditCard,
    title: "TapPay",
    subtitle: "Com parceiro",
    description: "Venda com cartão pelo celular usando parceiro homologado.",
    detail:
      "O app não vira maquininha sozinho. Tap to Pay depende de parceiro financeiro, contrato, homologação, KYC/KYB e regras operacionais aprovadas.",
    actionLabel: "Ver requisitos TapPay",
  },
  {
    key: "receber",
    icon: ArrowDownCircle,
    title: "Receber",
    subtitle: "Entradas",
    description: "Acompanhe entradas, recebimentos e cobranças do negócio.",
    detail:
      "Central para leitura de valores a receber, recebidos e pendentes, mantendo separação clara entre demo, sandbox e operação real.",
    actionLabel: "Ver entradas",
  },
  {
    key: "relatorios",
    icon: BarChart3,
    title: "Relatórios",
    subtitle: "Resumo",
    description: "Resumo comercial e financeiro para tomada de decisão.",
    detail:
      "Aqui entram relatórios de vendas, cobranças, taxas, recebíveis e evolução operacional do negócio.",
    actionLabel: "Abrir relatório",
  },
  {
    key: "agenda",
    icon: CalendarDays,
    title: "Agenda",
    subtitle: "Clientes",
    description: "Organize clientes, cobranças e próximos contatos.",
    detail:
      "Agenda comercial para lembrar cobranças, compromissos, recorrências e ações de relacionamento.",
    actionLabel: "Abrir agenda",
  },
  {
    key: "produtos",
    icon: Package,
    title: "Produtos",
    subtitle: "Vendas",
    description: "Cadastre produtos, serviços e itens comerciais.",
    detail:
      "Base para catálogo, venda assistida, link de pagamento, controle de produtos e fluxo comercial integrado.",
    actionLabel: "Gerenciar produtos",
  },
  {
    key: "ajuda",
    icon: CircleHelp,
    title: "Ajuda",
    subtitle: "Suporte",
    description: "Suporte operacional da Gestão Aurea.",
    detail:
      "Central para orientar uso, limites, regras de segurança, parceiro financeiro e operação comercial.",
    actionLabel: "Abrir suporte",
  },
  {
    key: "taxas",
    icon: Percent,
    title: "Taxas",
    subtitle: "Simular",
    description: "Simule taxas, custos e cenários de recebimento.",
    detail:
      "Simulador preparado para comparar taxas, prazos, antecipação e impacto financeiro antes da operação real.",
    actionLabel: "Simular taxas",
  },
];

function ToolTile({
  icon: Icon,
  title,
  subtitle,
  onClick,
}: Pick<ToolCard, "icon" | "title" | "subtitle"> & { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="border border-[#0F172A]/16 bg-[linear-gradient(180deg,#E6C84F_0%,#C99A06_100%)] text-center shadow-[0_8px_18px_rgba(15,23,42,0.14)] transition active:scale-[0.97]"
      style={{
        height: 72,
        width: "85%",
        justifySelf: "center",
        borderRadius: 15,
        padding: "8px 6px",
        boxSizing: "border-box",
      }}
    >
      <div
        className="mx-auto flex items-center justify-center rounded-[14px] bg-white/18"
        style={{ width: 34, height: 34 }}
      >
        <Icon size={20} strokeWidth={2.4} className="text-[#0A1F2E]" />
      </div>

      <div
        className="leading-tight text-[#0A1F2E]"
        style={{
          marginTop: 5,
          fontSize: 11.8,
          lineHeight: 1,
          fontFamily: '"Arial Black", Arial, sans-serif',
          fontWeight: 900,
          letterSpacing: "-0.01em",
        }}
      >
        {title}
      </div>

      <p
        className="leading-snug text-[#174F68]"
        style={{
          marginTop: 3,
          fontSize: 10.2,
          fontWeight: 800,
          lineHeight: 1.05,
        }}
      >
        {subtitle}
      </p>
    </button>
  );
}

function BannerCard() {
  return (
    <div className="rounded-[24px] border border-white/12 bg-[linear-gradient(180deg,rgba(13,43,63,0.98),rgba(8,26,40,0.98))] px-4 pt-4 pb-5 shadow-[0_12px_24px_rgba(0,0,0,0.16)]">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-[14px] bg-white/8 text-[#F5C842]">
          <CreditCard size={24} strokeWidth={2.3} />
        </div>

        <div>
          <h3
            className="text-[#F8FAFC]"
            style={{
              fontSize: 20,
              lineHeight: 1.1,
              fontFamily: '"Arial Black", Arial, sans-serif',
              fontWeight: 900,
            }}
          >
            Venda com cartão pelo celular
          </h3>

          <p className="mt-2 text-[14px] leading-relaxed text-[#CBD5E1]">
            Função preparada para Tap to Pay via parceiro homologado. Dinheiro real permanece bloqueado até homologação.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AureaGestaoPanel() {
  const [activePage, setActivePage] = useState<ToolCard | null>(null);

  // GESTAO_EARLY_INTERNAL_PAGE_OK
  if (activePage) {
    const Icon = activePage.icon;

    return (
      <div className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto px-4 pt-8 pb-8">
        <section className="rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.14),transparent_28%),linear-gradient(180deg,rgba(7,59,88,0.98),rgba(6,30,47,0.98))] px-5 pt-5 pb-6 text-white shadow-[0_14px_32px_rgba(0,0,0,0.18)]">
          <button
            type="button"
            onClick={() => setActivePage(null)}
            className="inline-flex items-center rounded-full border border-emerald-300/30 bg-emerald-400/14 px-3 py-1 text-[11px] font-black text-emerald-200 shadow-[0_8px_18px_rgba(16,185,129,0.12)]"
          >
            ← Voltar para Gestão
          </button>

          <p className="mt-5 text-[10px] uppercase tracking-[0.18em] text-[#D4AF37]">
            Gestão Aurea
          </p>

          <div className="mt-3 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-[16px] bg-[linear-gradient(180deg,#E6C84F_0%,#C99A06_100%)] text-[#0A1F2E] shadow-[0_8px_18px_rgba(15,23,42,0.14)]">
              <Icon size={24} strokeWidth={2.4} />
            </div>

            <h1
              className="text-[#F5C842]"
              style={{
                fontSize: 26,
                lineHeight: 1,
                fontFamily: '"Arial Black", Arial, sans-serif',
                fontWeight: 900,
                letterSpacing: "-0.02em",
              }}
            >
              {activePage.title}
            </h1>
          </div>

          <p className="mt-3 text-[14px] leading-relaxed text-[#E6EDF5]">
            {activePage.description}
          </p>
        </section>

        <section className="mt-5 rounded-[28px] bg-[linear-gradient(180deg,#16364B_0%,#0D2436_100%)] px-5 pt-5 pb-6 text-[#f4f8ff] shadow-[0_10px_22px_rgba(0,0,0,0.12)]">
          <p
            className="text-[#F5C842]"
            style={{
              fontSize: 18,
              lineHeight: 1,
              fontFamily: '"Arial Black", Arial, sans-serif',
              fontWeight: 900,
            }}
          >
            {activePage.subtitle}
          </p>

          <p className="mt-3 text-[13px] leading-relaxed text-[#D7D0BE]">
            {activePage.detail}
          </p>

          <div className="mt-5 rounded-[22px] border border-amber-500/16 bg-[rgba(12,30,42,0.74)] px-4 py-4">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
              Status operacional
            </p>
            <p className="mt-2 text-[13px] leading-relaxed text-[#CBD5E1]">
              Módulo preparado para operação real com parceiro homologado. Até lá, mantém comportamento seguro em demonstração/sandbox.
            </p>
          </div>

          <button
            type="button"
            className="mt-5 w-full rounded-[18px] bg-[linear-gradient(180deg,#E6C84F_0%,#C99A06_100%)] px-4 py-3 text-[12px] font-black text-[#0A1F2E] shadow-[0_8px_18px_rgba(15,23,42,0.14)]"
            style={{ fontFamily: '"Arial Black", Arial, sans-serif' }}
          >
            {activePage.actionLabel}
          </button>
        </section>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto px-4 pt-8 pb-8">
      <section className="rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.14),transparent_28%),linear-gradient(180deg,rgba(7,59,88,0.98),rgba(6,30,47,0.98))] px-5 pt-6 pb-7 text-white shadow-[0_14px_32px_rgba(0,0,0,0.18)]">
        <div className="inline-flex items-center rounded-full border border-amber-300/20 bg-amber-400/10 px-3 py-1 text-[11px] font-semibold tracking-[0.02em] text-[#F6D66B]">
          Gestão Aurea
        </div>

        <h1
          className="mt-5 text-[#F5C842]"
          style={{
            fontSize: 26,
            lineHeight: 1.05,
            fontFamily: '"Arial Black", Arial, sans-serif',
            fontWeight: 900,
            letterSpacing: "-0.02em",
          }}
        >
          Ferramentas do seu negócio
        </h1>

        <p className="mt-3 text-[15px] leading-relaxed text-[#E6EDF5]">
          Atalhos para cobrança, recebimentos e gestão comercial em um só lugar.
        </p>
      </section>

      <section className="mt-5 rounded-[28px] bg-[linear-gradient(180deg,#16364B_0%,#0D2436_100%)] px-5 pt-5 pb-6 shadow-[0_10px_22px_rgba(0,0,0,0.12)]">
        <div
          className="text-[#D6DEE8]"
          style={{
            fontSize: 13,
            fontFamily: '"Arial Black", Arial, sans-serif',
            fontWeight: 900,
          }}
        >
          Gestão rápida
        </div>

        <div className="mt-5 grid grid-cols-3" style={{ gap: 8 }}>
          {toolCards.map((item) => (
            <ToolTile
              key={item.key}
              icon={item.icon}
              title={item.title}
              subtitle={item.subtitle}
              onClick={() => setActivePage(item)}
            />
          ))}
        </div>

        <div className="mt-6">
          <BannerCard />
        </div>
      </section>
    </div>
  );
}

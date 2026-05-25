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

type ToolCard = {
  icon: LucideIcon;
  title: string;
  subtitle: string;
};

const toolCards: ToolCard[] = [
  { icon: QrCode, title: "Pix e QR", subtitle: "Gerar cobrança" },
  { icon: Link2, title: "Link", subtitle: "Receber por link" },
  { icon: CreditCard, title: "TapPay", subtitle: "Com parceiro" },
  { icon: ArrowDownCircle, title: "Receber", subtitle: "Entradas" },
  { icon: BarChart3, title: "Relatórios", subtitle: "Resumo" },
  { icon: CalendarDays, title: "Agenda", subtitle: "Clientes" },
  { icon: Package, title: "Produtos", subtitle: "Vendas" },
  { icon: CircleHelp, title: "Ajuda", subtitle: "Suporte" },
  { icon: Percent, title: "Taxas", subtitle: "Simular" },
];

function ToolTile({ icon: Icon, title, subtitle }: ToolCard) {
  return (
    <button
      type="button"
      className="border border-[#0F172A]/16 bg-[linear-gradient(180deg,#E6C84F_0%,#C99A06_100%)] text-center shadow-[0_8px_18px_rgba(15,23,42,0.14)] transition active:scale-[0.97]"
      style={{
        minHeight: 104,
        borderRadius: 18,
        padding: "12px 8px",
      }}
    >
      <div
        className="mx-auto flex items-center justify-center rounded-[14px] bg-white/18"
        style={{ width: 46, height: 46 }}
      >
        <Icon size={26} strokeWidth={2.4} className="text-[#0A1F2E]" />
      </div>

      <div
        className="leading-tight text-[#0A1F2E]"
        style={{
          marginTop: 10,
          fontSize: 14,
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
          marginTop: 5,
          fontSize: 11.5,
          fontWeight: 700,
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

        <div
          className="mt-5 grid grid-cols-3"
          style={{ gap: 14 }}
        >
          {toolCards.map((item) => (
            <ToolTile
              key={item.title}
              icon={item.icon}
              title={item.title}
              subtitle={item.subtitle}
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

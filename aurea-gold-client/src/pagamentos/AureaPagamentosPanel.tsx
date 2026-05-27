import { useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  BellRing,
  CalendarClock,
  CircleHelp,
  CreditCard,
  FileText,
  History,
  QrCode,
  ReceiptText,
  Repeat,
  ShieldCheck,
} from "lucide-react";

type PagAction =
  | "add-bill"
  | "boleto"
  | "subscription"
  | "card"
  | "agenda"
  | "alerts"
  | "receipts"
  | "history"
  | "help";

type PayPageInfo = {
  key: PagAction;
  title: string;
  subtitle: string;
  Icon: LucideIcon;
  description: string;
  detail: string;
  statusLabel: string;
  actionLabel: string;
};

type PayTileProps = {
  title: string;
  subtitle: string;
  Icon: LucideIcon;
  active?: boolean;
  onClick: () => void;
};

const payPages: Record<PagAction, PayPageInfo> = {
  "add-bill": {
    key: "add-bill",
    title: "Conta",
    subtitle: "Cadastrar",
    Icon: FileText,
    description: "Cadastre contas a pagar, vencimentos e lembretes sem executar pagamento real.",
    detail:
      "Base operacional para organizar conta, valor, data de vencimento, status e recorrência. Pagamento real permanece bloqueado até parceiro financeiro homologado.",
    statusLabel: "Organização segura",
    actionLabel: "Salvar conta demo",
  },
  boleto: {
    key: "boleto",
    title: "Boleto",
    subtitle: "Cobrança",
    Icon: QrCode,
    description: "Área preparada para leitura e organização de boleto.",
    detail:
      "Futura leitura de linha digitável/código de barras, vencimento e status. Pagamento real, liquidação real e comprovante real seguem bloqueados.",
    statusLabel: "Boleto em modo seguro",
    actionLabel: "Registrar boleto demo",
  },
  subscription: {
    key: "subscription",
    title: "Assina",
    subtitle: "Recorrente",
    Icon: Repeat,
    description: "Organize assinaturas e compromissos recorrentes.",
    detail:
      "Controle de serviços mensais, impacto no caixa, vencimentos e alertas. Débito automático real não está ativo nesta etapa.",
    statusLabel: "Recorrência preparada",
    actionLabel: "Salvar assinatura demo",
  },
  card: {
    key: "card",
    title: "Cartão",
    subtitle: "Parceiro",
    Icon: CreditCard,
    description: "Pagamentos com cartão dependem de parceiro homologado.",
    detail:
      "O app não processa cartão real sozinho. Qualquer operação com cartão físico, virtual, gateway ou Tap to Pay depende de PSP/BaaS, contrato, KYC/KYB e compliance.",
    statusLabel: "Cartão real bloqueado",
    actionLabel: "Ver requisitos do parceiro",
  },
  agenda: {
    key: "agenda",
    title: "Agenda",
    subtitle: "Vencimentos",
    Icon: CalendarClock,
    description: "Agenda de vencimentos, contas e compromissos.",
    detail:
      "Central para organizar próximos pagamentos, datas importantes, previsões e rotinas financeiras sem movimentação real automática.",
    statusLabel: "Agenda preparada",
    actionLabel: "Criar lembrete demo",
  },
  alerts: {
    key: "alerts",
    title: "Alertas",
    subtitle: "Lembretes",
    Icon: BellRing,
    description: "Alertas para vencimentos e rotinas financeiras.",
    detail:
      "Módulo para lembretes de contas, assinaturas e pagamentos futuros. Notificações reais serão tratadas em etapa própria.",
    statusLabel: "Alertas em preparação",
    actionLabel: "Configurar alerta demo",
  },
  receipts: {
    key: "receipts",
    title: "Recibos",
    subtitle: "Sem fake",
    Icon: ReceiptText,
    description: "Recibos e comprovantes com regra de segurança.",
    detail:
      "Aurea não gera comprovante real falso. Recibos reais só existirão com liquidação confirmada por parceiro financeiro homologado e reconciliação oficial.",
    statusLabel: "Sem comprovante fake",
    actionLabel: "Ver política de recibos",
  },
  history: {
    key: "history",
    title: "Histórico",
    subtitle: "Eventos",
    Icon: History,
    description: "Histórico de pagamentos e eventos operacionais.",
    detail:
      "Área para listar contas, boletos, assinaturas, simulações e eventos. Movimentação real será separada de demo/sandbox.",
    statusLabel: "Histórico estruturado",
    actionLabel: "Abrir histórico demo",
  },
  help: {
    key: "help",
    title: "Ajuda",
    subtitle: "Suporte",
    Icon: CircleHelp,
    description: "Suporte para pagamentos, boletos e segurança.",
    detail:
      "Central de orientação para explicar limites, bloqueios, parceiro financeiro, comprovantes e regras de operação segura.",
    statusLabel: "Suporte preparado",
    actionLabel: "Abrir suporte",
  },
};

const payCards = Object.values(payPages);

function PayTile({
  title,
  subtitle,
  Icon,
  active = false,
  onClick,
}: PayTileProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex flex-col items-center justify-center text-center shadow-[0_8px_18px_rgba(15,23,42,0.14)] transition active:scale-[0.98] ${
        active
          ? "bg-[linear-gradient(180deg,#F8E46D_0%,#D2A900_100%)] ring-2 ring-[#FFF1A6]"
          : "bg-[linear-gradient(180deg,#E9CF43_0%,#CBA500_100%)]"
      } hover:brightness-105`}
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
        className="mb-1 flex items-center justify-center rounded-[14px] bg-white/18"
        style={{ width: 34, height: 34 }}
      >
        <Icon size={20} strokeWidth={2.4} className="text-[#0B2536]" />
      </div>

      <div
        className="text-[#0B2536]"
        style={{
          fontSize: 11.8,
          lineHeight: 1,
          fontFamily: '"Arial Black", Arial, sans-serif',
          fontWeight: 900,
        }}
      >
        {title}
      </div>

      <p
        className="mt-1 leading-tight text-[#123047]/80"
        style={{ fontSize: 10.2, fontWeight: 800, lineHeight: 1.05 }}
      >
        {subtitle}
      </p>
    </button>
  );
}

export default function AureaPagamentosPanel() {
  const [activeAction, setActiveAction] = useState<PagAction | null>(null);
  const activePage = activeAction ? payPages[activeAction] : null;

  // PAGAR_EARLY_INTERNAL_PAGE_OK
  if (activePage) {
    const Icon = activePage.Icon;

    return (
      <section className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto px-4 pt-8 pb-32">
        <section className="rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.14),transparent_28%),linear-gradient(180deg,rgba(7,59,88,0.98),rgba(6,30,47,0.98))] px-5 pt-5 pb-6 text-white shadow-[0_14px_32px_rgba(0,0,0,0.18)]">
          <button
            type="button"
            onClick={() => setActiveAction(null)}
            className="inline-flex items-center rounded-full border border-emerald-300/30 bg-emerald-400/14 px-3 py-1 text-[11px] font-black text-emerald-200 shadow-[0_8px_18px_rgba(16,185,129,0.12)]"
          >
            ← Voltar para Pagar
          </button>

          <p className="mt-5 text-[10px] uppercase tracking-[0.18em] text-[#D4AF37]">
            Pagar Aurea
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
            <p className="mt-2 text-[13px] font-semibold leading-relaxed text-[#CBD5E1]">
              {activePage.statusLabel}
            </p>
          </div>

          <div className="mt-5 rounded-[22px] border border-white/12 bg-[linear-gradient(180deg,rgba(13,43,63,0.98),rgba(8,26,40,0.98))] px-4 py-4">
            <p className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">
              Segurança financeira
            </p>
            <p className="mt-2 text-[12px] leading-relaxed text-[#B8AD95]">
              Pagamento real, boleto real, cartão real, liquidação real e comprovante real permanecem bloqueados até PSP/BaaS homologado, contrato, KYC/KYB, compliance, webhook seguro, ledger e reconciliação oficiais.
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
      </section>
    );
  }

  return (
    <section className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto px-4 pt-8 pb-32">
      <section className="rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.14),transparent_28%),linear-gradient(180deg,rgba(7,59,88,0.98),rgba(6,30,47,0.98))] px-5 pt-6 pb-7 text-white shadow-[0_14px_32px_rgba(0,0,0,0.18)]">
        <div className="inline-flex items-center rounded-full border border-amber-300/20 bg-amber-400/10 px-3 py-1 text-[11px] font-semibold tracking-[0.02em] text-[#F6D66B]">
          Pagamentos em modo seguro
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
          Pagar Aurea
        </h1>

        <p className="mt-3 text-[15px] leading-relaxed text-[#E6EDF5]">
          Organize contas, boletos e assinaturas sem movimentar dinheiro real no modo demonstração.
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
          Pagar rápido
        </div>

        <div className="mt-5 grid grid-cols-3" style={{ gap: 8 }}>
          {payCards.map((item) => (
            <PayTile
              key={item.key}
              title={item.title}
              subtitle={item.subtitle}
              Icon={item.Icon}
              active={activeAction === item.key}
              onClick={() => setActiveAction(item.key)}
            />
          ))}
        </div>

        <div className="mt-6 rounded-[24px] border border-white/12 bg-[linear-gradient(180deg,rgba(13,43,63,0.98),rgba(8,26,40,0.98))] px-4 pt-4 pb-5 shadow-[0_12px_24px_rgba(0,0,0,0.16)]">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-[14px] bg-white/8 text-[#F5C842]">
              <ShieldCheck size={24} strokeWidth={2.3} />
            </div>

            <div className="min-w-0 flex-1">
              <h3
                className="text-[#F8FAFC]"
                style={{
                  fontSize: 20,
                  lineHeight: 1.1,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  fontWeight: 900,
                }}
              >
                Pagamento protegido
              </h3>

              <p className="mt-2 text-[14px] leading-relaxed text-[#CBD5E1]">
                Pagamento real, boleto real, cartão real e liquidação real permanecem bloqueados até parceiro financeiro homologado.
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                  Contas R$ 0,00
                </span>
                <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                  Assinaturas 0
                </span>
                <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                  Boletos 0
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </section>
  );
}

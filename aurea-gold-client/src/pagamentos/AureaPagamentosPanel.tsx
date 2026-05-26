import React, { useState } from "react";
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

type PagAction = "add-bill" | "subscription" | "boleto" | null;

type PayTileProps = {
  title: string;
  subtitle: string;
  Icon: React.ComponentType<{ size?: number; strokeWidth?: number; className?: string }>;
  active?: boolean;
  disabled?: boolean;
  onClick?: () => void;
};

function PayTile({
  title,
  subtitle,
  Icon,
  active = false,
  disabled = false,
  onClick,
}: PayTileProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex min-h-[132px] flex-col items-center justify-center rounded-[22px] px-2.5 py-4 text-center shadow-[0_10px_22px_rgba(0,0,0,0.16)] transition active:scale-[0.98] ${
        active
          ? "bg-[linear-gradient(180deg,#F8E46D_0%,#D2A900_100%)] ring-2 ring-[#FFF1A6]"
          : "bg-[linear-gradient(180deg,#E9CF43_0%,#CBA500_100%)]"
      } ${disabled ? "cursor-not-allowed opacity-70" : "hover:brightness-105"}`}
    >
      <Icon size={30} strokeWidth={2.6} className="mb-4 text-[#0B2536]" />

      <div
        className="text-[#0B2536]"
        style={{
          fontSize: 15,
          lineHeight: 1.05,
          fontFamily: '"Arial Black", Arial, sans-serif',
          fontWeight: 900,
        }}
      >
        {title}
      </div>

      <p className="mt-2 text-[12px] font-semibold leading-tight text-[#123047]/80">
        {subtitle}
      </p>
    </button>
  );
}

export default function AureaPagamentosPanel() {
  const [activeAction, setActiveAction] = useState<PagAction>(null);

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

        <div
          className="mt-5 grid grid-cols-3"
          style={{ gap: 14 }}
        >
          <PayTile
            title="Conta"
            subtitle="Cadastrar"
            Icon={FileText}
            active={activeAction === "add-bill"}
            onClick={() => setActiveAction("add-bill")}
          />
          <PayTile
            title="Boleto"
            subtitle="Cobrança"
            Icon={QrCode}
            active={activeAction === "boleto"}
            onClick={() => setActiveAction("boleto")}
          />
          <PayTile
            title="Assina"
            subtitle="Recorrente"
            Icon={Repeat}
            active={activeAction === "subscription"}
            onClick={() => setActiveAction("subscription")}
          />
          <PayTile
            title="Cartão"
            subtitle="Parceiro"
            Icon={CreditCard}
            disabled
          />
          <PayTile
            title="Agenda"
            subtitle="Vencimentos"
            Icon={CalendarClock}
            active={activeAction === "add-bill"}
            onClick={() => setActiveAction("add-bill")}
          />
          <PayTile
            title="Alertas"
            subtitle="Lembretes"
            Icon={BellRing}
            disabled
          />
          <PayTile
            title="Recibos"
            subtitle="Sem fake"
            Icon={ReceiptText}
            disabled
          />
          <PayTile
            title="Histórico"
            subtitle="Em breve"
            Icon={History}
            disabled
          />
          <PayTile
            title="Ajuda"
            subtitle="Suporte"
            Icon={CircleHelp}
            disabled
          />
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

        <div className="mt-5 rounded-[24px] border border-white/12 bg-white/[0.04] px-4 py-4 text-[14px] leading-relaxed text-[#CBD5E1]">
          {!activeAction && (
            <p>
              Selecione uma ação para abrir a base operacional de pagamentos. Esta área organiza contas, boletos e rotinas recorrentes sem executar transação real.
            </p>
          )}

          {activeAction === "add-bill" && (
            <div className="space-y-2">
              <h3
                className="text-[#F8FAFC]"
                style={{
                  fontSize: 18,
                  lineHeight: 1.1,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  fontWeight: 900,
                }}
              >
                Adicionar conta
              </h3>
              <p>
                Base para cadastrar conta a pagar, valor, vencimento, lembrete e status. Neste ciclo, o foco é organização; pagamento real segue bloqueado.
              </p>
            </div>
          )}

          {activeAction === "subscription" && (
            <div className="space-y-2">
              <h3
                className="text-[#F8FAFC]"
                style={{
                  fontSize: 18,
                  lineHeight: 1.1,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  fontWeight: 900,
                }}
              >
                Assinaturas recorrentes
              </h3>
              <p>
                Espaço para mapear serviços mensais, impacto no caixa e futuros alertas automáticos, sem débito automático real nesta etapa.
              </p>
            </div>
          )}

          {activeAction === "boleto" && (
            <div className="space-y-2">
              <h3
                className="text-[#F8FAFC]"
                style={{
                  fontSize: 18,
                  lineHeight: 1.1,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  fontWeight: 900,
                }}
              >
                Cobrança com boleto
              </h3>
              <p>
                Base visual para futura emissão e acompanhamento de boletos via parceiro homologado. Não gera boleto real, linha digitável real ou cobrança real.
              </p>
            </div>
          )}
        </div>
      </section>
    </section>
  );
}

import React, { useState } from "react";
import QuickPixActions from "./QuickPixActions";

const TABS_LIST = ["PIX", "Cartão", "Empréstimos", "Depósitos", "Relatórios", "IA 3.0"] as const;
type Tab = typeof TABS_LIST[number];

function GhostButton(
  { onClick, children }: { onClick?: () => void; children: React.ReactNode }
) {
  return (
    <button
      onClick={onClick}
      className="h-9 px-3 rounded-xl border border-neutral-700 hover:bg-neutral-800 text-sm"
    >
      {children}
    </button>
  );
}

function Section(
  { title, children }: { title: string; children: React.ReactNode }
) {
  return (
    <section className="space-y-2">
      <div className="text-neutral-200 font-semibold">{title}</div>
      <div className="rounded-xl border border-neutral-800 p-4">{children}</div>
    </section>
  );
}

function clickSel(sel: string) {
  const el = document.querySelector(sel) as HTMLElement | null;
  if (el) el.click();
}

export default function AureaSuperPanel() {
  const [tab, setTab] = useState<Tab>("PIX");

  return (
    <div className="space-y-4">
      {/* Barra de abas */}
      <div className="overflow-x-auto no-scrollbar -mx-1 px-1">
        <div className="flex gap-2 min-w-max">
          {TABS_LIST.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`aurea-tab px-3 h-9 rounded-xl whitespace-nowrap ${tab === t ? "aurea-tab--active" : ""}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Conteúdo por aba */}
      <div className="grid gap-4">
        {tab === "PIX" && (
          <>
            <Section title="Saldo">
              <div className="text-neutral-400">R$ 0,00</div>
            </Section>

            <Section title="Entradas (Mês)">
              <div className="text-neutral-400">R$ 0,00</div>
            </Section>

            <Section title="Saídas (Mês)">
              <div className="text-neutral-400">R$ 0,00</div>
            </Section>

            <Section title="Resumo — últimos 7 dias">
              <div className="text-neutral-500 text-sm">
                (Gráfico aqui — vamos plugar Recharts com <code>/api/v1/ai/summary</code>.)
              </div>
            </Section>

            {/* Ações rápidas + modal controlado pelo QuickPixActions */}
            <div className="rounded-xl border border-neutral-800 p-4">
              <div className="text-neutral-300 mb-2">Ações rápidas</div>
              <div className="grid gap-2">
                <GhostButton onClick={() => clickSel('[data-aurea="pix-open"]')}>Enviar PIX</GhostButton>
                <GhostButton onClick={() => clickSel('[data-aurea="pix-history-open"]')}>Histórico</GhostButton>
                <GhostButton onClick={() => clickSel('[data-aurea="pix-clear"]')}>Limpar</GhostButton>
              </div>
            </div>

            {/* Componente que contém o modal/fluxos de PIX */}
            <QuickPixActions />
          </>
        )}

        {tab === "Cartão" && (
          <Section title="Cartão">
            <p className="text-neutral-400">Limite, fatura, pagamento, cartão virtual.</p>
            <div className="flex gap-2">
              <GhostButton onClick={() => clickSel('[data-aurea="card-generate-virtual"]')}>
                Gerar cartão virtual
              </GhostButton>
              <GhostButton onClick={() => clickSel('[data-aurea="card-pay-bill"]')}>
                Pagar fatura
              </GhostButton>
            </div>
          </Section>
        )}

        {tab === "Empréstimos" && (
          <Section title="Empréstimos">
            <p className="text-neutral-400 mb-3">Simulação e contratação.</p>
            <div className="flex gap-2">
              <GhostButton onClick={() => clickSel('[data-aurea="loan-simulate"]')}>
                Simular
              </GhostButton>
            </div>
          </Section>
        )}

        {tab === "Depósitos" && (
          <Section title="Depósitos">
            <p className="text-neutral-400 mb-3">Boleto/PIX, comprovantes.</p>
            <div className="flex gap-2">
              <GhostButton onClick={() => clickSel('[data-aurea="deposit-generate-slip"]')}>
                Gerar Boleto
              </GhostButton>
            </div>
          </Section>
        )}

        {tab === "Relatórios" && (
          <Section title="Relatórios">
            <p className="text-neutral-400 mb-3">Exportação PDF/CSV, resumo mensal.</p>
            <div className="flex gap-2">
              <GhostButton onClick={() => clickSel('[data-aurea="report-export-pdf"]')}>
                Exportar PDF
              </GhostButton>
            </div>
          </Section>
        )}

        {tab === "IA 3.0" && (
          <Section title="Aurea IA 3.0">
            <p className="text-neutral-400 mb-3">Chat, resumo financeiro e automações.</p>
            <div className="flex gap-2">
              <GhostButton onClick={() => clickSel('[data-aurea="ai-open"]')}>
                Abrir Assistente
              </GhostButton>
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

import React from "react";
import { IaHeadlineLab } from "../super2/IaHeadlineLab";
import ChartSuper2Lab from "./ChartSuper2Lab";
import AureaAIChatLab from "./AureaAIChatLab";
import ConsultorFinanceiroIAPanelLab from "./ConsultorFinanceiroIAPanelLab";

import PlanosPremium from "./PlanosPremium";

export default function Super2Lab() {
  return (
    <div className="aurea-super2 min-h-screen flex items-start justify-center pt-10 pb-20 bg-black text-[#f5f5f5]">
      <IaHeadlineLab />
      <main className="aurea-panel w-[360px] max-w-full rounded-2xl border border-[#d4af37]/40 bg-black/80 backdrop-blur-xl px-4 pb-4 pt-3">
        <header className="mb-2">
          <div className="text-sm font-semibold tracking-wide text-[#d4af37] drop-shadow-[0_0_4px_#d4af37]">
            AUREA GOLD • PREMIUM (LAB)
          </div>
          <div className="text-[10px] opacity-70">
            v1.0 beta • Super2 • Histórico + IA 3.0 (laboratório)
          </div>
        </header>

        {/* Gráfico em modo laboratório */}
        <section className="mt-3 text-[11px]">
          <div className="super2-section-title mb-1">
            Resumo — últimos 7 dias (LAB)
          </div>
          <div className="border border-[#d4af37]/30 rounded-lg px-2 py-2">
            <ChartSuper2Lab />
          </div>
        </section>

        {/* IA 3.0 em modo LAB, isolada */}
        <AureaAIChatLab />

        {/* Consultor Financeiro IA 3.0 (LAB) */}
        <ConsultorFinanceiroIAPanelLab />

        {/* Planos premium da Aurea Gold (somente LAB por enquanto) */}
        <PlanosPremium />
      </main>
    </div>
  );
}
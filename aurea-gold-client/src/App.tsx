import React from "react";
import { AppShell } from "./AppShell";
import SuperAureaHome from "./super2/SuperAureaHome";
// import PanelReceitasReservasLab from "./pagamentos/PanelReceitasReservasLab";

export default function App() {
  return (
    <AppShell>
      <div className="w-full max-w-6xl px-4 py-6 mx-auto">
        {/* HEADER BETA / TÍTULO */}
        <header className="mb-6 md:mb-8">
          <div className="text-[10px] md:text-xs border-b border-zinc-800 pb-4 text-xs uppercase tracking-wide">
            <span className="font-bold leading-tight">
              AUREA GOLD • PAINEL v2 super/ia beta
            </span>
          </div>
          <div className="text-[10px] text-zinc-400 mt-1">
            Ambiente interno IA 3.0 • Modo dev-27
          </div>
          <div className="h-px w-40 md:w-64 bg-amber-500 mt-2" />
        </header>

        {/* MAIN CONTENT */}
        <main className="w-full pb-4 md:pb-6 overflow-x-auto">
          {/* Por enquanto, focamos no painel de IA + PIX + beta */}
          <SuperAureaHome />
          {/* <PanelReceitasReservasLab /> */}
        </main>
      </div>
    </AppShell>
  );
}

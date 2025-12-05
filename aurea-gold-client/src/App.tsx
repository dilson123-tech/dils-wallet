import React, { useState } from "react";
import { AppShell, AppTab } from "./AppShell";
import SuperAureaHome from "./super2/SuperAureaHome";
import AureaPixPanel from "./super2/AureaPixPanel";
import AureaIAPanel from "./super2/AureaIAPanel";
// import PanelReceitasReservasLab from "./pagamentos/PanelReceitasReservasLab";

export default function App() {
  const [activeTab, setActiveTab] = useState<AppTab>("home");

  let content: React.ReactNode;

  switch (activeTab) {
    case "home":
      content = (
        <>
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
            <SuperAureaHome />
            {/* <PanelReceitasReservasLab /> */}
          </main>
        </>
      );
      break;

    case "pix":
      content = (
        <div className="w-full px-4 py-6 mx-auto">
          <AureaPixPanel />
        </div>
      );
      break;

    case "ia":
      content = (
        <div className="w-full px-4 py-6 mx-auto">
          <AureaIAPanel />
        </div>
      );
      break;

    case "pagamentos":
      content = (
        <div className="w-full max-w-6xl px-4 py-6 mx-auto">
          <h1 className="text-sm font-semibold text-amber-300 mb-2 uppercase tracking-wide">
            Pagamentos • Laboratório
          </h1>
          <p className="text-xs text-zinc-400">
            Aqui vamos plugar o painel de Pagamentos e o Receitas & Reservas
            Lab, trazendo contas, boletos, assinaturas e testes avançados.
          </p>
        </div>
      );
      break;

    default:
      content = null;
  }

  return (
    <AppShell activeTab={activeTab} onTabChange={setActiveTab}>
      {content}
    </AppShell>
  );
}

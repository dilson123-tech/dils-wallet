import React, { useState } from "react";
import { AppShell, AppTab } from "./AppShell";
import SuperAureaHome from "./super2/SuperAureaHome";
import AureaPixPanel from "./super2/AureaPixPanel";
import AureaIAPanel from "./super2/AureaIAPanel";
import AureaPagamentosPanel from "./pagamentos/AureaPagamentosPanel";
import AureaCreditoIAPanel from "./credito/AureaCreditoIAPanel";
import PlanosPremium from "./super2-lab/PlanosPremium";
// import PanelReceitasReservasLab from "./pagamentos/PanelReceitasReservasLab";

const isPlanosLab =
  typeof window !== "undefined" &&
  window.location.pathname.includes("planos-lab");

export default function App() {
  if (isPlanosLab) {
    return (
      <div className="min-h-screen bg-black text-zinc-50">
        <main className="w-full px-4 py-6 mx-auto max-w-6xl">
          <PlanosPremium />
        </main>
      </div>
    );
  }

  const [activeTab, setActiveTab] = useState<AppTab>("home");
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [pixInitialAction, setPixInitialAction] = useState<"send" | "charge" | "statement" | null>(null);

  const handleTabChange = (tab: AppTab) => {
    if (tab === activeTab) return;

    setIsTransitioning(true);

    setTimeout(() => {
      setActiveTab(tab);
      setIsTransitioning(false);
    }, 500);
  };

  const handleHomePixShortcut = (action: "enviar" | "receber" | "extrato") => {
    let next: "send" | "charge" | "statement" | null = null;

    if (action === "enviar") {
      next = "send";
    } else if (action === "extrato") {
      next = "statement";
    } else if (action === "receber") {
      next = "charge";
    }

    setPixInitialAction(next);
    handleTabChange("pix");
  };

  let content: React.ReactNode;

  switch (activeTab) {
    case "home":
      content = (
        <>
          {/* HEADER APP OFICIAL */}
          <header className="mb-6 md:mb-8">
            <div className="text-[10px] md:text-xs border-b border-zinc-800 pb-4 uppercase tracking-wide flex flex-col md:flex-row md:items-center md:justify-between gap-1">
              <span className="font-bold leading-tight">
                AUREA GOLD • CARTEIRA DIGITAL
              </span>
              <span className="text-[9px] md:text-[10px] text-amber-300">
                Versão IA 3.0 • Ambiente interno (LAB)
              </span>
            </div>
            <div className="h-px w-40 md:w-64 bg-amber-500 mt-2" />
          </header>

          {/* MAIN CONTENT */}
          <main className="w-full pb-4 md:pb-6 overflow-x-auto">
            <SuperAureaHome onPixShortcut={handleHomePixShortcut} />
            {/* <PanelReceitasReservasLab /> */}
          </main>
        </>
      );
      break;

    case "pix":
      content = (
        <div className="w-full px-4 py-6 mx-auto">
          <AureaPixPanel initialAction={pixInitialAction} />
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
        <div className="w-full px-4 py-6 mx-auto">
          <AureaPagamentosPanel />
        </div>
      );
      break;

    case "credito-ia":
      content = (
        <div className="w-full px-4 py-6 mx-auto">
          <AureaCreditoIAPanel />
        </div>
      );
      break;

    default:
      content = null;
  }

  return (
    <AppShell
      activeTab={activeTab}
      onTabChange={handleTabChange}
      isSplash={isTransitioning}
    >
      {content}
    </AppShell>
  );
}

import React, { PropsWithChildren } from "react";

export type AppTab = "home" | "pix" | "ia" | "pagamentos" | "credito-ia";

interface AppShellProps extends PropsWithChildren {
  activeTab: AppTab;
  onTabChange?: (tab: AppTab) => void;
  isSplash?: boolean;
}

export function AppShell({
  children,
  activeTab,
  onTabChange,
  isSplash = false,
}: AppShellProps) {
  const tabs: { key: AppTab; label: string; icon: string }[] = [
    { key: "home", label: "Conta", icon: "🏦" },
    { key: "ia", label: "Negócio", icon: "🏪" },
    { key: "pix", label: "Pix", icon: "◎" },
    { key: "pagamentos", label: "Pagamentos", icon: "💳" },
    { key: "credito-ia", label: "Crédito IA", icon: "📊" },
  ];

  const headerSubtitle =
    activeTab === "home"
      ? "Visão geral da sua conta"
      : activeTab === "pix"
      ? "Movimentações PIX"
      : activeTab === "ia"
      ? "Inteligência de negócio"
      : activeTab === "pagamentos"
      ? "Pagamentos e cobranças"
      : "Simulação de crédito";

  return (
    <div className="min-h-screen flex flex-col text-white bg-[radial-gradient(circle_at_top,_rgba(212,175,55,0.08),_transparent_22%),linear-gradient(180deg,#090909_0%,#0d0f13_100%)]">
      
      {/* HEADER PREMIUM */}
      <header className="sticky top-0 z-30 px-3 pt-3 pb-2 backdrop-blur-md">
        <div className="ag-hero px-4 py-3.5 flex items-center justify-between rounded-[22px]">

          <div className="flex flex-col">
            <span className="text-[10px] tracking-[0.3em] ag-gold-text uppercase">
              AUREA GOLD
            </span>

            <span className="text-sm font-semibold ag-title">
              {headerSubtitle}
            </span>
          </div>

          <span className="text-[10px] px-2 py-1 rounded-full border ag-muted border-[rgba(212,175,55,0.2)]">
            BETA
          </span>

        </div>
      </header>

      {/* MAIN */}
      <main className="flex-1 w-full px-3 pb-[118px]">
        <div className="w-full max-w-[460px] mx-auto">
          {children}
        </div>
      </main>

      {/* NAV PREMIUM */}
      <footer className="fixed bottom-0 left-0 right-0 z-40 px-3 pb-[max(12px,env(safe-area-inset-bottom))]">
        <div className="ag-surface-elevated mx-auto max-w-[460px] flex justify-between items-center px-2 py-2 min-h-[76px] rounded-[26px]">

          {tabs.map((tab) => {
            const isActive = tab.key === activeTab;

            return (
              <button
                key={tab.key}
                onClick={() => !isSplash && onTabChange?.(tab.key)}
                className={`group relative flex flex-col items-center justify-center gap-1 flex-1 min-h-[58px] rounded-[18px] transition-all duration-200 ${
                  isActive
                    ? "bg-[linear-gradient(135deg,rgba(212,175,55,0.24),rgba(212,175,55,0.10))] shadow-[inset_0_0_0_1px_rgba(212,175,55,0.34),0_10px_24px_rgba(0,0,0,0.34)]"
                    : "hover:bg-white/5"
                }`}
              >
                <span
                  className={`text-[18px] ${
                    isActive ? "ag-gold-text" : "ag-soft"
                  }`}
                >
                  {tab.icon}
                </span>

                <span
                  className={`text-[10px] font-medium tracking-[0.18em] uppercase ${
                    isActive ? "ag-gold-text" : "ag-muted"
                  }`}
                >
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </footer>

      {/* SPLASH */}
      {isSplash && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm z-50">
          <div className="ag-card px-6 py-6 flex flex-col items-center gap-3">
            <div className="h-10 w-10 rounded-full border border-[rgba(212,175,55,0.4)] border-t-transparent animate-spin" />
            <span className="text-xs tracking-[0.3em] ag-gold-text uppercase">
              AUREA GOLD
            </span>
            <span className="text-xs ag-muted">
              Carregando...
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

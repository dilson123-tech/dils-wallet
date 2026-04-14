import React, { PropsWithChildren } from "react";

export type AppTab = "home" | "pix" | "gestao" | "pagamentos" | "mais";

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
    { key: "home", label: "Conta", icon: "⌂" },
    { key: "gestao", label: "Gestão", icon: "▦" },
    { key: "pix", label: "Pix", icon: "◎" },
    { key: "pagamentos", label: "Pagar", icon: "▣" },
    { key: "mais", label: "Mais", icon: "≡" },
  ];

  const headerSubtitle =
    activeTab === "home"
      ? "Sua conta digital"
      : activeTab === "pix"
      ? "Área Pix"
      : activeTab === "gestao"
      ? "Gestão do negócio"
      : activeTab === "pagamentos"
      ? "Pagamentos"
      : "Central Aurea";

  return (
    <div className="min-h-screen flex flex-col text-white bg-[radial-gradient(circle_at_top,_rgba(90,160,255,0.10),_transparent_22%),linear-gradient(180deg,#06101f_0%,#09162a_100%)]">
      
      {activeTab !== "home" && (
        <header className="sticky top-0 z-30 px-4 pt-4 pb-2 sm:px-4 md:px-3 backdrop-blur-md">
          <div className="ag-hero px-4 py-3 flex items-center justify-between rounded-[22px]">
            <div className="flex flex-col">
              <span className="text-[10px] tracking-[0.3em] ag-gold-text uppercase">
                AUREA GOLD
              </span>

              <span className="text-sm font-semibold ag-title">
                {headerSubtitle}
              </span>
            </div>

            <span className="text-[10px] px-2 py-1 rounded-full border ag-muted border-sky-500/20 bg-sky-500/10">
              BETA
            </span>
          </div>
        </header>
      )}

      {/* MAIN */}
      <main className="flex-1 w-full px-4 pt-4 pb-[116px] sm:px-4 md:px-3">
        <div className="w-full max-w-[960px] mx-auto">
          {children}
        </div>
      </main>

      {/* NAV PREMIUM */}
      <footer className="fixed bottom-0 left-0 right-0 z-50 flex justify-center px-4 sm:px-4 md:px-3 pb-[max(14px,env(safe-area-inset-bottom))]">
        <div className="w-full max-w-[960px] flex justify-between items-center gap-0.5 sm:gap-1 rounded-[24px] sm:rounded-[28px] border border-sky-500/14 bg-[rgba(8,18,35,0.94)] px-2 py-2 sm:px-2.5 sm:py-2.5 shadow-[0_20px_48px_rgba(2,8,20,0.45),0_0_24px_rgba(90,160,255,0.08)] backdrop-blur-xl">

          {tabs.map((tab) => {
            const isActive = tab.key === activeTab;

            return (
              <button
                key={tab.key}
                onClick={() => !isSplash && onTabChange?.(tab.key)}
                className={`group relative flex flex-col items-center justify-center gap-0.5 sm:gap-1 flex-1 min-h-[54px] sm:min-h-[60px] rounded-[18px] sm:rounded-[20px] transition-all duration-200 ${
                  isActive ? "bg-[linear-gradient(180deg,rgba(90,160,255,0.24),rgba(90,160,255,0.08))] shadow-[inset_0_0_0_1px_rgba(90,160,255,0.28),0_10px_26px_rgba(2,8,20,0.32)]" : "bg-[linear-gradient(180deg,#e2b611,#c99a06)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.10),0_8px_18px_rgba(0,0,0,0.20)] hover:brightness-105"
                }`}
              >
                <span
                  className={`text-[16px] sm:text-[18px] leading-none ${
                    isActive ? "text-[#f4f8ff]" : "text-[#06101f]"
                  }`}
                >
                  {tab.icon}
                </span>

                <span
                  className={`text-[9px] sm:text-[10px] font-bold tracking-[0.04em] sm:tracking-[0.08em] uppercase ${
                    isActive ? "text-[#f4f8ff]" : "text-[#06101f]"
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
        <div className="fixed inset-0 flex items-center justify-center bg-[rgba(6,16,31,0.82)] backdrop-blur-sm z-50">
          <div className="ag-card px-6 py-6 flex flex-col items-center gap-3">
            <div className="h-10 w-10 rounded-full border border-sky-400/50 border-t-transparent animate-spin" />
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

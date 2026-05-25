import React, { PropsWithChildren } from "react";
import { createPortal } from "react-dom";

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
    <div className="app-shell min-h-screen flex flex-col text-white overflow-x-hidden bg-[radial-gradient(circle_at_top,_rgba(212,175,55,0.06),_transparent_22%),linear-gradient(180deg,#0E2230_0%,#123447_100%)]">
      
      {activeTab !== "home" && (
        <header className="hidden md:block sticky top-0 z-30 px-4 pt-4 pb-2 sm:px-4 md:px-3 backdrop-blur-md">
          <div className="ag-hero px-4 py-3 flex items-center justify-between rounded-[22px]">
            <div className="flex flex-col">
              <span className="text-[10px] tracking-[0.3em] ag-gold-text uppercase">
                AUREA GOLD
              </span>

              <span className="text-sm font-semibold ag-title">
                {headerSubtitle}
              </span>
            </div>

            <span className="text-[10px] px-2 py-1 rounded-full border ag-muted border-amber-500/12 bg-amber-500/10">
              BETA
            </span>
          </div>
        </header>
      )}

      {/* MAIN */}
      <main className="flex-1 w-full px-4 pt-4 pb-[220px] sm:px-4 md:px-3">
        <div data-app-content="true" className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto">
          {children}
        </div>
      </main>

      {/* NAV PREMIUM */}
      {typeof document !== "undefined"
        ? createPortal(
            <footer
              data-app-dock="true"
              className="app-dock flex justify-center px-4 sm:px-4 md:px-3 pb-[max(10px,env(safe-area-inset-bottom))]"
              style={{
                position: "fixed",
                inset: "auto 0 max(10px, env(safe-area-inset-bottom)) 0",
                top: "auto",
                right: 0,
                bottom: "max(10px, env(safe-area-inset-bottom))",
                left: 0,
                width: "100vw",
                maxWidth: "none",
                transform: "none",
                zIndex: 99999,
              }}
            >
              <div className="wallet-dock-inner w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] flex justify-between items-center gap-1.5 rounded-[28px] border border-amber-500/14 bg-[rgba(16,42,55,0.96)] px-2 py-2 shadow-[0_20px_48px_rgba(2,8,20,0.45),0_0_24px_rgba(212,175,55,0.08)] backdrop-blur-xl">

                {tabs.map((tab) => {
                  const isActive = tab.key === activeTab;

                  return (
                    <button
                      key={tab.key}
                      onClick={() => !isSplash && onTabChange?.(tab.key)}
                      className={`group relative flex flex-col items-center justify-center gap-0.5 sm:gap-1 flex-1 min-h-[56px] sm:min-h-[60px] rounded-[18px] sm:rounded-[20px] transition-all duration-200 ${
                        isActive ? "bg-[linear-gradient(180deg,#f1d36b,#d4af37)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.18),0_10px_26px_rgba(2,8,20,0.32)]" : "bg-[linear-gradient(180deg,#e2b611,#c99a06)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.10),0_8px_18px_rgba(0,0,0,0.20)] hover:brightness-105"
                      }`}
                    >
                      <span
                        className={`text-[16px] sm:text-[18px] leading-none ${
                          isActive ? "text-[#0E2230]" : "text-[#0E2230]"
                        }`}
                      >
                        {tab.icon}
                      </span>

                      <span
                        className={`text-[9px] sm:text-[10px] font-bold tracking-[0.04em] sm:tracking-[0.08em] uppercase ${
                          isActive ? "text-[#0E2230]" : "text-[#0E2230]"
                        }`}
                      >
                        {tab.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </footer>,
            document.body
          )
        : null}

      {/* SPLASH */}
      {isSplash && (
        <div className="fixed inset-0 flex items-center justify-center bg-[rgba(6,16,31,0.82)] backdrop-blur-sm z-50">
          <div className="ag-card px-6 py-6 flex flex-col items-center gap-3">
            <div className="h-10 w-10 rounded-full border border-amber-500/24 border-t-transparent animate-spin" />
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

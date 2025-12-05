import React, { PropsWithChildren } from "react";

export type AppTab = "home" | "pix" | "ia" | "pagamentos";

interface AppShellProps extends PropsWithChildren {
  activeTab: AppTab;
  onTabChange?: (tab: AppTab) => void;
}

/**
 * AppShell — estrutura oficial do aplicativo Aurea Gold.
 * Container principal do app:
 *  - header premium
 *  - área de conteúdo
 *  - tab bar inferior (Home / PIX / IA / Pagamentos)
 */
export function AppShell({ children, activeTab, onTabChange }: AppShellProps) {
  const tabs: { key: AppTab; label: string; icon: string }[] = [
    { key: "home", label: "Home",        icon: "🏠" },
    { key: "pix",  label: "PIX",         icon: "⚡" },
    { key: "ia",   label: "IA 3.0",      icon: "🧠" },
    { key: "pagamentos", label: "Pagos", icon: "💳" },
  ];

  return (
    <div
      className="
        min-h-screen w-full
        bg-gradient-to-b from-black via-zinc-900 to-black
        text-zinc-100
        flex flex-col
      "
    >
      {/* HEADER PREMIUM — depois refinamos */}
      <header className="h-12 border-b border-amber-500/40 flex items-center px-4">
        <div className="text-xs uppercase tracking-widest text-amber-300">
          Aurea Gold
        </div>
      </header>

      {/* ÁREA PRINCIPAL */}
      <main className="flex-1 overflow-y-auto p-4">
        {children}
      </main>

      {/* TAB BAR / NAV INFERIOR */}
      <footer className="h-16 border-t border-amber-500/40 bg-black/80 backdrop-blur flex items-center">
        <nav className="flex w-full max-w-3xl mx-auto h-full">
          {tabs.map((tab) => {
            const isActive = tab.key === activeTab;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => onTabChange?.(tab.key)}
                className={`
                  flex-1 flex flex-col items-center justify-center
                  text-[10px] uppercase tracking-wide
                  transition-colors
                  ${isActive ? "text-amber-300" : "text-zinc-500"}
                `}
              >
                <div className="flex flex-col items-center gap-1">
                  {/* Indicador superior */}
                  <div
                    className={`h-0.5 w-6 rounded-full ${
                      isActive ? "bg-amber-400" : "bg-transparent"
                    }`}
                  />
                  <span className="text-base leading-none">{tab.icon}</span>
                  <span className="leading-none">{tab.label}</span>
                </div>
              </button>
            );
          })}
        </nav>
      </footer>
    </div>
  );
}

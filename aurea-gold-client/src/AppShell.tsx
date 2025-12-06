import React, { PropsWithChildren } from "react";

export type AppTab = "home" | "pix" | "ia" | "pagamentos";

interface AppShellProps extends PropsWithChildren {
  activeTab: AppTab;
  onTabChange?: (tab: AppTab) => void;
  isSplash?: boolean;
}

/**
 * AppShell — estrutura oficial do aplicativo Aurea Gold.
 * - Header premium (muda conforme a aba)
 * - Área de conteúdo (children)
 * - Navegação inferior estilo banco: Conta / Negócio / Pix / Pagamentos
 */
export function AppShell({
  children,
  activeTab,
  onTabChange,
  isSplash = false,
}: AppShellProps) {
  const tabs: { key: AppTab; label: string; icon: string }[] = [
    { key: "home",       label: "Conta",       icon: "🏦" },
    { key: "ia",         label: "Negócio",     icon: "🏪" },
    { key: "pix",        label: "Pix",         icon: "◎" },
    { key: "pagamentos", label: "Pagamentos",  icon: "💳" },
  ];

  const headerTitle = "Aurea Gold";

  const headerSubtitle =
    activeTab === "home"
      ? "Visão geral da sua conta Aurea Gold."
      : activeTab === "pix"
      ? "Envios, recebimentos e extratos PIX."
      : activeTab === "ia"
      ? "AureaIA 3.0 para o seu negócio."
      : "Pagamentos & cobranças";

  return (
    <div
      className="
        min-h-screen w-full
        bg-gradient-to-b from-black via-zinc-900 to-black
        text-zinc-100
        flex flex-col
      "
    >
      {/* HEADER PREMIUM */}
      <header className="h-16 border-b border-zinc-800/80 bg-black/80 backdrop-blur flex items-center px-4">
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-[0.25em] text-amber-400">
            Aurea Gold • Beta
          </span>
          <span className="text-sm font-semibold text-zinc-100">
            {headerTitle}
          </span>
          <span className="text-[11px] text-zinc-400">
            {headerSubtitle}
          </span>
        </div>
      </header>

      {/* CONTEÚDO PRINCIPAL */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      {/* NAV INFERIOR ESTILO APP DE BANCO */}
      <footer className="relative border-t border-zinc-800 bg-black/90 backdrop-blur">
        <nav className="max-w-3xl mx-auto flex items-end justify-between px-4 pt-2 pb-3">
          {tabs.map((tab) => {
            const isActive = tab.key === activeTab;
            const isPix = tab.key == "pix";

            if (isPix) {
              // Botão central flutuante do PIX
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => !isSplash && onTabChange?.(tab.key)}
                  className="flex flex-col items-center justify-center -translate-y-4"
                >
                  <div
                    className={`
                      h-12 w-12 rounded-full
                      flex items-center justify-center
                      text-xl
                      shadow-[0_0_24px_rgba(45,212,191,0.9)]
                      border border-emerald-300/70
                      ${isActive ? "bg-emerald-400 text-black" : "bg-emerald-500 text-black"}
                    `}
                  >
                    {tab.icon}
                  </div>
                  <span
                    className={`
                      mt-1 text-[10px] font-medium
                      ${isActive ? "text-emerald-300" : "text-zinc-400"}
                    `}
                  >
                    {tab.label}
                  </span>
                </button>
              );
            }

            // Demais abas (Conta / Negócio / Pagamentos)
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => onTabChange?.(tab.key)}
                className="flex-1 flex flex-col items-center justify-center gap-1"
              >
                <span
                  className={`
                    text-lg leading-none
                    ${isActive ? "text-amber-300" : "text-zinc-400"}
                  `}
                >
                  {tab.icon}
                </span>
                <span
                  className={`
                    text-[10px] uppercase tracking-wide
                    ${isActive ? "text-amber-300" : "text-zinc-500"}
                  `}
                >
                  {tab.label}
                </span>
              </button>
            );
          })}
        </nav>
      </footer>

      {/* SPLASH / LOADING PREMIUM */}
      {isSplash && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3">
            <div className="h-10 w-10 rounded-full border border-amber-400/70 border-t-transparent animate-spin" />
            <div className="text-[11px] uppercase tracking-[0.28em] text-amber-300">
              AUREA GOLD
            </div>
            <div className="text-[10px] text-zinc-400">
              Carregando painel...
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { PropsWithChildren } from "react";

/**
 * AppShell — estrutura oficial do aplicativo Aurea Gold.
 * Esse componente será o container principal do app,
 * onde conectaremos:
 *  - navegação
 *  - status bar premium
 *  - painel principal
 *  - IA 3.0 integrada
 */
export function AppShell({ children }: PropsWithChildren) {
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

      {/* RODAPÉ / NAV / TAB BAR — placeholder */}
      <footer className="h-14 border-t border-amber-500/40 flex items-center justify-center text-[10px] uppercase text-zinc-400">
        nav oficial
      </footer>
    </div>
  );
}

import React from "react";
import SuperAureaHome from "./super2/SuperAureaHome";
import PanelReceitasReservasLab from "./pagamentos/PanelReceitasReservasLab";

export default function App() {
  return (
    <div className="min-h-screen bg-black text-amber-400 flex justify-center">
      {/* Container central para o layout Aurea */}
      <div className="w-full max-w-6xl flex">
        {/* Sidebar brand (mostra só no desktop) */}
        <aside className="hidden md:block w-52 border-r border-zinc-800 p-4 text-xs uppercase tracking-wide">
          <div className="font-bold leading-tight">
            <div>AUREA GOLD •</div>
            <div>PREMIUM</div>
            <div className="text-[10px] text-zinc-400 mt-1">v1.0 beta</div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-4 md:p-6 overflow-x-auto">
          <header className="mb-4 md:mb-6">
            <h1 className="text-xl md:text-2xl font-semibold">
              AUREA GOLD • PREMIUM v1.0 beta
            </h1>
            <div className="h-px w-40 md:w-64 bg-amber-500 mt-2" />
          </header>

          <SuperAureaHome />
        </main>
      </div>
    </div>
  );
}
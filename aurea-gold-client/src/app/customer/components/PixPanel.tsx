import React from "react";
import SummaryKpis from "./SummaryKpis";
import RecentPixList from "./RecentPixList";

export default function PixPanel() {
  return (
    <div style={{ padding: 12 }}>
      {/* KPIs + Gráfico */}
      <SummaryKpis />

      {/* Lista das últimas PIX */}
      <div className="mt-4">
        <div className="text-sm text-gray-500 mb-2">Últimas PIX (10)</div>
        <RecentPixList />
      </div>
    </div>
  );
}

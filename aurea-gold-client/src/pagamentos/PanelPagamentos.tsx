import React from "react";
import PanelReservasIA3Lab from "./PanelReservasIA3Lab";

export default function PanelPagamentos() {
  return (
    <div className="border border-zinc-700 rounded-lg p-3 text-xs text-zinc-200 bg-black/40">
      <h2 className="text-sm font-semibold text-amber-400 mb-2">
        Painel de Pagamentos • LAB (desativado)
      </h2>
      <p className="text-zinc-400 leading-snug">
        Este painel era usado para testes antigos da IA de pagamentos.
        Agora o painel oficial de operações está sendo migrado para o
        novo módulo <span className="text-amber-300 font-semibold">
        Receitas &amp; Reservas
        </span>.
      </p>
      <p className="text-zinc-500 mt-2">
        Quando a nova IA de pagamentos estiver pronta, este espaço volta
        com dados em tempo real.
      </p>
      <div className="mt-4">
      <PanelReservasIA3Lab />
    </div>
  </div>
  );
}

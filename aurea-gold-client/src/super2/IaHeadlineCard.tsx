import React from "react";
import type { AureaIaHeadlinePanel } from "./ia3Types";

interface IaHeadlineCardProps {
  data?: AureaIaHeadlinePanel;
}

export const IaHeadlineCard: React.FC<IaHeadlineCardProps> = ({ data }) => {
  if (!data) return null;

  const badgeClass =
    data.nivel === "ok"
      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/40"
      : data.nivel === "atencao"
      ? "bg-amber-500/15 text-amber-300 border-amber-500/40"
      : "bg-red-500/15 text-red-300 border-red-500/40";

  const tituloNivel =
    data.nivel === "ok"
      ? "Dia tranquilo"
      : data.nivel === "atencao"
      ? "Sinal amarelo"
      : "Alerta crítico";

  return (
    <div className="w-full rounded-2xl border border-amber-500/40 bg-zinc-950/80 p-4 md:p-5 shadow-[0_0_30px_rgba(251,191,36,0.15)] space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1">
          <p className="text-[11px] uppercase tracking-wide text-amber-400/80">
            IA 3.0 • Painel 3
          </p>
          <h2 className="text-sm md:text-base font-semibold text-zinc-50">
            {data.headline}
          </h2>
          <p className="text-[11px] md:text-xs text-zinc-400">
            {data.subheadline}
          </p>
        </div>

        <span className={`px-2 py-1 rounded-full text-[10px] border ${badgeClass}`}>
          {tituloNivel}
        </span>
      </div>

      <p className="text-[11px] md:text-xs text-zinc-300 whitespace-pre-line">
        {data.resumo}
      </p>

      <div className="rounded-xl border border-amber-500/20 bg-zinc-900/70 p-3 space-y-1.5">
        <p className="text-[10px] font-semibold text-amber-300">
          Destaques do seu dia
        </p>
        <ul className="space-y-1">
          {data.destaques.map((item, idx) => (
            <li
              key={idx}
              className="text-[10px] md:text-[11px] text-zinc-300 flex gap-1.5"
            >
              <span className="mt-[3px] h-1 w-1 rounded-full bg-amber-400/80" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent p-3">
        <p className="text-[10px] md:text-[11px] text-zinc-200">
          {data.recomendacao}
        </p>
      </div>
    </div>
  );
};

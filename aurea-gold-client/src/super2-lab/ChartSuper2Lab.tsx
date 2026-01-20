import React, { useEffect, useState } from "react";
import { API_BASE, USER_EMAIL } from "../super2/api";
import { getToken } from "../lib/auth";

import { authHeaders } from "../lib/auth";

type DayPoint = {
  dia: string;
  entradas: number;
  saidas: number;
  net: number;
};

type PixBalancePayload = {
  saldo_atual: number;
  entradas_mes: number;
  saidas_mes: number;
  ultimos_7d?: {
    dia: string;
    entradas: number;
    saidas: number;
  }[];
};

export default function ChartSuper2Lab() {
  const [points, setPoints] = useState<DayPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setErr(null);

        const r = await fetch(`${API_BASE}/api/v1/pix/balance?days=7`, {
          headers: USER_EMAIL ? { "X-User-Email": USER_EMAIL } : {},
        });

        if (!r.ok) throw new Error(`HTTP ${r.status}`);

        const data = (await r.json()) as PixBalancePayload;

        const serie: DayPoint[] = (data.ultimos_7d || []).map((d) => {
          const entradas = d.entradas || 0;
          const saidas = d.saidas || 0;
          return {
            dia: d.dia,
            entradas,
            saidas,
            net: entradas - saidas,
          };
        });

        console.log("LAB serie =>", serie);
        setPoints(serie);
      } catch (e: any) {
        console.error("LAB chart erro =>", e);
        setErr(e?.message ?? "Falha ao carregar gráfico LAB");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <div className="text-xs text-zinc-400">Carregando gráfico LAB...</div>;
  }

  if (err) {
    return <div className="text-xs text-red-400">Erro LAB: {err}</div>;
  }

  if (!points.length) {
    return (
      <div className="text-xs text-zinc-400">
        Sem dados para os últimos 7 dias (LAB).
      </div>
    );
  }

  const maxAbs =
    points.reduce((m, p) => Math.max(m, Math.abs(p.net || 0)), 0) || 1;

  // Monta pontos normalizados pra linha SVG
  const svgPoints = points.map((p, idx) => {
    const n = points.length;
    const x = n === 1 ? 50 : (idx / (n - 1)) * 100;

    // zero fica em y = 50, positivos pra cima, negativos pra baixo
    const yRaw = 50 - (p.net / maxAbs) * 40;
    const y = Math.max(10, Math.min(90, yRaw));

    return { x, y };
  });

  const poly = svgPoints.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <div className="mt-1 text-[11px]">
      <div className="relative h-40 overflow-hidden rounded-md bg-zinc-950/80">
        <svg
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="gold-lab-line" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#b68b2e" />
              <stop offset="50%" stopColor="#d4af37" />
              <stop offset="100%" stopColor="#f5e38a" />
            </linearGradient>
          </defs>

          {/* Linha base zero em y=50 */}
          <line
            x1={0}
            y1={50}
            x2={100}
            y2={50}
            stroke="#444"
            strokeWidth={0.5}
            strokeDasharray="2 3"
          />

          <polyline
            points={poly}
            fill="none"
            stroke="url(#gold-lab-line)"
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {svgPoints.map((p, idx) => (
            <circle
              key={idx}
              cx={p.x}
              cy={p.y}
              r={1.8}
              fill="#050505"
              stroke="#d4af37"
              strokeWidth={0.8}
            />
          ))}
        </svg>
      </div>
    </div>
  );
}
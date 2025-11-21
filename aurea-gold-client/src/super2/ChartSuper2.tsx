import React, { useEffect, useState } from "react";
import { fetchPixHistory7d } from "./api";

interface Point {
  dia: string;
  valor: number;
}

export default function ChartSuper2() {
  const [points, setPoints] = useState<Point[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setErr(null);

        const r: any = await fetchPixHistory7d();
        console.log("[Super2][history7d] raw:", r);

        let rows: any[] = [];

        // 1) formatos mais prováveis
        if (Array.isArray(r?.historico)) {
          rows = r.historico;
        } else if (Array.isArray(r?.data)) {
          rows = r.data;
        } else if (Array.isArray(r?.items)) {
          rows = r.items;
        } else if (Array.isArray(r?.rows)) {
          rows = r.rows;
        } else if (Array.isArray(r)) {
          // resposta já é um array
          rows = r;
        } else if (r && typeof r === "object") {
          // 2) fallback: pega o primeiro array de dentro do objeto
          const candidateArrays = Object.values(r).filter((v) =>
            Array.isArray(v)
          ) as any[][];
          if (candidateArrays.length > 0) {
            rows = candidateArrays[0];
          }
        }

        console.log("[Super2][history7d] rows len:", rows.length);

        const mapped: Point[] = rows.map((h: any) => ({
          dia: String(h.dia ?? h.data ?? h.dia_label ?? "?"),
          valor: Number(
            h.saldo ??
              h.valor ??
              h.total ??
              h.quantia ??
              h.amount ??
              0
          ),
        }));

        setPoints(mapped);
      } catch (e: any) {
        console.error("[Super2][history7d] erro:", e);
        setErr(e?.message ?? "Erro ao carregar gráfico");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) {
    return (
      <div className="text-[11px] text-[#d4af37]">
        Carregando gráfico...
      </div>
    );
  }

  if (err) {
    return (
      <div className="text-[11px] text-red-400">
        {err}
      </div>
    );
  }

  if (!points.length) {
    return (
      <div className="text-[11px] text-yellow-400">
        Sem dados suficientes para o gráfico.
      </div>
    );
  }

  return (
    <div className="aurea-chart-box space-y-1">
      {points.map((p) => (
        <div key={p.dia} className="aurea-chart-row flex items-center gap-2">
          <span className="aurea-chart-label w-16 text-[10px] opacity-70">
            {p.dia}
          </span>
          <div className="flex-1 h-2 rounded-full bg-[#222] overflow-hidden">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-[#d4af37] to-[#f7e27a] shadow-[0_0_6px_#d4af37]"
              style={{
                width: `${Math.min(Math.max(p.valor, 0) * 0.1, 100)}%`,
              }}
            />
          </div>
          <span className="aurea-chart-value w-20 text-right text-[10px]">
            R$ {p.valor.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
}

import React, { useEffect, useState } from "react";
import { getToken } from "../lib/auth";

import { API_BASE, USER_EMAIL } from "./api";
import { authHeaders } from "../lib/auth";

import {
  ResponsiveContainer,
  ComposedChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Bar,
  Line,
  ReferenceLine,
  LabelList,
} from "recharts";

type Pix7dPoint = {
  dia: string;
  entradas: number;
  saidas: number;
  saldo_dia: number;
};

type Pix7dResponse = {
  ultimos_7d: Pix7dPoint[];
};

interface AureaPixChartProps {
  // opcional: se o painel quiser injetar dados manualmente
  summary?: Pix7dResponse | null;
}

// Dados simulados para modo LAB quando a API falhar
const FALLBACK_PIX7D: Pix7dResponse = {
  ultimos_7d: [],
};

function fmtBRL(v: number | undefined): string {

  const n = typeof v === "number" && !Number.isNaN(v) ? v : 0;
  return (
    "R$ " +
    n
      .toFixed(2)
      .replace(".", ",")
  );
}

function fmtDiaShort(label: any): string {
  const s = String(label ?? "");
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) return `${m[3]}/${m[2]}`;
  return s;
}

function fmtDiaLong(label: any): string {
  const s = String(label ?? "");
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) return `${m[3]}/${m[2]}/${m[1]}`;
  return s;
}

const AureaPixChart: React.FC<AureaPixChartProps> = ({ summary }) => {
  const [data, setData] = useState<Pix7dResponse | null>(summary ?? null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // se o pai mandar summary no futuro, atualiza
  useEffect(() => {
    if (summary) {
      setData(summary);
    }
  }, [summary]);

  // se NÃO vier summary, o próprio gráfico busca /api/v1/pix/balance?days=7
  useEffect(() => {
    if (summary) return; // pai controla os dados

    let alive = true;

    async function load() {
      const pickJWT = (k: string) => {
      const v =
        (typeof window !== "undefined" && localStorage.getItem(k)) || "";
      // JWT real: 3 partes + tamanho mínimo (evita token curto/lixo)
      return v.split(".").length === 3 && v.length > 120 ? v : "";
    };

    const accessToken =
      pickJWT("aurea.jwt") ||
      pickJWT("aurea_jwt") ||
      pickJWT("aurea.access_token") ||
      pickJWT("aurea_access_token") ||
      pickJWT("authToken") ||
      "";

    try {
        setLoading(true);
        setErr(null);
        const r = await fetch(`${API_BASE}/api/v1/pix/balance?days=7`, {
          method: "GET",
          headers: { ...authHeaders(), 
            ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
          },
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = (await r.json()) as any;
        const ult = Array.isArray(j?.ultimos_7d) ? j.ultimos_7d : [];
        
        const payload: Pix7dResponse = { ultimos_7d: ult };
        if (!alive) return;
        setData(payload);
      } catch (e: any) {
        if (!alive) return;
        // MODO LAB: em vez de quebrar com erro, caímos para dados simulados
        console.error("[AureaPixChart] Falha ao carregar /api/v1/pix/balance?days=7, usando dados simulados:", e);
        setErr(e?.message ?? "Falha ao carregar dados reais agora (modo LAB).");
        setData(FALLBACK_PIX7D);
      } finally {
        if (alive) setLoading(false);
      }
    }

    load();
    return () => {
      alive = false;
    };
  }, [summary]);

  const raw = (data?.ultimos_7d ?? []) as Pix7dPoint[];

  if (loading && !raw.length) {
    return (
      <p className="aurea-chart__empty text-[11px] opacity-70">
        Carregando gráfico dos últimos 7 dias…
      </p>
    );
  }

  // Se der erro MAS já temos fallback, mostramos só um aviso discreto
  if (err && raw.length) {
    return (
      <div className="space-y-1">
        <p className="aurea-chart__empty text-[11px] opacity-70">
          Não foi possível carregar os dados reais agora (modo LAB).
        </p>
        <ChartInner raw={raw} />
      </div>
    );
  }

  if (!raw.length) {
    return (
      <p className="aurea-chart__empty text-[11px] opacity-60">
        Sem dados suficientes para montar o gráfico dos últimos 7 dias.
      </p>
    );
  }

  return <ChartInner raw={raw} />;
};

function ChartInner({ raw }: { raw: Pix7dPoint[] }) {
  const TooltipContent = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;
    const row = (payload?.[0]?.payload ?? {}) as any;
    const entradas = Number(row.entradas ?? 0);
    const saidas = Number(row.saidas ?? 0);
    const saldo = Number(row.saldo ?? 0);
    return (
      <div className="rounded-xl border border-amber-500/30 bg-black/90 px-3 py-2 text-[11px] text-zinc-100">
        <div className="mb-1 text-[11px] font-semibold opacity-90">{`Dia ${fmtDiaLong(label)}`}</div>
        <div className="flex justify-between gap-4"><span className="opacity-70">Entradas</span><span>{fmtBRL(entradas)}</span></div>
        <div className="flex justify-between gap-4"><span className="opacity-70">Saídas</span><span>{fmtBRL(saidas)}</span></div>
        <div className="mt-1 flex justify-between gap-4 border-t border-white/10 pt-1"><span className="opacity-70">Saldo</span><span>{fmtBRL(saldo)}</span></div>
      </div>
    );
  };

  const chartData = raw.map((d) => ({
    name: d.dia,
    entradas: Number(d.entradas ?? 0),
    saidas: Number(d.saidas ?? 0),
    saldo: Number(d.saldo_dia ?? 0),
  }));
  const hasEntradas = chartData.some((d) => d.entradas !== 0);
  const hasSaidas = chartData.some((d) => d.saidas !== 0);
  const allVals = chartData.flatMap((d) => [d.entradas, d.saidas, d.saldo]);
  const minV = Math.min(0, ...(allVals.length ? allVals : [0]));
  const maxV = Math.max(0, ...(allVals.length ? allVals : [0]));
  const pad = Math.max(50, Math.round((maxV - minV) * 0.12));
  const domain: [number, number] = [minV - pad, maxV + pad];
  const allZero = chartData.every(
    (d) => (d.entradas === 0 && d.saidas === 0 && d.saldo === 0)
  );

  if (allZero) {
    return (
      <div
        className="aurea-chart aurea-card aurea-card--chart mt-2"
        style={{ marginTop: "0.5rem" }}
      >
        <div className="aurea-chart__header mb-1">
          <div className="text-[10px] uppercase tracking-wide opacity-80">
            Fluxo PIX — últimos 7 dias
          </div>
          <div className="text-[10px] opacity-60">
            Sem movimentações no período
          </div>
        </div>

        <p className="text-[11px] opacity-70">
          Ainda não há entradas/saídas registradas nos últimos 7 dias. Faça um PIX
          para iniciar seu histórico.
        </p>
      </div>
    );
  }



  return (
    <div
      className="aurea-chart aurea-card aurea-card--chart mt-2"
      style={{ marginTop: "0.5rem" }}
    >
      <div className="aurea-chart__header mb-1">
        <div className="text-[10px] uppercase tracking-wide opacity-80">
          Fluxo PIX — últimos 7 dias
        </div>
        <div className="text-[10px] opacity-60">
          Entradas, saídas e saldo diário
        </div>
      </div>

      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer width="100%" height={220} minWidth={0} minHeight={220}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="name" tickFormatter={(v) => fmtDiaShort(v)} />
            <YAxis
              domain={domain}
              tickFormatter={(v) => fmtBRL(Number(v)).replace("R$ ", "")}
            />
            <Tooltip content={TooltipContent} />
            <Legend />
            <ReferenceLine y={0} strokeDasharray="3 3" opacity={0.35} />
            {hasEntradas && (
              <Bar
                dataKey="entradas"
                name="Entradas"
                barSize={18}
                radius={[6, 6, 0, 0]}
              />
            )}

            {hasSaidas && (
              <Bar
                dataKey="saidas"
                name="Saídas"
                barSize={18}
                radius={[6, 6, 0, 0]}
              />
            )}
<Line
              type="monotone"
              dataKey="saldo"
              name="Saldo"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            >
              <LabelList
                dataKey="saldo"
                position="top"
                formatter={(v: any) => {
                  const n = Number(v);
                  if (!n) return "";
                  return fmtBRL(n).replace("R$ ", "");
                }}
              />
            </Line>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default AureaPixChart;
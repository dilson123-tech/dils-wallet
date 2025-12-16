import React, { useEffect, useState } from "react";

import { API_BASE, USER_EMAIL } from "./api";
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
  ultimos_7d: [
    { dia: "Seg", entradas: 1200, saidas: 800, saldo_dia: 400 },
    { dia: "Ter", entradas: 900, saidas: 600, saldo_dia: 300 },
    { dia: "Qua", entradas: 1500, saidas: 1100, saldo_dia: 400 },
    { dia: "Qui", entradas: 700, saidas: 500, saldo_dia: 200 },
    { dia: "Sex", entradas: 2000, saidas: 1400, saldo_dia: 600 },
    { dia: "Sáb", entradas: 800, saidas: 700, saldo_dia: 100 },
    { dia: "Dom", entradas: 600, saidas: 400, saldo_dia: 200 },
  ],
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

  // se NÃO vier summary, o próprio gráfico busca /api/v1/pix/7d
  useEffect(() => {
    if (summary) return; // pai controla os dados

    let alive = true;

    async function load() {
      try {
        setLoading(true);
        setErr(null);
        const r = await fetch(`${API_BASE}/api/v1/pix/balance?days=7`, {
          method: "GET",
          headers: {
            "X-User-Email": USER_EMAIL,
          },
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = (await r.json()) as any;
        const ult = Array.isArray(j?.ultimos_7d) ? j.ultimos_7d : [];
        if (!ult.length) throw new Error('payload_sem_ultimos_7d');
        const payload: Pix7dResponse = { ultimos_7d: ult };
        if (!alive) return;
        setData(payload);
      } catch (e: any) {
        if (!alive) return;
        // MODO LAB: em vez de quebrar com erro, caímos para dados simulados
        console.error("[AureaPixChart] Falha ao carregar /api/v1/pix/7d, usando dados simulados:", e);
        setErr(e?.message ?? "Falha ao carregar dados reais, usando exemplo LAB.");
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
          Não foi possível carregar os dados reais agora. Exibindo exemplo
          simulado dos últimos 7 dias (modo LAB).
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
  const chartData = raw.map((d) => ({
    name: d.dia,
    entradas: Number(d.entradas ?? 0),
    saidas: Number(d.saidas ?? 0),
    saldo: Number(d.saldo_dia ?? 0),
  }));

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
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={220}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="name" />
            <YAxis
              tickFormatter={(v) =>
                fmtBRL(Number(v)).replace("R$ ", "")
              }
            />
            <Tooltip
              formatter={(value: any, name: string) => [
                fmtBRL(Number(value)),
                name === "entradas"
                  ? "Entradas"
                  : name === "saidas"
                  ? "Saídas"
                  : "Saldo",
              ]}
            />
            <Legend />

            <Bar
              dataKey="entradas"
              name="Entradas"
              barSize={18}
              radius={[6, 6, 0, 0]}
            />
            <Bar
              dataKey="saidas"
              name="Saídas"
              barSize={18}
              radius={[6, 6, 0, 0]}
            />

            <Line
              type="monotone"
              dataKey="saldo"
              name="Saldo"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default AureaPixChart;

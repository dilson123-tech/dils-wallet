import React, { useEffect, useState } from "react";
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
        const r = await fetch("/api/v1/pix/7d");
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = (await r.json()) as Pix7dResponse;
        if (!alive) return;
        setData(j);
      } catch (e: any) {
        if (!alive) return;
        setErr(e?.message ?? "Falha ao carregar dados do gráfico");
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

  if (err && !raw.length) {
    return (
      <p className="aurea-chart__empty text-[11px] text-red-400">
        Erro ao carregar gráfico: {err}
      </p>
    );
  }

  if (!raw.length) {
    return (
      <p className="aurea-chart__empty text-[11px] opacity-60">
        Sem dados suficientes para montar o gráfico dos últimos 7 dias.
      </p>
    );
  }

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
        <ResponsiveContainer>
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
};

export default AureaPixChart;

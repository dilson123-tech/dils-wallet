import React from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
  BarChart, Bar, Legend
} from "recharts";

type Pt = Record<string, any>;

type Props = {
  data?: Pt[];           // pode vir vazio/undefined
  type?: "line" | "bar"; // default line
  xKey?: string;         // se não vier, tentamos inferir
  yKey?: string;         // se não vier, tentamos inferir
  color?: string;        // cor padrão gold
};

/** tenta inferir primeiro campo string (x) e primeiro numérico (y) */
function inferKeys(rows: Pt[] | undefined): { xKey?: string; yKey?: string } {
  if (!rows || rows.length === 0) return {};
  const sample = rows.find(r => r && typeof r === "object");
  if (!sample) return {};
  let xKey: string | undefined;
  let yKey: string | undefined;
  for (const k of Object.keys(sample)) {
    const v = (sample as any)[k];
    if (!xKey && typeof v === "string") xKey = k;
    if (!yKey && typeof v === "number") yKey = k;
    if (xKey && yKey) break;
  }
  return { xKey, yKey };
}

export default function SummaryChart({
  data,
  type = "line",
  xKey,
  yKey,
  color = "#f2c94c",
}: Props) {
  // dados fake só para diagnóstico local, se não vier nada do pai
  const fake: Pt[] = [
    { label: "Seg", value: 10 },
    { label: "Ter", value: 20 },
    { label: "Qua", value: 15 },
    { label: "Qui", value: 25 },
    { label: "Sex", value: 30 },
  ];

  // usa data se veio array válido; senão usa fake
  const rows = Array.isArray(data) && data.length ? data : fake;

  const inferred = !xKey || !yKey ? inferKeys(rows) : {};
  const X = xKey || inferred.xKey || "label";
  const Y = yKey || inferred.yKey || "value";

  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height="100%">
        {type === "line" ? (
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
            <XAxis dataKey={X} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="basis" dataKey={Y} stroke={color} strokeWidth={3} dot={false} />
          </LineChart>
        ) : (
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
            <XAxis dataKey={X} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={Y} fill={color} />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

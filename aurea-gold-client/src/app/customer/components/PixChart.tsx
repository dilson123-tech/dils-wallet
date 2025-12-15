import React from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

type Tx = { created_at?: string; valor?: number; tipo?: string };

function toSeries(txs: Tx[]) {
  const clean = (txs || [])
    .filter(t => t && (t.created_at || typeof t.valor === "number"))
    .map(t => ({
      date: t.created_at ? new Date(t.created_at) : new Date(),
      value: Number(t.valor || 0),
    }))
    .sort((a,b) => a.date.getTime() - b.date.getTime());

  // série cumulativa (saldo incremental)
  let acc = 0;
  return clean.map((p, i) => {
    acc += p.value;
    return {
      name: p.date.toLocaleDateString("pt-BR", { day:"2-digit", month:"2-digit" }),
      value: Math.max(0, p.value),      // valor do ponto
      saldo: acc,                       // saldo cumulativo (se quiser trocar para 'saldo')
    };
  });
}

export default function PixChart({ txs }: { txs: Tx[] }) {
  const data = toSeries(txs);
  if (!data.length) {
    return (
      <div style={{
        minHeight: 200,
        background: "rgba(255,215,0,.06)",
        border: "1px solid rgba(255,215,0,.18)",
        borderRadius: 10,
        display: "flex", alignItems: "center", justifyContent: "center",
        color: "rgba(255,215,0,.45)"
      }}>
        Sem dados suficientes para o gráfico
      </div>
    );
  }

  return (
    <div style={{ width: "100%", minHeight: 240 }}>
      <div data-aurea-rc="wrap220" style={{ width: "100%", height: 220 }}>
      <ResponsiveContainer width="100%" height="100%" minWidth={280} minHeight={220}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"  stopColor="#FFD700" stopOpacity={0.9}/>
              <stop offset="100%" stopColor="#FFD700" stopOpacity={0.15}/>
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,215,0,.12)" vertical={false} />
          <XAxis dataKey="name" stroke="#FFD700" tick={{ fill:"#FFD700", fontSize:12 }} />
          <YAxis stroke="#FFD700" tick={{ fill:"#FFD700", fontSize:12 }} />
          <Tooltip contentStyle={{ background:"#111", border:"1px solid rgba(255,215,0,.4)" }} />
          <Area type="monotone" dataKey="value" stroke="#FFD700" strokeWidth={3} fill="url(#goldGrad)" />
        </AreaChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}

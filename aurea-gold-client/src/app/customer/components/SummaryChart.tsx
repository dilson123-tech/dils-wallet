import React from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function SummaryChart({ data }: { data?: { dia: string; valor: number }[] }) {
  const rows = Array.isArray(data) ? data : [];
  return (
    <div className="w-full h-48">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={rows}>
          <XAxis dataKey="dia" hide={false} />
          <YAxis hide />
          <Tooltip />
          <Area type="monotone" dataKey="valor" stroke="#d4af37" fill="#d4af37" fillOpacity={0.25} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

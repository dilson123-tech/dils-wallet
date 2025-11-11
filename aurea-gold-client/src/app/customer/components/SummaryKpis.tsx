import { useEffect, useState } from "react";
import { fetchSummary, SummaryRes } from "@/services/summary";

function fmt(v:number){ return v.toLocaleString("pt-BR",{style:"currency",currency:"BRL"}); }

export default function SummaryKpis() {
  const [data, setData] = useState<SummaryRes|null>(null);
  const [err, setErr]   = useState<string>("");

  useEffect(() => {
    fetchSummary().then(setData).catch(e=>setErr(String(e)));
  }, []);

  if (err) return <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700">Erro: {err}</div>;
  if (!data) return <div className="p-4 rounded-xl bg-gray-50 border text-gray-600 animate-pulse">Carregando resumo…</div>;

  const m = data.metrics;

  const kpi = (label:string, value:string, extra?:string, pos?:boolean) => (
    <div className="p-4 rounded-2xl shadow-sm bg-white border">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-2xl font-semibold">{value}</div>
      {extra && <div className={`text-sm ${pos ? "text-emerald-600":"text-gray-500"}`}>{extra}</div>}
    </div>
  );

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpi("Envios", fmt(m.total_envios), `${m.qtd_envios} transações`)}
      {kpi("Recebimentos", fmt(m.total_recebimentos), `${m.qtd_recebimentos} entradas`)}
      {kpi("Saldo estimado", fmt(m.saldo_estimado), (m.saldo_estimado>=0?"positivo":"negativo"), m.saldo_estimado>=0)}
      {kpi("Saldo (modelo)", m.saldo_model!=null?fmt(m.saldo_model):"—")}
    </div>
  );
}

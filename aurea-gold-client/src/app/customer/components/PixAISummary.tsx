import { useEffect, useState } from "react";
import { getPixSummary } from "@/lib/api";

type Summary = Awaited<ReturnType<typeof getPixSummary>>;

export default function PixAISummary({ hours = 24 }: { hours?: number }) {
  const [data, setData] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getPixSummary(hours)
      .then((j) => { if (alive) { setData(j); setErr(null); } })
      .catch((e) => { if (alive) setErr(String(e)); })
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [hours]);

  if (loading) return <div className="aurea-card">Carregando resumo de PIX…</div>;
  if (err) return <div className="aurea-card text-red-400">Erro: {err}</div>;
  if (!data) return null;

  const br = (n: number) => n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

  return (
    <section className="aurea-card" style={{ display:"grid", gap:12 }}>
      <header style={{ fontWeight:600, fontSize:18 }}>Resumo de PIX (últimas {data.ultimas_horas}h)</header>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,minmax(0,1fr))", gap:12 }}>
        <Metric label="Saldo atual" value={br(data.saldo_atual)} />
        <Metric label="Entradas (histórico)" value={br(data.entradas_total)} />
        <Metric label="Saídas (histórico)" value={br(data.saidas_total)} />
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,minmax(0,1fr))", gap:12 }}>
        <Metric label="Entradas (janela)" value={br(data.(ultimas_janela?.entradas ?? 0))} />
        <Metric label="Saídas (janela)" value={br(data.ultimas_janela.saidas)} />
        <Metric label="Transações (janela)" value={String(data.ultimas_janela.qtd)} />
      </div>
      <small style={{ opacity:.7 }}>Desde: {new Date(data.ultimas_janela.desde).toLocaleString("pt-BR")}</small>
    </section>
  );
}

function Metric({ label, value }: { label:string; value:string }) {
  return (
    <div className="aurea-metric" style={{ padding:12, border:"1px solid #444", borderRadius:10 }}>
      <div style={{ fontSize:12, opacity:.8 }}>{label}</div>
      <div style={{ fontSize:18, fontWeight:700 }}>{value}</div>
    </div>
  );
}

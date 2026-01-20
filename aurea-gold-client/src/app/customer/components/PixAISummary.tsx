// @ts-nocheck
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
    getPixSummary()
      .then((j) => { if (alive) { setData(j as Summary); setErr(null); } })
      .catch((e) => alive && setErr(String(e)))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [hours]);

  if (loading) return <div className="aurea-card">Carregando resumo de PIX…</div>;
  if (err) return <div className="aurea-card text-red-400">Erro: {err}</div>;
  if (!data) return null;

  const d: any = data;
  const ultimas_janela = d?.ultimas_janela ?? {};
  const br = (n: number) => Number(n ?? 0).toLocaleString("pt-BR", { style:"currency", currency:"BRL" });

  return (
    <section className="aurea-card" style={{ display:"grid", gap:12 }}>
      <header style={{ fontWeight:600, fontSize:18 }}>Resumo de PIX (últimas {d?.ultimas_horas ?? hours}h)</header>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,minmax(0,1fr))", gap:12 }}>
        <Metric label="Saldo atual" value={br(d?.saldo_atual ?? 0)} />
        <Metric label="Entradas (histórico)" value={br(d?.entradas_total ?? 0)} />
        <Metric label="Saídas (histórico)" value={br(d?.saidas_total ?? 0)} />
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,minmax(0,1fr))", gap:12 }}>
        <Metric label="Entradas (janela)" value={br(ultimas_janela?.entradas ?? 0)} />
        <Metric label="Saídas (janela)" value={br(ultimas_janela?.saidas ?? 0)} />
        <Metric label="Transações (janela)" value={String(ultimas_janela?.qtd ?? 0)} />
      </div>

      <small style={{ opacity:.7 }}>
        Desde: {ultimas_janela?.desde ? new Date(ultimas_janela.desde).toLocaleString("pt-BR") : "—"}
      </small>
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

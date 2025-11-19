import React, { useEffect, useState } from "react";
import StatCard from "./StatCard";

const fmtBR = (v: number) => `R$ ${Number((v ?? 0)).toFixed(2)}`;

type UltimasJanela = {
  entradas?: number;
  saidas?: number;
  qtd?: number;
  desde?: string | number | Date;
};

type AISummary = {
  saldo_atual: number;
  entradas_total?: number;
  saidas_total?: number;
  ultimas_horas?: number;
  ultimas_janela?: UltimasJanela;
};

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function AureaFloatingReport() {
  const [data, setData] = useState<AISummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setErr(null);
      const r = await fetch(`${API_BASE}/api/v1/ai/summary`, { method: "GET" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = (await r.json()) as AISummary;
      setData(j);
    } catch (e: any) {
      setErr(e?.message ?? "Falha ao carregar");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const glow = "0 0 22px rgba(255,204,51,.25)";
  const box: React.CSSProperties = { position:"fixed", right:18, bottom:18, zIndex:60, width:360, maxWidth:"92vw" };

  const d: AISummary = (data ?? {}) as AISummary;
  const win: UltimasJanela = (d.ultimas_janela ?? {}) as UltimasJanela;

  return (
    <aside style={box}>
      <div className="aurea-card" style={{ padding: 14 }}>
        <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:10 }}>
          <span className="aurea-chip" style={{ boxShadow: glow }}>Relatório</span>
          <div style={{ fontWeight:800, letterSpacing:.3 }}>Entradas &amp; Saídas (24h)</div>
          <button onClick={load} title="Atualizar" style={{
            marginLeft:"auto", background:"transparent",
            border:"1px solid rgba(255,204,51,.3)", color:"#ffcc33",
            padding:"4px 8px", borderRadius:8
          }}>↻</button>
        </div>

        {loading && <div style={{ opacity:.7 }}>Carregando…</div>}
        {err && <div style={{ color:"#ff6b6b" }}>Erro: {err}</div>}

        {data && (
          <>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
              <StatCard title="Saldo atual" value={fmtBR(d.saldo_atual ?? 0)} />
              <StatCard title="Movtos (24h)" value={String(win.qtd ?? 0)} />
              <StatCard title="Entradas (24h)" value={fmtBR(win.entradas ?? 0)} />
              <StatCard title="Saídas (24h)" value={fmtBR(win.saidas ?? 0)} />
            </div>
            <div style={{ display:"flex", gap:8, marginTop:12, alignItems:"center" }}>
              <small style={{ opacity:.6 }}>
                Desde: {win.desde ? new Date(win.desde).toLocaleString("pt-BR") : "—"}
              </small>
              <button
                onClick={() => window.dispatchEvent(new CustomEvent("aurea:open-ia"))}
                className="aurea-chip" style={{ marginLeft:"auto" }}
              >🤖 IA 3.0</button>
            </div>
          </>
        )}
      </div>
    </aside>
  );
}

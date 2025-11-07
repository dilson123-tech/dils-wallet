import React, { useEffect, useState } from "react";

type Summary = {
  saldo_atual: number;
  entradas_total: number;
  saidas_total: number;
  ultimas_horas: number;
  ultimas_janela: { entradas: number; saidas: number; qtd: number; desde: string };
};

export default function Dashboard() {
  const [data, setData] = useState<Summary | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    console.log("🚀 Dashboard carregado com sucesso!");
    fetch("https://dils-wallet-production.up.railway.app/api/v1/ai/summary", {
      headers: { "Accept": "application/json" },
    })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch(e => setErr(String(e)));
  }, []);

  return (
    <div style={{
      minHeight: "calc(100vh - 120px)",
      background: "linear-gradient(135deg,#0b0b0b 0%, #151515 60%, #0b0b0b 100%)",
      color: "#eee",
      padding: "16px",
      borderRadius: 12,
      border: "1px solid #333"
    }}>
      <h1 style={{ color: "#d4af37", margin: 0, fontWeight: 800, letterSpacing: 1 }}>Dashboard Aurea Gold</h1>
      <p style={{ opacity: .8, marginTop: 6 }}>Painel de status da Aurea IA 3.0 + PIX</p>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: 16,
        marginTop: 16
      }}>
        <section style={{ padding: 16, borderRadius: 12, background: "#1b1b1b", border: "1px solid #444" }}>
          <h3 style={{ marginTop: 0, color: "#f0c75e" }}>Resumo Inteligente (24h)</h3>
          {err && <div style={{ color: "#ff6666" }}>Erro: {err}</div>}
          {!data && !err && <div style={{ opacity: .7 }}>Carregando…</div>}
          {data && (
            <pre style={{
              background: "#0f0f0f",
              border: "1px solid #333",
              borderRadius: 8,
              padding: 12,
              overflowX: "auto"
            }}>{JSON.stringify(data, null, 2)}</pre>
          )}
        </section>

        <section style={{ padding: 16, borderRadius: 12, background: "#1b1b1b", border: "1px solid #444" }}>
          <h3 style={{ marginTop: 0, color: "#f0c75e" }}>Indicadores</h3>
          <ul style={{ lineHeight: 1.8, listStyle: "none", paddingLeft: 0, margin: 0 }}>
            <li>Saldo atual: <strong style={{ color: "#9fd" }}>{data ? data.saldo_atual.toFixed(2) : "—"}</strong></li>
            <li>Entradas: <strong style={{ color: "#9f9" }}>{data ? data.entradas_total.toFixed(2) : "—"}</strong></li>
            <li>Saídas: <strong style={{ color: "#f99" }}>{data ? data.saidas_total.toFixed(2) : "—"}</strong></li>
            <li>Movtos 24h: <strong>{data ? data.ultimas_janela.qtd : "—"}</strong></li>
          </ul>
        </section>
      </div>
    </div>
  );
}

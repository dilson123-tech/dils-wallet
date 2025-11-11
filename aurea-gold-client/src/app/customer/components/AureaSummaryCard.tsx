import React, { useEffect, useRef, useState } from "react";

const API = (import.meta as any).env?.VITE_API_BASE || "http://127.0.0.1:8080";
const REFRESH_MS = Number((import.meta as any).env?.VITE_AI_REFRESH_MS ?? 30000); // 30s padrão

type WindowStats = { entradas: number; saidas: number; qtd: number };
type AISummary = {
  saldo_atual: number;
  entradas_total: number;
  saidas_total: number;
  ultimas_24h: WindowStats;
  ultimos_7d: WindowStats;
  qtd_transacoes: number;
  mensagem: string;
};

function fmtBR(n: number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n);
}

export default function AureaSummaryCard() {
  const [data, setData] = useState<AISummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const inflight = useRef(false);
  const timer = useRef<number | null>(null);

  async function fetchSummary() {
    if (inflight.current) return;           // evita concorrência
    inflight.current = true;
    try {
      setLoading(true);
      setErr(null);
      const r = await fetch(`${API}/api/v1/ai/summary`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ hours: 24 }) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = (await r.json()) as AISummary;
      setData(j);
    } catch (e: any) {
      setErr(e?.message || "Falha ao obter Resumo IA");
    } finally {
      setLoading(false);
      inflight.current = false;
    }
  }

  // inicial + auto-refresh com visibilidade da aba
  useEffect(() => {
    fetchSummary(); // primeira carga

    function start() {
      if (timer.current !== null) return;
      timer.current = window.setInterval(() => {
        if (document.visibilityState === "visible") fetchSummary();
      }, REFRESH_MS);
    }
    function stop() {
      if (timer.current !== null) {
        clearInterval(timer.current);
        timer.current = null;
      }
    }

    // pausa quando aba não está visível
    const vis = () => (document.visibilityState === "visible" ? start() : stop());
    document.addEventListener("visibilitychange", vis);
    start();

    return () => {
      document.removeEventListener("visibilitychange", vis);
      stop();
    };
  }, []);

  return (
    <div style={{
      marginTop: 14,
      padding: "12px 14px",
      borderRadius: 12,
      background: "linear-gradient(180deg,#191919,#0f0f0f)",
      border: "1px solid rgba(255, 209, 102, .35)",
      boxShadow: "0 10px 28px rgba(0,0,0,.35)"
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, marginBottom: 6 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: "50%",
            background: "radial-gradient(circle at 30% 30%, #ffd166, #caa44a 60%, #6b5a28)"
          }} />
          <div style={{ fontWeight: 700 }}>
            Resumo IA • Aurea Gold
          </div>
        </div>
        <button
          onClick={fetchSummary}
          disabled={loading}
          style={{
            padding: "6px 10px",
            borderRadius: 10,
            border: "1px solid #3a3a3a",
            background: loading ? "#202020" : "linear-gradient(180deg,#2a2a2a,#181818)",
            color: "#ddd",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: 12
          }}
          title={`Atualizar agora (auto ${Math.round(REFRESH_MS/1000)}s)`}
        >
          {loading ? "Atualizando…" : "Atualizar"}
        </button>
      </div>

      {err && <div style={{ color: "#ff6b6b", marginBottom: 6 }}>Erro: {err}</div>}

      {data && !err && (
        <div style={{ display: "grid", gap: 6 }}>
          <div style={{ opacity: .92 }}>{data.mensagem}</div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0,1fr))",
            gap: 8,
            marginTop: 6
          }}>
            <div style={{ background: "#141414", border: "1px solid #262626", borderRadius: 10, padding: "8px 10px" }}>
              <div style={{ fontSize: 12, opacity: .7 }}>Entradas (7d)</div>
              <div style={{ fontWeight: 700, color: "#06d6a0" }}>{fmtBR(data.(ultimos_7d?.entradas ?? 0))}</div>
            </div>
            <div style={{ background: "#141414", border: "1px solid #262626", borderRadius: 10, padding: "8px 10px" }}>
              <div style={{ fontSize: 12, opacity: .7 }}>Saídas (7d)</div>
              <div style={{ fontWeight: 700, color: "#ff6b6b" }}>{fmtBR(data.ultimos_7d.saidas)}</div>
            </div>
            <div style={{ background: "#141414", border: "1px solid #262626", borderRadius: 10, padding: "8px 10px" }}>
              <div style={{ fontSize: 12, opacity: .7 }}>Transações</div>
              <div style={{ fontWeight: 700 }}>{data.qtd_transacoes}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

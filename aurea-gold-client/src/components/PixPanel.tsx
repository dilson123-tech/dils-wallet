import React, { useState, useEffect } from "react";

// hardcode DEV estável pra garantir que o painel funcione agora
const API_BASE = "http://127.0.0.1:8080";
console.log("[PixPanel] API_BASE =", API_BASE);

// Tipos
type PixHistoryItem = {
  id: number;
  tipo: "entrada" | "saida";
  valor: number;
  descricao: string;
  timestamp: string | null;
};

type PixSummaryResponse = {
  saldo_pix: number;
};

type PixHistoryResponse = {
  history: PixHistoryItem[];
  recebidos: PixHistoryItem[];
  enviados: PixHistoryItem[];
};

export default function PixPanel() {
  const [saldoPix, setSaldoPix] = useState<number | null>(null);
  const [history, setHistory] = useState<PixHistoryItem[]>([]);

  const [saldoError, setSaldoError] = useState<string | null>(null);
  const [histError, setHistError] = useState<string | null>(null);

  const [loadingSaldo, setLoadingSaldo] = useState<boolean>(true);
  const [loadingHist, setLoadingHist] = useState<boolean>(true);

  // ----- Fetch Saldo -----
  async function fetchBalance() {
    setLoadingSaldo(true);
    try {
      const url = `${API_BASE}/api/v1/pix/balance`;
      console.log("[PixPanel] GET balance", url);

      const res = await fetch(url);
      console.log("[PixPanel] status balance =", res.status);

      if (!res.ok) throw new Error("Erro ao buscar saldo PIX");

      const data: PixSummaryResponse = await res.json();
      console.log("[PixPanel] balance data =", data);

      setSaldoPix(data.saldo_pix);
      setSaldoError(null);
    } catch (err: any) {
      console.error("[PixPanel] fetchBalance error:", err);
      setSaldoError(err.message || "Falha geral saldo");
    } finally {
      setLoadingSaldo(false);
    }
  }
  // ----- Fetch Histórico -----
  async function fetchHistory() {
    setLoadingHist(true);
    try {
      const url = `${API_BASE}/api/v1/pix/history`;
      console.log("[PixPanel] GET history", url);

      const res = await fetch(url);
      console.log("[PixPanel] status history =", res.status);

      if (!res.ok) throw new Error("Erro ao buscar histórico PIX");

      const data: PixHistoryResponse = await res.json();
      console.log("[PixPanel] history data =", data);

      setHistory(data.history || []);
      setHistError(null);
    } catch (err: any) {
      console.error("[PixPanel] fetchHistory error:", err);
      setHistError(err.message || "Falha geral histórico");
    } finally {
      setLoadingHist(false);
    }
  }

  // dispara no mount
  useEffect(() => {
    fetchBalance();
    fetchHistory();
  }, []);
  return (
    <div
      style={{
        color: "#fff",
        background: "#000",
        padding: "1rem",
        maxWidth: "520px",
        fontFamily: "system-ui, sans-serif",
        lineHeight: 1.4,
      }}
    >
      <h2 style={{ color: "gold", marginBottom: "0.5rem" }}>
        PIX • Aurea Gold
      </h2>

      {/* status saldo */}
      {saldoError && (
        <div style={{ color: "red", marginBottom: "0.5rem" }}>
          {saldoError}
        </div>
      )}

      <div style={{ marginBottom: "1rem" }}>
        <strong>Saldo PIX:</strong>{" "}
        {loadingSaldo
          ? "..."
          : saldoPix !== null
          ? `R$ ${saldoPix.toFixed(2)}`
          : "—"}
      </div>

      {/* histórico */}
      <h3
        style={{
          color: "gold",
          fontSize: "1rem",
          marginTop: "1rem",
          marginBottom: "0.5rem",
        }}
      >
        Histórico de Transações
      </h3>

      {histError && (
        <div style={{ color: "red", marginBottom: "0.5rem" }}>
          {histError}
        </div>
      )}

      {loadingHist ? (
        <div style={{ color: "#888" }}>Carregando...</div>
      ) : history.length === 0 ? (
        <div style={{ color: "#888" }}>Nenhuma transação ainda.</div>
      ) : (
        <ul
          style={{
            listStyle: "none",
            padding: 0,
            margin: 0,
            fontSize: "0.9rem",
            borderTop: "1px solid #333",
          }}
        >
          {history.map((item) => (
            <li
              key={item.id}
              style={{
                borderBottom: "1px solid #333",
                padding: "0.5rem 0",
                color:
                  item.tipo === "entrada" ? "lightgreen" : "#ff6868",
                display: "grid",
                gridTemplateColumns: "1fr auto",
                columnGap: "0.5rem",
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: "bold" }}>
                  {item.tipo === "entrada" ? "↑ Entrada" : "↓ Saída"}
                </div>
                <div style={{ color: "#aaa" }}>
                  {item.descricao || "— sem descrição —"}
                </div>
                <div
                  style={{
                    color: "#666",
                    fontSize: "0.75rem",
                    whiteSpace: "nowrap",
                  }}
                >
                  {item.timestamp || "sem horário"}
                </div>
              </div>

              <div
                style={{
                  fontWeight: "bold",
                  minWidth: "80px",
                  textAlign: "right",
                }}
              >
                R$ {item.valor.toFixed(2)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

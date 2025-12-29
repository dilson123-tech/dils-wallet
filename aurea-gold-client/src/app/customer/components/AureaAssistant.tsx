import React, { useState } from "react";
import { withAuth } from "../../../lib/api";

type AIRequestPayload = {
  message: string;
  user_id?: number;
};

type AIResponseData = {
  answer: string;
  saldo_atual?: number | null;
  resumo_pix?: {
    saldo_pix?: number;
    total_recebido?: number;
    total_enviado?: number;
    ultimas_transacoes?: {
      id: number;
      tipo: string;
      valor: number;
      descricao: string;
      timestamp: string | null;
    }[];
  } | null;
};

export default function AureaAssistant() {
  const [pergunta, setPergunta] = useState("");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resposta, setResposta] = useState<AIResponseData | null>(null);
  const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

  async function consultarIA(e: React.FormEvent) {
    e.preventDefault();
    if (!pergunta.trim()) return;

    setLoading(true);
    setErro(null);

    try {
      const payload: AIRequestPayload = {
        message: pergunta,
        user_id: 1,
      };

      const r = await fetch(`${API_BASE}/api/v1/ai/chat`, withAuth({
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }));

      if (!r.ok) {
        throw new Error("Falha ao consultar IA");
      }

      const data = (await r.json()) as AIResponseData;
      setResposta(data);
    } catch (err: any) {
      console.error("[AUREA IA] erro:", err);
      setErro(err.message || "Erro inesperado");
    } finally {
      setLoading(false);
    }
  }

  // formata número em R$
  function fmt(v: number | undefined | null) {
    if (v === undefined || v === null) return "--";
    return v.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 2,
    });
  }

  // escolhe cor conforme tipo de transação
  function corTipo(tipo: string) {
    if (tipo === "entrada") return "#00ff66"; // recebeu
    if (tipo === "saida") return "#ff4444";   // mandou
    return "#ffffff";
  }


  // resumo financeiro inteligente
  function renderResumoFinanceiro() {
    if (!resposta || !resposta.resumo_pix) return null;
    const resumo = resposta.resumo_pix;

    return (
      <div
        style={{
          marginTop: "12px",
          background:
            "radial-gradient(circle at 20% 20%, rgba(212,175,55,0.15) 0%, rgba(0,0,0,0) 70%)",
          border: "1px solid rgba(212,175,55,0.4)",
          borderRadius: "10px",
          padding: "12px",
          color: "#fff",
          fontSize: "0.8rem",
          lineHeight: 1.4,
        }}
      >
        <div
          style={{
            fontSize: "0.8rem",
            fontWeight: 600,
            color: "#d4af37",
            textTransform: "uppercase",
            marginBottom: "8px",
          }}
        >
          Inteligência Financeira Aurea Gold · BETA
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>
            <div style={{ color: "#888", fontSize: "0.65rem" }}>Saldo PIX</div>
            <div style={{ color: "#d4af37", fontWeight: 600 }}>
              {fmt(resposta.saldo_atual ?? resumo.saldo_pix)}
            </div>
          </div>
          <div>
            <div style={{ color: "#888", fontSize: "0.65rem" }}>Fluxo</div>
            <div style={{ fontSize: "0.7rem" }}>
              <span style={{ color: "#00ff66" }}>+{fmt(resumo.total_recebido)}</span> /{" "}
              <span style={{ color: "#ff4444" }}>-{fmt(resumo.total_enviado)}</span>
            </div>
          </div>
        </div>

        {resumo.ultimas_transacoes && resumo.ultimas_transacoes.length > 0 && (
          <div style={{ marginTop: "10px" }}>
            <div style={{ color: "#999", fontSize: "0.7rem", marginBottom: "4px" }}>
              Últimas transações
            </div>
            {resumo.ultimas_transacoes.slice(0, 2).map((tx) => (
              <div
                key={tx.id}
                style={{
                  border: "1px solid rgba(212,175,55,0.3)",
                  borderRadius: "6px",
                  padding: "6px",
                  marginBottom: "6px",
                  fontSize: "0.7rem",
                }}
              >
                <div style={{ color: corTipo(tx.tipo), fontWeight: 600 }}>
                  {tx.tipo === "entrada" ? "↘ Entrada" : "↗ Saída"} · {fmt(tx.valor)}
                </div>
                <div>{tx.descricao}</div>
                {tx.timestamp && (
                  <div style={{ color: "#888", fontSize: "0.6rem" }}>{tx.timestamp}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }


  return (
    <div
      style={{
        background:
          "radial-gradient(circle at 20% 20%, rgba(212,175,55,0.12) 0%, rgba(0,0,0,0) 70%)",
        border: "1px solid rgba(212,175,55,0.6)",
        borderRadius: "10px",
        boxShadow:
          "0 30px 80px rgba(0,0,0,0.95), 0 0 60px rgba(212,175,55,0.2)",
        padding: "16px",
        maxWidth: "360px",
        color: "#fff",
        fontFamily:
          '-apple-system,BlinkMacSystemFont,"Inter","Roboto","Segoe UI",sans-serif',
      }}
    >
      {/* Header */}
      <div
        style={{
          fontSize: "0.75rem",
          fontWeight: 600,
          color: "#d4af37",
          textTransform: "uppercase",
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <span>AUREA IA 3.0</span>
        <span
          style={{
            border: "1px solid #d4af37",
            padding: "2px 6px",
            borderRadius: "4px",
            fontSize: "0.6rem",
            fontWeight: 700,
            color: "#000",
            background:
              "linear-gradient(to right,#d4af37 0%,rgba(0,0,0,0) 70%)",
          }}
        >
          BETA
        </span>
      </div>

      <div style={{ fontSize: "0.7rem", color: "#ccc", marginTop: "4px" }}>
        Consultor financeiro inteligente
      </div>

      {/* Formulário */}
      <form onSubmit={consultarIA} style={{ marginTop: "12px" }}>
        <label
          style={{
            fontSize: "0.7rem",
            color: "#888",
            display: "block",
            marginBottom: "4px",
          }}
        >
          Pergunta pra IA
        </label>
        <input
          value={pergunta}
          onChange={(e) => setPergunta(e.target.value)}
          placeholder="Ex: quanto eu tenho de saldo no Pix?"
          style={{
            width: "100%",
            background: "rgba(0,0,0,0.6)",
            border: "1px solid rgba(212,175,55,0.4)",
            color: "#fff",
            padding: "8px",
            borderRadius: "4px",
            fontSize: "0.8rem",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            marginTop: "10px",
            background:
              "linear-gradient(to right,rgba(212,175,55,0.9),rgba(138,113,18,0.4))",
            border: "1px solid rgba(212,175,55,0.7)",
            color: "#000",
            fontWeight: 600,
            fontSize: "0.8rem",
            borderRadius: "4px",
            padding: "8px",
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "Consultando..." : "Perguntar"}
        </button>
      </form>

      {/* Mensagem de erro */}
      {erro && (
        <div
          style={{
            color: "#f88b8b",
            border: "1px solid #f88b8b",
            background: "rgba(80,0,0,0.4)",
            borderRadius: "6px",
            padding: "8px",
            fontSize: "0.7rem",
            marginTop: "12px",
          }}
        >
          {erro}
        </div>
      )}

      {/* Resposta IA */}
      {resposta && resposta.answer && (
        <div
          style={{
            marginTop: "12px",
            background: "rgba(0,0,0,0.5)",
            border: "1px solid rgba(212,175,55,0.4)",
            borderRadius: "6px",
            padding: "10px",
            fontSize: "0.8rem",
          }}
        >
          <div
            style={{
              fontSize: "0.7rem",
              color: "#d4af37",
              fontWeight: 600,
              marginBottom: "4px",
            }}
          >
            Análise da IA
          </div>
          {resposta.answer}
        </div>
      )}

      {/* Resumo financeiro */}
      {renderResumoFinanceiro()}
    </div>
  );
}

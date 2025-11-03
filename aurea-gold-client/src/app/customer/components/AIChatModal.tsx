import React, { useEffect, useState } from "react";

type Props = { open: boolean; onClose: () => void; };
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8080";

export default function AIChatModal({ open, onClose }: Props) {
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string>("");
  const [extra, setExtra] = useState<{ saldo_atual?: number; resumo_pix?: any }>({});
  const [raw, setRaw] = useState<any>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    function onKey(e: KeyboardEvent) { if (e.key === "Escape") onClose(); }
    if (open) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  async function ask() {
    if (!msg.trim()) return;
    setLoading(true); setAnswer(""); setError(""); setRaw(null);
    try {
      const r = await fetch(`${API_BASE}/api/v1/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg.trim(), user_id: 1 }),
      });

      let data: any = null;
      try { data = await r.json(); }
      catch {
        const t = await r.text();
        try { data = JSON.parse(t); } catch { data = { answer: t }; }
      }
      setRaw(data);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);

      // tenta vários campos comuns; se vier vazio, cai pro JSON inteiro
      const ansCandidate =
        (typeof data?.answer === "string" && data.answer) ||
        (typeof data?.message === "string" && data.message) ||
        (typeof data?.detail === "string" && data.detail) || "";

      const finalAns = (ansCandidate || "").trim().length
        ? ansCandidate
        : JSON.stringify(data, null, 2);

      setAnswer(finalAns);

      // extras conhecidos
      if (typeof data?.saldo_atual === "number" || data?.resumo_pix) {
        setExtra({ saldo_atual: data?.saldo_atual, resumo_pix: data?.resumo_pix });
      } else if (data?.resumo_pix?.saldo_atual) {
        setExtra({ saldo_atual: data.resumo_pix.saldo_atual, resumo_pix: data.resumo_pix });
      }

      // debug
      // eslint-disable-next-line no-console
      console.log("[AUREA IA][status]", r.status, "[payload]", data);
    } catch (e:any) {
      setError(e?.message || String(e));
      setAnswer("Sem resposta.");
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <header className="modal-header">
          <h3>Aurea Gold • IA 3.0</h3>
          <button className="modal-close" onClick={onClose} aria-label="Fechar">✕</button>
        </header>

        <div className="modal-body">
          <label className="gold-label">Mensagem</label>
          <textarea
            className="gold-input"
            rows={3}
            placeholder="Pergunte: ex. 'Resumo do meu saldo e últimos PIX'"
            value={msg}
            onChange={(e) => setMsg(e.target.value)}
          />
          <button className="gold-primary" onClick={ask} disabled={loading}>
            {loading ? "Consultando..." : "Perguntar à IA"}
          </button>

          <div className="ai-answer" style={{ marginTop: 12, whiteSpace: "pre-wrap" }}>
            <div className="ai-title">Resposta da IA</div>
            {loading ? <p>Carregando...</p> : <p>{answer}</p>}

            {typeof extra.saldo_atual === "number" && (
              <div className="ai-chip">Saldo atual: <b>R$ {extra.saldo_atual.toFixed(2)}</b></div>
            )}
            {extra.resumo_pix && (
              <details className="ai-details" open>
                <summary>Resumo PIX</summary>
                <pre>{JSON.stringify(extra.resumo_pix, null, 2)}</pre>
              </details>
            )}
            {error && (
              <div className="ai-chip" style={{borderColor:"rgba(255,99,99,.35)", background:"rgba(255,99,99,.12)"}}>
                Erro: {error}
              </div>
            )}
            {raw && (
              <details className="ai-details">
                <summary>JSON bruto (debug)</summary>
                <pre>{JSON.stringify(raw, null, 2)}</pre>
              </details>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

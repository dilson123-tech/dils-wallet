import React, { useMemo, useState } from "react";

type Msg = { role: "user" | "assistant" | "system" | "error"; content: string };
const API_BASE = String(import.meta.env.VITE_API_BASE || "").replace(/\/+$/, "");

export default function AureaIAConcierge() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "assistant", content: "Olá! Sou a Aurea IA 3.0. Como posso ajudar?" }
  ]);

  const endpoints = useMemo(() => [
    `${API_BASE}/api/v1/ai/chat`,
    `${API_BASE}/api/v1/ai/complete`,
    `${API_BASE}/api/v1/ai`
  ], []);

  async function askAurea(prompt: string) {
    setLoading(true);
    try {
      let res: Response | null = null;
      for (const url of endpoints) {
        try {
          res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt, messages: msgs }),
            credentials: "omit"
          });
          if (res.ok) break;
        } catch { /* tenta o próximo */ }
      }
      if (!res || !res.ok) throw new Error("Falha ao contatar a IA (verifique rota no backend).");

      // resposta em { reply: string } ou { message: string } — tratamos ambos
      const j = await res.json().catch(() => ({}));
      const reply = j.reply ?? j.message ?? JSON.stringify(j);
      setMsgs(m => [...m, { role: "assistant", content: String(reply) }]);
    } catch (e: any) {
      setMsgs(m => [...m, { role: "error", content: e?.message ?? String(e) }]);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q) return;
    setMsgs(m => [...m, { role: "user", content: q }]);
    setInput("");
    askAurea(q);
  }

  return (
    <>
      {/* FAB */}
      <button
        onClick={() => setOpen(o => !o)}
        title="Aurea IA 3.0"
        aria-label="Abrir chat da Aurea IA 3.0"
        style={{
          position: "fixed", right: 20, bottom: 20, zIndex: 60,
          border: "1px solid #b4871b",
          background: "linear-gradient(135deg,#f5d46b,#d3a62c)",
          color: "#0b0b0b", borderRadius: 999, padding: "12px 16px",
          fontWeight: 800, boxShadow: "0 8px 24px rgba(212,175,55,.35)"
        }}
      >
        🤖 Aurea IA
      </button>

      {/* Painel */}
      {open && (
        <aside
          role="dialog"
          aria-label="Aurea IA 3.0 Concierge"
          style={{
            position: "fixed", right: 20, bottom: 76, zIndex: 59,
            width: 380, height: "65vh",
            display: "flex", flexDirection: "column",
            background: "rgba(10,10,10,.92)", backdropFilter: "blur(6px)",
            border: "1px solid #2c240f", borderRadius: 12,
            boxShadow: "0 8px 24px rgba(0,0,0,.6)"
          }}
        >
          <header style={{ padding: "10px 12px", borderBottom: "1px solid #2c240f", display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontWeight: 800, color: "#f0c75e" }}>Aurea IA 3.0</span>
            <span style={{ marginLeft: "auto", opacity: .8, fontSize: 12 }}>{API_BASE ? "online" : "offline (VITE_API_BASE vazio)"}</span>
          </header>

          <div style={{ flex: 1, overflowY: "auto", padding: 12, display: "grid", gap: 10 }}>
            {msgs.map((m, i) => (
              <div key={i} style={{
                justifySelf: m.role === "user" ? "end" : "start",
                maxWidth: "85%",
                background: m.role === "user" ? "#1b1b1b" : (m.role === "error" ? "#2a1010" : "#121212"),
                border: "1px solid #333", borderRadius: 10, padding: "8px 10px", whiteSpace: "pre-wrap"
              }}>
                <div style={{ opacity: .7, fontSize: 12, marginBottom: 4 }}>
                  {m.role === "user" ? "Você" : m.role === "assistant" ? "Aurea" : "Erro"}
                </div>
                <div>{m.content}</div>
              </div>
            ))}
            {loading && <div style={{ opacity: .7 }}>Pensando…</div>}
          </div>

          <form onSubmit={onSubmit} style={{ padding: 10, display: "flex", gap: 8, borderTop: "1px solid #2c240f" }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Digite sua pergunta…"
              style={{
                flex: 1, background: "#0e0e0e", color: "#eee",
                border: "1px solid #333", borderRadius: 8, padding: "10px 12px"
              }}
            />
            <button
              type="submit"
              disabled={loading}
              style={{
                background: "linear-gradient(135deg,#f5d46b,#d3a62c)",
                color: "#0b0b0b", fontWeight: 800, borderRadius: 8,
                padding: "10px 14px", border: "1px solid #b4871b"
              }}
            >
              Enviar
            </button>
          </form>
        </aside>
      )}
    </>
  );
}

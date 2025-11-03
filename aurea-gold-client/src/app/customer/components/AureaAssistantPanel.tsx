import React, { useEffect, useRef, useState } from "react";

const API_BASE = (import.meta as any).env?.VITE_API_BASE || "http://127.0.0.1:8080";

type Msg = { role: "user" | "assistant"; text: string };
export default function AureaAssistantPanel() {
  const [open, setOpen] = useState(true);
  
  // empurra layout quando a IA abre
  useEffect(() => {
    document.body.classList.toggle("aurea-ia-open", open);
    return () => document.body.classList.remove("aurea-ia-open");
  }, [open]);

// empurra layout quando a IA abre
  useEffect(() => {
    document.body.classList.toggle("aurea-ia-open", open);
    return () => document.body.classList.remove("aurea-ia-open");
  }, [open]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "assistant", text: "Ola! Posso resumir seu saldo PIX e ultimas movimentacoes." }
  ]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // --- drag (desktop): desloca com translate(dx,dy) ---
  const [drag, setDrag] = useState({ dx: 0, dy: 0 });
  const dragging = useRef(false);
  const drag0 = useRef({ x: 0, y: 0, dx: 0, dy: 0 });

  function onDragStart(e: React.PointerEvent) {
    dragging.current = true;
    const p = (e as any);
    drag0.current = { x: p.clientX, y: p.clientY, dx: drag.dx, dy: drag.dy };
    (e.target as HTMLElement).setPointerCapture?.(p.pointerId ?? 1);
  }
  function onDragMove(e: React.PointerEvent) {
    if (!dragging.current) return;
    const p = (e as any);
    const dx = p.clientX - drag0.current.x + drag0.current.dx;
    const dy = p.clientY - drag0.current.y + drag0.current.dy;
    setDrag({ dx, dy });
  }
  function onDragEnd() { dragging.current = false; }
  // toggle via evento global (opcional)
  useEffect(() => {
    const onToggle = () => setOpen(v => !v);
    window.addEventListener("aurea-assistant:toggle", onToggle);
    return () => window.removeEventListener("aurea-assistant:toggle", onToggle);
  }, []);

  // autoscroll
  useEffect(() => {
    try {
      if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    } catch {}
  }, [msgs]);

  async function send() {
    if (!input.trim() || busy) return;
    const content = input.trim();
    setInput("");
    setMsgs(m => [...m, { role: "user", text: content }]);
    setBusy(true);
    try {
      const r = await fetch(`${API_BASE}/api/v1/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content, user_id: 1 })
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      const reply = j.reply ?? "Sem resposta no momento.";
      setMsgs(m => [...m, { role: "assistant", text: reply }]);
    } catch (e) {
      console.error("[AUREA IA] erro:", e);
      setMsgs(m => [...m, { role: "assistant", text: "Falha ao consultar IA. Tente novamente." }]);
    } finally {
      setBusy(false);
    }
  }

  function quickAsk(q: string) {
    if (busy) return;
    setInput(q);
    setTimeout(() => send(), 0);
  }

  function clearChat() {
    setMsgs([{ role: "assistant", text: "Chat limpo. Posso ajudar com seu PIX agora." }]);
  }

  return (
    <aside
      className="aurea-assistant"
      style={{
        position: "fixed",
        bottom: 24,
        right: 24,
        width: 360,
        height: "70vh",
        background: "#141414",
        border: "1px solid #b88900",
        borderRadius: 12,
        boxShadow: "0 0 16px rgba(255, 204, 51, .25)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
          transform: `translate(${drag.dx}px, ${drag.dy}px)`,
          touchAction: "none",
          cursor: "move",
        zIndex: 2000, pointerEvents: "auto"
      }}
    >
      <header onPointerDown={onDragStart} onPointerMove={onDragMove} onPointerUp={onDragEnd} onPointerCancel={onDragEnd} style={{
        height: 46, display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "0 12px", background: "linear-gradient(90deg, #000 0%, #1a1200 40%, #b88900 100%)",
        color: "#ffcc33", fontWeight: 700
      }}>
        <span>Aurea IA 3.0</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={clearChat} className="btn" style={{ padding: "4px 10px", fontSize: 12 }}>Limpar</button>
          <button onClick={() => setOpen(o => !o)} className="btn" style={{ padding: "4px 10px", fontSize: 12 }}>
            {open ? "Minimizar" : "Abrir"}
          </button>
        </div>
      </header>

      {/* Mini input quando minimizado */}
      {!open && (
        <form
          onSubmit={(e) => { e.preventDefault(); send(); setOpen(true); }}
          style={{ padding: 8, display: "flex", gap: 8, alignItems: "center" }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={busy ? "Consultando IA..." : "Pergunte sobre seu PIX..."}
            disabled={busy}
            style={{ flex: 1, fontSize: 12 }}
          />
          <button type="submit" className="btn" disabled={busy}>
            {busy ? "..." : "Enviar"}
          </button>
        </form>
      )}

      {open ? (
        <>
          <div ref={scrollRef} style={{ flex: 1, padding: 12, overflowY: "auto", background: "#0f0f0f" }}>
            {msgs.map((m, i) => (
              <div key={i} style={{ marginBottom: 10, display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
                <div style={{
                  maxWidth: "88%", padding: "8px 10px", borderRadius: 10,
                  background: m.role === "user" ? "#1f1f1f" : "rgba(255,204,51,.1)",
                  border: m.role === "user" ? "1px solid #2a2a2a" : "1px solid #b88900",
                  color: "#f2f2f2", fontSize: 14, whiteSpace: "pre-wrap"
                }}>
                  {m.text}
                </div>
              </div>
            ))}
          </div>

          <div style={{ padding: "8px 10px", background: "#121212", borderTop: "1px solid #2b2b2b" }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
              <button className="btn" style={{ fontSize: 12, padding: "4px 8px" }} onClick={() => quickAsk("Quanto tenho de saldo PIX agora?")}>Saldo agora</button>
              <button className="btn" style={{ fontSize: 12, padding: "4px 8px" }} onClick={() => quickAsk("Resumo PIX das ultimas 24 horas")}>Ultimas 24h</button>
              <button className="btn" style={{ fontSize: 12, padding: "4px 8px" }} onClick={() => quickAsk("Liste os 5 ultimos PIX")}>5 ultimos</button>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); send(); }} style={{ display: "flex", gap: 8 }}>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={busy ? "Consultando IA..." : "Pergunte sobre seu PIX..."}
                disabled={busy}
                style={{ flex: 1 }}
              />
              <button type="submit" className="btn" disabled={busy}>{busy ? "..." : "Enviar"}</button>
            </form>
          </div>
        </>
      ) : (
        <div style={{ padding: 12, color: "#ccc", fontSize: 13 }}>Painel minimizado.</div>
      )}
    </aside>
  );
}

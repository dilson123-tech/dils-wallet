import React, { useState, useEffect, useRef } from "react";
import { API_BASE, USER_EMAIL } from "../super2/api";

type Message = {
  id: number;
  role: "user" | "ai";
  text: string;
};

export default function AureaAIChatLab() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  // auto-scroll sempre para a última mensagem
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      text: trimmed,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/api/v1/ai/chat_lab`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Email": USER_EMAIL,
        },
        body: JSON.stringify({ message: trimmed }),
      });

      if (!resp.ok) {
        throw new Error("Falha ao falar com a IA 3.0 da Aurea Gold.");
      }

      const data = (await resp.json()) as { reply?: string };

      const rawReply =
        (data.reply ?? "").trim() ||
        "IA 3.0 respondeu, mas não retornou texto utilizável.";

      const aiMsg: Message = {
        id: Date.now() + 1,
        role: "ai",
        text: rawReply,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: any) {
      const msg = e?.message ?? "Erro inesperado ao falar com a IA.";
      setError(msg);
      const aiMsg: Message = {
        id: Date.now() + 2,
        role: "ai",
        text:
          "Tive um problema técnico agora no laboratório. Tente novamente em instantes.",
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setMessages([]);
    setError(null);
  }

  return (
    <section className="mt-4 text-[11px] border border-[#d4af37]/40 rounded-lg px-2 py-2 bg-black/70">
      <div className="super2-section-title mb-1">
        IA 3.0 — Assistente do Cliente (LAB)
      </div>

      <p className="text-[10px] text-zinc-300 mb-2">
        Versão de laboratório da IA 3.0 Premium. Aqui testamos o comportamento
        da IA sem impactar o painel oficial do cliente.
      </p>

      <div
        ref={listRef}
        className="h-32 max-h-40 overflow-y-auto space-y-1 pr-1 mb-2"
      >
        {messages.length === 0 ? (
          <div className="text-[10px] text-zinc-500">
            Envie uma pergunta sobre saldo, entradas, saídas ou PIX para ver a
            IA 3.0 responder em modo de teste.
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={`text-[10px] rounded-md px-2 py-1 ${
                m.role === "user"
                  ? "bg-[#1b1f2a] text-zinc-100 border border-[#d4af37]/30 text-right"
                  : "bg-black text-[#f1f1f1] border border-emerald-500/30 text-left"
              }`}
            >
              <span className="block text-[9px] opacity-60 mb-0.5">
                {m.role === "user" ? "Você" : "IA 3.0 Aurea Gold"}
              </span>
                <div className="whitespace-pre-line">{m.text}</div>
            </div>
          ))
        )}
      </div>

      {error && (
        <div className="mb-2 text-[10px] text-red-400">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-1">
        <input
          className="flex-1 h-7 rounded-md border border-[#d4af37]/40 bg-black/80 px-2 text-[10px] outline-none focus:border-[#d4af37]"
          placeholder="Pergunte algo sobre saldo, entradas, saídas ou PIX..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="h-7 px-2 rounded-md text-[10px] bg-[#1f8b2f] hover:bg-[#26a33a] disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Aguarde..." : "Perguntar"}
        </button>
        <button
          type="button"
          onClick={handleClear}
          disabled={loading || messages.length === 0}
          className="h-7 px-2 rounded-md text-[10px] bg-[#2b2b2b] hover:bg-[#3a3a3a] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Limpar
        </button>
      </form>
    </section>
  );
}

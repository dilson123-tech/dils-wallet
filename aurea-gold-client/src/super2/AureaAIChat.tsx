import React, { useState, useEffect, useRef } from "react";
import { API_BASE, USER_EMAIL } from "./api";

type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  text: string;
};

export default function AureaAIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "assistant",
      text:
        "Olá! Eu sou a IA 3.0 do Aurea Gold. Pergunte sobre seu PIX, saldo ou " +
        "movimentação que eu te explico em linguagem simples.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  // auto-scroll sempre para a última mensagem
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now(),
      role: "user",
      text,
    };

    setInput("");
    setErr(null);
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/api/v1/ai/chat_lab`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Email": USER_EMAIL,
        },
        body: JSON.stringify({ message: text }),
      });

      if (!resp.ok) {
        throw new Error(
          `IA indisponível no momento (código ${resp.status}). Tente novamente em instantes.`
        );
      }

      const data = await resp.json();

      const replyText: string =
        (data.reply ??
          data.answer ??
          data.message ??
          data.text ??
          "Recebi sua pergunta, mas não consegui gerar uma resposta detalhada agora."
        ).toString();

      const aiMsg: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: replyText,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: any) {
      const msg =
        e?.message ||
        "Não consegui falar com a IA agora. Verifique sua conexão ou tente de novo em alguns segundos.";
      setErr(msg);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          role: "assistant",
          text:
            "Tentei responder sua pergunta, mas a IA está indisponível neste momento. " +
            "Por favor, tente novamente em alguns instantes.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setErr(null);
    setInput("");
    // mantém só a primeira mensagem (boas-vindas da IA)
    setMessages((prev) => (prev.length > 0 ? [prev[0]] : []));
  }

  return (
    <section className="mt-4 text-[11px]">
      <div className="super2-section-title mb-1">IA 3.0 — Assistente do Cliente</div>

      <div className="rounded-lg border border-[#d4af37]/30 bg-black/80 px-2 py-2 flex flex-col gap-2">
        {/* Lista de mensagens */}
        <div
          ref={listRef}
          className="h-32 max-h-40 overflow-y-auto pr-1 space-y-1"
        >
          {messages.map((m) => (
            <div
              key={m.id}
              className={`px-2 py-1 rounded-md text-[10px] leading-snug ${
                m.role === "user"
                  ? "bg-[#1f2a00] text-zinc-50 self-end border border-[#d4af37]/50 text-right"
                  : "bg-[#050505] text-zinc-200 border border-[#444]/60 text-left"
              }`}
            >
              <span className="block text-[9px] opacity-60 mb-0.5">
                {m.role === "user" ? "Você" : "IA 3.0 Aurea Gold"}
              </span>
              <span>{m.text}</span>
            </div>
          ))}
        </div>

        {/* Erro, se houver */}
        {err && (
          <div className="text-[10px] text-red-400">
            {err}
          </div>
        )}

        {/* Input + botões */}
        <form onSubmit={handleSend} className="flex gap-1 items-center">
          <input
            className="flex-1 h-7 rounded-md border border-[#333] bg-black/70 px-2 text-[10px] focus:outline-none focus:ring-1 focus:ring-[#d4af37]"
            placeholder="Pergunte algo sobre seu Aurea Gold..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="h-7 px-3 rounded-md border border-[#d4af37]/70 bg-gradient-to-r from-[#3f7b00] to-[#47a51b] text-[10px] disabled:opacity-40 disabled:cursor-not-allowed active:scale-[0.97] transition"
          >
            {loading ? "Enviando..." : "Perguntar"}
          </button>
          <button
            type="button"
            onClick={handleClear}
            disabled={loading || messages.length <= 1}
            className="h-7 px-2 rounded-md border border-[#555]/70 bg-[#111] text-[10px] disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Limpar
          </button>
        </form>
      </div>
    </section>
  );
}

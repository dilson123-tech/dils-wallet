
import React, { useState } from "react";

type QuickAction =
  | "analise_mes"
  | "onde_gasto_mais"
  | "economizar_agora"
  | "previsao_saldo"
  | "risco_mes"
  | "saldo_hoje"
  | "entradas_pix"
  | "saidas_pix"
  | "modo_consultor";

const quickMessages: Record<QuickAction, string> = {
  analise_mes:
    "faça uma análise completa do meu mês no PIX, com foco em gastos e entradas",
  onde_gasto_mais:
    "me diga em que categorias ou dias estou gastando mais no PIX",
  economizar_agora:
    "me mostre ideias práticas para economizar com base no meu histórico PIX",
  previsao_saldo:
    "qual a previsão de saldo no final do mês considerando meu PIX",
  risco_mes:
    "qual o nível de risco do meu mês no PIX, estou gastando demais?",
  saldo_hoje:
    "qual é o saldo de hoje considerando apenas as movimentações de PIX",
  entradas_pix:
    "resuma as entradas do mês no PIX, separando principais fontes",
  saidas_pix:
    "resuma as saídas do mês no PIX, destacando gastos críticos",
  modo_consultor:
    "assuma o modo consultor financeiro IA 3.0 e me oriente sobre meu PIX",
};

export default function ConsultorFinanceiroIAPanelLab() {
  const [message, setMessage] = useState("");
  const [log, setLog] = useState<string[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleQuick(action: QuickAction) {
    const text = quickMessages[action];
    setMessage(text);
    setLog((prev) =>
      [`▶ Pergunta rápida: ${text}`, ...prev].slice(0, 6)
    );
  }

  async function handleSend() {
    if (!message.trim() || loading) return;

    const pergunta = message.trim();

    setLog((prev) =>
      [`✅ Pergunta enviada para IA 3.0 (LAB): ${pergunta}`, ...prev].slice(
        0,
        6,
      )
    );
    setMessage("");
    setError(null);
    setLoading(true);

    try {
      const resp = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          // prefixo deixa claro para o backend que é um modo LAB focado em PIX
          message: "[MODO CONSULTOR PIX LAB] " + pergunta,
        }),
      });

      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }

      const data = await resp.json() as any;

      // tenta pegar campo padrão "reply"; se não tiver, mostra JSON bruto
      const reply =
        typeof data?.reply === "string" ? data.reply : JSON.stringify(data, null, 2);

      setAnswer(reply);
      setLog((prev) =>
        ["💬 Resposta recebida da IA 3.0 (LAB).", ...prev].slice(0, 6)
      );
    } catch (err) {
      console.error(err);
      setError(
        "Erro ao falar com a IA 3.0 (LAB). Confira se o backend está rodando em /api/v1/ai/chat."
      );
      setLog((prev) =>
        ["⚠️ Erro ao consultar IA 3.0 (LAB).", ...prev].slice(0, 6)
      );
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setLog([]);
    setMessage("");
    setAnswer(null);
    setError(null);
  }

  return (
    <section className="mt-6 rounded-2xl border border-amber-500/50 bg-black p-4 md:p-5 space-y-3 shadow-[0_0_30px_rgba(251,191,36,0.15)] text-zinc-100 relative z-20">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.18em]">
            Painel IA 3.0 • Consultor Financeiro (LAB)
          </p>
          <h2 className="mt-1 text-sm md:text-base font-semibold text-amber-100">
            Gerente financeiro IA focado em PIX, entradas, saídas e risco do mês.
          </h2>
          <p className="mt-1 text-[10px] md:text-xs text-zinc-100">
            Versão laboratório — aqui testamos perguntas prontas e fluxo de atendimento
            antes de ligar em definitivo na IA oficial do app.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/60 bg-zinc-950 px-3 py-1 text-[9px] md:text-[10px] text-amber-100">
          <span className="inline-flex h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
          <span>Modo LAB • usando IA 3.0</span>
        </div>
      </div>

      {/* Ações rápidas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] md:text-[11px]">
        <button
          type="button"
          onClick={() => handleQuick("analise_mes")}
          className="rounded-full bg-amber-500 text-black font-medium px-3 py-1 hover:bg-amber-400 transition"
        >
          Análise do mês
        </button>
        <button
          type="button"
          onClick={() => handleQuick("onde_gasto_mais")}
          className="rounded-full bg-amber-500 text-black font-medium px-3 py-1 hover:bg-amber-400 transition"
        >
          Onde gasto mais
        </button>
        <button
          type="button"
          onClick={() => handleQuick("economizar_agora")}
          className="rounded-full bg-amber-500 text-black font-medium px-3 py-1 hover:bg-amber-400 transition"
        >
          Economizar agora
        </button>
        <button
          type="button"
          onClick={() => handleQuick("previsao_saldo")}
          className="rounded-full bg-amber-500 text-black font-medium px-3 py-1 hover:bg-amber-400 transition"
        >
          Previsão de saldo
        </button>
        <button
          type="button"
          onClick={() => handleQuick("risco_mes")}
          className="rounded-full bg-amber-500 text-black font-medium px-3 py-1 hover:bg-amber-400 transition"
        >
          Risco do mês
        </button>
        <button
          type="button"
          onClick={() => handleQuick("saldo_hoje")}
          className="rounded-full bg-amber-500 text-black font-medium px-3 py-1 hover:bg-amber-400 transition"
        >
          Saldo hoje (PIX)
        </button>
        <button
          type="button"
          onClick={() => handleQuick("entradas_pix")}
          className="rounded-full bg-amber-500 text-black font-medium px-3 py-1 hover:bg-amber-400 transition"
        >
          Entradas do mês
        </button>
        <button
          type="button"
          onClick={() => handleQuick("saidas_pix")}
          className="rounded-full bg-amber-500 text-black font-medium px-3 py-1 hover:bg-amber-400 transition"
        >
          Saídas do mês
        </button>
        <button
          type="button"
          onClick={() => handleQuick("modo_consultor")}
          className="col-span-2 md:col-span-4 rounded-full bg-zinc-800 text-amber-100 font-medium px-3 py-1 hover:bg-zinc-700 transition"
        >
          Modo consultor (PIX)
        </button>
      </div>

      {/* Campo de pergunta */}
      <div className="mt-2 space-y-2">
        <label className="block text-[10px] md:text-[11px] text-zinc-100">
          Pergunte algo sobre seu PIX para o consultor IA 3.0 (LAB)
        </label>
        <div className="flex flex-col md:flex-row gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ex.: preciso reduzir meus gastos de PIX nessa semana, por onde começo?"
            className="flex-1 rounded-full bg-zinc-900 border border-zinc-700 px-3 py-2 text-[11px] md:text-xs text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleSend}
              disabled={loading}
              className="rounded-full bg-amber-500 text-black font-semibold px-4 py-2 text-[11px] md:text-xs hover:bg-amber-400 disabled:opacity-60 disabled:cursor-not-allowed transition"
            >
              {loading ? "Perguntando..." : "Perguntar"}
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="rounded-full bg-zinc-800 text-zinc-100 px-3 py-2 text-[11px] md:text-xs hover:bg-zinc-700 transition"
            >
              Limpar
            </button>
          </div>
        </div>
      </div>

      {/* Resposta da IA 3.0 (LAB) */}
      {answer && (
        <div className="mt-3 rounded-2xl border border-amber-500/60 bg-zinc-950/90 p-3 text-[11px] md:text-xs text-zinc-100 space-y-2">
          <p className="text-[10px] uppercase tracking-[0.16em] text-amber-300">
            IA 3.0 • Resposta (LAB)
          </p>
          <p className="whitespace-pre-line">{answer}</p>
        </div>
      )}

      {/* Log pequeno só para feedback visual no LAB */}
      {log.length > 0 && (
        <div className="mt-2 rounded-xl bg-zinc-950/80 border border-zinc-800 p-3 space-y-1 max-h-36 overflow-y-auto text-[10px] md:text-[11px] text-zinc-100">
          {log.map((entry, idx) => (
            <div key={idx}>• {entry}</div>
          ))}
        </div>
      )}

      {/* Erro de comunicação com a IA */}
      {error && (
        <div className="mt-2 text-[10px] md:text-[11px] text-red-400">
          {error}
        </div>
      )}
    </section>
  );
}

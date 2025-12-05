import React, { useState } from "react";
import { API_BASE, USER_EMAIL } from "./api";

/**
 * AureaIAPanel
 *
 * Painel oficial da IA 3.0 dentro do app Aurea Gold.
 * Aqui concentramos:
 *  - visão de consultor financeiro
 *  - atalhos de perguntas
 *  - resposta textual da IA 3.0
 *  - área reservada para o chat completo (fase 2)
 */
export default function AureaIAPanel() {
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);

  async function askIA(message: string) {
    if (loading) return;

    setLoading(true);
    setErr(null);
    setLastQuestion(message);
    setAnswer(null);

    try {
      const resp = await fetch(`${API_BASE}/api/v1/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Email": USER_EMAIL,
        },
        body: JSON.stringify({ message }),
      });

      if (!resp.ok) {
        throw new Error(
          `IA indisponível no momento (código ${resp.status}). Tente novamente em instantes.`
        );
      }

      const data = await resp.json();

      const replyText: string = (
        data.reply ??
        data.answer ??
        data.message ??
        data.text ??
        "Recebi sua pergunta, mas não consegui gerar uma resposta detalhada agora."
      ).toString();

      setAnswer(replyText);
    } catch (e: any) {
      const msg =
        e?.message ||
        "Não consegui falar com a IA agora. Verifique sua conexão ou tente de novo em alguns segundos.";
      setErr(msg);
    } finally {
      setLoading(false);
    }
  }

  function handleQuick(message: string) {
    void askIA(message);
  }

  function handleClear() {
    setLastQuestion(null);
    setAnswer(null);
    setErr(null);
  }

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* HEADER */}
      <header className="mb-4">
        <div className="text-[10px] uppercase tracking-wide text-zinc-400">
          Aurea Gold • IA 3.0 premium
        </div>
        <h1 className="text-lg md:text-xl font-semibold text-amber-300 mt-1">
          IA 3.0 • Consultor financeiro Aurea
        </h1>
        <p className="text-xs text-zinc-400 mt-1 max-w-xl">
          Esta é a área dedicada à inteligência artificial do app Aurea Gold.
          Aqui o cliente fala com a IA, recebe resumos, alertas e recomendações
          sobre a vida financeira.
        </p>
        <div className="h-px w-32 bg-amber-500 mt-3" />
      </header>

      {/* CARDS RESUMO */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
        <div className="rounded-xl border border-amber-500/40 bg-zinc-950/80 p-3">
          <div className="text-[10px] uppercase tracking-wide text-zinc-400 mb-1">
            Resumo do mês
          </div>
          <p className="text-[11px] text-zinc-200">
            A IA 3.0 vai gerar um resumo em linguagem clara sobre entradas,
            saídas e saldo do PIX no mês.
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-emerald-300 mb-1">
            Oportunidades
          </div>
          <p className="text-[11px] text-emerald-100/80">
            Sugestões de economia, reserva e ajustes no fluxo de caixa pessoal
            ou da empresa.
          </p>
        </div>

        <div className="rounded-xl border border-sky-500/40 bg-sky-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-sky-300 mb-1">
            Alertas
          </div>
          <p className="text-[11px] text-sky-100/80">
            Alertas de risco de atrasos, concentração de gastos e comportamentos
            fora do padrão.
          </p>
        </div>
      </section>

      {/* ATALHOS DE PERGUNTAS */}
      <section className="mb-4">
        <h2 className="text-[11px] uppercase tracking-wide text-zinc-400 mb-2">
          Atalhos de conversa com a IA
        </h2>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleQuick("resumo do mes no pix")}
            className="px-3 py-2 rounded-full bg-amber-500 text-black text-[11px] font-semibold uppercase tracking-wide disabled:opacity-60 disabled:cursor-not-allowed"
            disabled={loading}
          >
            Analisar meu mês
          </button>
          <button
            type="button"
            onClick={() =>
              handleQuick("tenho risco de atrasar alguma conta?")
            }
            className="px-3 py-2 rounded-full border border-amber-500/60 text-amber-300 text-[11px] uppercase tracking-wide disabled:opacity-60 disabled:cursor-not-allowed"
            disabled={loading}
          >
            Tenho risco de atrasar contas?
          </button>
          <button
            type="button"
            onClick={() =>
              handleQuick("onde estou gastando mais no pix este mes?")
            }
            className="px-3 py-2 rounded-full border border-zinc-700 text-zinc-200 text-[11px] uppercase tracking-wide disabled:opacity-60 disabled:cursor-not-allowed"
            disabled={loading}
          >
            Onde estou gastando mais?
          </button>
          <button
            type="button"
            onClick={() =>
              handleQuick(
                "monte um plano de acao para melhorar minhas financas baseado nos meus movimentos de pix"
              )
            }
            className="px-3 py-2 rounded-full border border-zinc-700 text-zinc-200 text-[11px] uppercase tracking-wide disabled:opacity-60 disabled:cursor-not-allowed"
            disabled={loading}
          >
            Sugerir um plano de ação
          </button>
        </div>
      </section>

      {/* RESPOSTA DA IA 3.0 */}
      <section className="mb-4 rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
        <div className="text-[11px] font-semibold text-zinc-200 mb-1 flex items-center justify-between gap-2">
          <span>Resposta da IA 3.0</span>
          <div className="flex items-center gap-2">
            {loading && (
              <span className="text-[10px] text-amber-300">
                Pensando na sua situação...
              </span>
            )}
            <button
              type="button"
              onClick={handleClear}
              className="px-2 py-1 rounded-full border border-zinc-600 text-[9px] uppercase tracking-wide text-zinc-300 hover:border-amber-400 hover:text-amber-300 active:scale-[0.97] transition disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              Limpar
            </button>
          </div>
        </div>

        {lastQuestion && (
          <p className="text-[10px] text-zinc-400 mb-2">
            <span className="font-semibold text-zinc-200">
              Pergunta enviada:{" "}
            </span>
            {lastQuestion}
          </p>
        )}

        {err && (
          <p className="text-[10px] text-red-400 mb-2">
            {err}
          </p>
        )}

        <div className="min-h-[72px] rounded-lg border border-dashed border-zinc-700 bg-black/40 px-2 py-2 text-[11px] text-zinc-200 whitespace-pre-line">
          {answer
            ? answer
            : "Clique em um dos atalhos acima para ver aqui a resposta da IA 3.0 sobre sua vida financeira no Aurea Gold."}
        </div>
      </section>

      {/* BLOCO CHAT / FUTURA INTEGRAÇÃO */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
        <div className="text-[11px] font-semibold text-zinc-200 mb-1">
          Chat de IA 3.0 (em breve)
        </div>
        <p className="text-[11px] text-zinc-400 mb-2">
          Aqui vamos integrar o chat completo da IA 3.0 da Aurea Gold, com
          contexto financeiro do usuário e histórico de PIX.
        </p>
        <div className="h-20 rounded-lg border border-dashed border-zinc-700 bg-black/40 flex items-center justify-center text-[11px] text-zinc-500">
          Área reservada para o chat da IA 3.0.
        </div>
      </section>
    </div>
  );
}

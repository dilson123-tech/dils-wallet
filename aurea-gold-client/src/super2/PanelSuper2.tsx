import React, { useEffect, useState } from "react";
import {
  fetchPixBalance,
  fetchPixHistory,
  PixBalancePayload,
  PixHistoryDay,
} from "./api";
import AureaPixSendModal from "./AureaPixSendModal";
import ChartSuper2 from "./ChartSuper2";
import AureaAIChat from "./AureaAIChat";

function fmtBRL(v: number | undefined | null): string {
  const n = typeof v === "number" && !Number.isNaN(v) ? v : 0;
  return (
    "R$ " +
    n
      .toFixed(2)
      .replace(".", ",")
  );
}

export default function PanelSuper2() {
  const [balance, setBalance] = useState<PixBalancePayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [showSendModal, setShowSendModal] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  async function load() {
    try {
      setLoading(true);
      setErr(null);
      const b = await fetchPixBalance();
      setBalance(b);
    } catch (e: any) {
      setErr(e?.message ?? "Falha ao carregar dados do PIX.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const saldo = balance?.saldo_atual ?? 0;
  const entradasMes = (balance as any)?.entradas_mes ?? 0;
  const saidasMes = (balance as any)?.saidas_mes ?? 0;

  function handlePixSent() {
    setShowSendModal(false);
    load();
  }

  async function handleShowHistory() {
    try {
      setErr(null);
      const hist = await fetchPixHistory();
      console.log("SUPER2 history raw =>", hist);

      const arr = Array.isArray((hist as any)?.dias)
        ? (hist as any).dias
        : Array.isArray(hist as any)
        ? (hist as any)
        : Array.isArray((hist as any)?.history)
        ? (hist as any).history
        : [];

      setHistory(arr);
      setShowHistory((prev) => !prev);
    } catch (e: any) {
      setErr(e?.message ?? "Falha ao carregar histórico PIX.");
    }
  }

    function handleClear() {
    // limpar histórico e mensagens de erro locais do painel Super2
    setShowHistory(false);
    setErr(null);
    setHistory([]);
    console.log("Super2: estado local limpo (histórico/erros).");
  }

  return (
    <div className="aurea-super2 min-h-screen flex items-start justify-center pt-10 pb-20 bg-black text-[#f5f5f5]">
      <main className="aurea-panel w-[360px] max-w-full rounded-2xl border border-[#d4af37]/40 bg-black/80 backdrop-blur-xl px-4 pb-4 pt-3">
        <header className="mb-2">
          <div className="text-sm font-semibold tracking-wide text-[#d4af37] drop-shadow-[0_0_4px_#d4af37]">
            AUREA GOLD • PREMIUM
          </div>
          <div className="text-[10px] opacity-70">v1.0 beta • Super2</div>
        </header>

        {err && (
          <div className="mt-1 text-[11px] text-red-400">
            {err}
          </div>
        )}

        {loading && (
          <div className="mt-1 text-[11px] text-[#d4af37]">
            Carregando dados do PIX...
          </div>
        )}

        {/* Bloco de saldos */}
        <section className="mt-3 text-[11px] space-y-1 border border-[#d4af37]/30 rounded-lg px-2 py-2">
          <div className="flex justify-between">
            <span>Saldo</span>
            <span className="font-semibold">{fmtBRL(saldo)}</span>
          </div>
          <div className="flex justify-between">
            <span>Entradas (Mês)</span>
            <span className="font-semibold">{fmtBRL(entradasMes)}</span>
          </div>
          <div className="flex justify-between">
            <span>Saídas (Mês)</span>
            <span className="font-semibold">{fmtBRL(saidasMes)}</span>
          </div>
        </section>

        {/* Resumo / gráfico últimos 7 dias */}
        <section className="mt-4">
          <div className="super2-section-title mb-1">
            Resumo — últimos 7 dias
          </div>
          <ChartSuper2 />
        </section>

        {/* Ações rápidas */}
        <section className="mt-4">
          <div className="super2-section-title mb-1">
            Ações rápidas
          </div>
          <div className="flex flex-col gap-2">
            <button
              className="h-8 rounded-md border border-[#d4af37]/60 bg-gradient-to-r from-[#228000] to-[#21a020] text-[11px] hover:from-[#217f00] hover:to-[#41b500] active:scale-[0.98] transition"
              onClick={() => setShowSendModal(true)}
            >
              Enviar PIX
            </button>

            <button
              className="h-8 rounded-md border border-[#d4af37]/60 bg-gradient-to-r from-[#171900] to-[#181200] text-[11px] hover:from-[#271700] hover:to-[#413b00] active:scale-[0.98] transition"
              onClick={handleShowHistory}
            >
              Histórico
            </button>

            <button
              className="h-8 rounded-md border border-[#d4af37]/60 bg-gradient-to-r from-[#171900] to-[#181200] text-[11px] hover:from-[#271700] hover:to-[#413b00] active:scale-[0.98] transition"
              onClick={handleClear}
            >
              Limpar
            </button>
          </div>
        </section>

        {/* Histórico diário (entradas/saídas) */}
        {showHistory && (
          <section className="mt-4 text-[11px]">
            <div className="super2-section-title mb-1">
              Histórico recente (resumo diário)
            </div>
            {history.length === 0 ? (
              <div className="text-[10px] text-zinc-400">
                Nenhum dado de PIX encontrado para este usuário.
              </div>
            ) : (
              <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
                {history.map((d: any) => {
                  const label = new Date(
                    `${d.dia}T00:00:00`
                  ).toLocaleDateString("pt-BR", {
                    day: "2-digit",
                    month: "2-digit",
                  });
                  const net = (d.entradas || 0) - (d.saidas || 0);
                  return (
                    <div
                      key={d.dia}
                      className="flex items-center justify-between rounded-md border border-[#d4af37]/30 bg-black/70 px-2 py-1"
                    >
                      <div className="flex flex-col">
                        <span className="text-[10px] opacity-70">
                          {label}
                        </span>
                        <span className="text-[10px] text-zinc-300">
                          Entradas: {fmtBRL(d.entradas)} • Saídas:{" "}
                          {fmtBRL(d.saidas)}
                        </span>
                      </div>
                      <div
                        className={`text-[11px] font-semibold ${
                          net >= 0 ? "text-emerald-400" : "text-red-400"
                        }`}
                      >
                        {fmtBRL(net)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        )}

        <AureaAIChat />

          <footer className="mt-4 flex justify-end">
          <span className="text-[9px] px-2 py-0.5 rounded-full border border-[#d4af37]/60 bg-black/60 text-[#d4af37]">
            SUPER2 • mobile
          </span>
        </footer>

        <AureaPixSendModal
          open={showSendModal}
          onClose={() => setShowSendModal(false)}
          onSent={handlePixSent}
        />
      </main>
    </div>
  );
}

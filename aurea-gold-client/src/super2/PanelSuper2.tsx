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
  const [history, setHistory] = useState<PixHistoryDay[]>([]);
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
        ? ((hist as any).dias as PixHistoryDay[])
        : Array.isArray(hist as any)
        ? (hist as PixHistoryDay[])
        : Array.isArray((hist as any)?.history)
        ? ((hist as any).history as PixHistoryDay[])
        : [];

      setHistory(arr);
      setShowHistory((prev) => !prev);
    } catch (e: any) {
      setErr(e?.message ?? "Falha ao carregar histórico PIX.");
    }
  }

  function handleClear() {
    setShowHistory(false);
    setErr(null);
    setHistory([]);
    console.log("Super2: estado local limpo (histórico/erros).");
  }

  return (
    <div className="aurea-super2 min-h-screen flex justify-center items-start bg-[#020617] text-[#f5f5f5] px-2 py-6 sm:py-10">
      <main className="aurea-panel w-full max-w-sm rounded-2xl border border-[#d4af37]/40 bg-black/80 backdrop-blur-xl px-4 pb-4 pt-3 shadow-[0_0_35px_rgba(0,0,0,0.95)]">
        <header className="mb-3 flex items-center justify-between gap-2">
          <div>
            <div className="text-sm font-semibold tracking-wide text-[#d4af37] drop-shadow-[0_0_4px_#d4af37]">
              AUREA GOLD • PREMIUM
            </div>
            <div className="text-[10px] opacity-70">
              Carteira PIX • painel Super2
            </div>
          </div>
          <span className="text-[9px] px-2 py-0.5 rounded-full border border-[#d4af37]/60 bg-black/70 text-[#facc15]">
            v1.0 BETA
          </span>
        </header>

        {err && <div className="mt-1 text-[11px] text-red-400">{err}</div>}

        {loading && (
          <div className="mt-1 text-[11px] text-[#d4af37]">
            Carregando dados do PIX...
          </div>
        )}

        {/* Bloco de saldos */}
        <section className="mt-3 text-[11px] space-y-2 rounded-xl border border-[#d4af37]/40 bg-black/70 px-3 py-3 shadow-[0_0_16px_rgba(0,0,0,0.7)]">
          <div className="flex items-baseline justify-between">
            <div className="flex flex-col">
              <span className="text-[10px] opacity-70">Saldo disponível</span>
              <span className="text-[13px] font-semibold text-[#facc15]">
                {fmtBRL(saldo)}
              </span>
            </div>
            <span className="text-[9px] px-2 py-0.5 rounded-full border border-[#facc15]/40 text-[#facc15]">
              Carteira PIX
            </span>
          </div>

          <div className="h-px bg-gradient-to-r from-transparent via-[#d4af37]/40 to-transparent" />

          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div className="rounded-md border border-[#d4af37]/20 bg-black/60 px-2 py-1.5">
              <div className="opacity-70">Entradas (Mês)</div>
              <div className="font-semibold">{fmtBRL(entradasMes)}</div>
            </div>
            <div className="rounded-md border border-[#d4af37]/20 bg-black/60 px-2 py-1.5">
              <div className="opacity-70">Saídas (Mês)</div>
              <div className="font-semibold">{fmtBRL(saidasMes)}</div>
            </div>
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
          <div className="super2-section-title mb-1 flex items-center justify-between">
            <span>Ações rápidas</span>
            <span className="text-[9px] text-zinc-400">PIX do dia a dia</span>
          </div>

          <div className="rounded-xl border border-[#d4af37]/35 bg-black/70 px-2 py-2 shadow-[0_0_12px_rgba(0,0,0,0.6)] space-y-2">
            <button
              className="h-8 w-full rounded-md border border-[#d4af37]/70 bg-gradient-to-r from-[#228000] to-[#21a020] text-[11px] font-semibold hover:from-[#217f00] hover:to-[#41b500] active:scale-[0.98] transition"
              onClick={() => setShowSendModal(true)}
            >
              Enviar PIX
            </button>

            <button
              className="h-8 w-full rounded-md border border-[#d4af37]/60 bg-gradient-to-r from-[#171900] to-[#181200] text-[11px] hover:from-[#271700] hover:to-[#413b00] active:scale-[0.98] transition"
              onClick={handleShowHistory}
            >
              Ver histórico diário
            </button>

            <button
              className="h-8 w-full rounded-md border border-[#d4af37]/40 bg-black/80 text-[11px] hover:border-[#d4af37]/80 active:scale-[0.98] transition"
              onClick={handleClear}
            >
              Limpar painel
            </button>
          </div>
        </section>

        {/* Histórico diário (entradas/saídas) */}
        {showHistory && (
          <section className="mt-4 text-[11px]">
            <div className="rounded-lg border border-[#d4af37]/35 bg-black/80 px-2 py-2 space-y-2 shadow-[0_0_14px_rgba(0,0,0,0.85)]">
              <div className="flex items-center justify-between">
                <div className="super2-section-title">Histórico recente</div>
                <span className="text-[9px] px-2 py-0.5 rounded-full border border-[#d4af37]/60 bg-black/60 text-[#d4af37]">
                  últimos dias de PIX
                </span>
              </div>
              {history.length === 0 ? (
                <div className="text-[10px] text-zinc-400">
                  Nenhum dado de PIX encontrado para este usuário.
                </div>
              ) : (
                <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                  {history.map((d) => {
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
            </div>
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

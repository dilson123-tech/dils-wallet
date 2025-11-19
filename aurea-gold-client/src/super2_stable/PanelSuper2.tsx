import AureaAISummary from "./AureaAISummary";
import React, { useEffect, useState } from "react";
import { fetchPixBalance, PixBalancePayload } from "./api";

function fmtBRL(v: number | undefined): string {
  const n = typeof v === "number" && !Number.isNaN(v) ? v : 0;
  return (
    "R$ " +
    n
      .toFixed(2)
      .replace(".", ",")
  );
}

export default function PanelSuper2() {
  const [data, setData] = useState<PixBalancePayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        setLoading(true);
        setErr(null);
        const j = await fetchPixBalance();
        if (!alive) return;
        setData(j);
      } catch (e: any) {
        if (!alive) return;
        setErr(e?.message ?? "Falha ao carregar dados");
      } finally {
        if (alive) setLoading(false);
      }
    }

    load();
    return () => {
      alive = false;
    };
  }, []);

  const saldo = data?.saldo_atual;
  const entradasMes = data?.entradas_mes;
  const saidasMes = data?.saidas_mes;

  return (
    <div className="aurea-wrap min-h-screen flex items-start justify-center pt-10 pb-28 bg-gradient-to-b from-black via-[#0d0d0d] to-black">
      <main
        className="aurea-panel w-[360px] max-w-full rounded-2xl border border-[#d4af37]/40 bg-[#000000d0] backdrop-blur-xl text-[#f5f5f5] shadow-[0_0_25px_#d4af3720] px-5 py-5"
        role="region"
        aria-label="Aurea Gold / Painel PIX"
      >
        <header className="mb-4">
          <h1 className="text-sm font-bold tracking-wide text-[#d4af37] drop-shadow-[0_0_4px_#d4af37]">
            AUREA GOLD • PREMIUM{" "}
            <span className="text-[10px] font-normal opacity-70 align-middle">
              v1.0 beta
            </span>
          </h1>

          {err && (
            <p className="mt-1 text-[11px] text-red-400">
              ⚠ {err}
            </p>
          )}

          {loading && !err && (
            <p className="mt-1 text-[11px] text-[#d4af37]">
              Carregando dados do PIX…
            </p>
          )}
        </header>

        <section className="text-[11px] space-y-1 mb-4">
          <div className="flex justify-between border-b border-[#2b2b2b] pb-1 hover:border-[#d4af37]/40 transition">
            <span>Saldo</span>
            <span className="font-semibold">{fmtBRL(saldo)}</span>
          </div>

          <div className="flex justify-between border-b border-[#2b2b2b] pb-1 hover:border-[#d4af37]/40 transition">
            <span>Entradas (Mês)</span>
            <span className="font-semibold">{fmtBRL(entradasMes)}</span>
          </div>

          <div className="flex justify-between border-b border-[#2b2b2b] pb-1 hover:border-[#d4af37]/40 transition">
            <span>Saídas (Mês)</span>
            <span className="font-semibold">{fmtBRL(saidasMes)}</span>
          </div>

          <div className="pt-2">
            <div className="text-[10px] uppercase tracking-wide opacity-70">
              Resumo — últimos 7 dias
            </div>
            <div className="text-[11px] opacity-60">
              Gráfico — plugaremos /api/v1/ai/summary
            </div>
          </div>
        </section>

        <section className="mt-2">
          <div className="text-[10px] uppercase tracking-wide opacity-70 mb-1">
        <AureaAISummary />

            Ações rápidas
          </div>
          <div className="flex flex-col gap-2">
            <button className="h-8 rounded-md border border-[#d4af37]/70 bg-gradient-to-r from-[#3b2b00] to-[#2a2100] text-[11px] font-semibold hover:from-[#4a3600] hover:to-[#332600] active:scale-[0.98] transition">
              Enviar PIX
            </button>
            <button className="h-8 rounded-md border border-[#d4af37]/60 bg-gradient-to-r from-[#282000] to-[#201a00] text-[11px] hover:from-[#332600] hover:to-[#241d00] active:scale-[0.98] transition">
              Histórico
            </button>
            <button className="h-8 rounded-md border border-[#d4af37]/50 bg-gradient-to-r from-[#1f1900] to-[#181200] text-[11px] hover:from-[#271f00] hover:to-[#1b1500] active:scale-[0.98] transition">
              Limpar
            </button>
          </div>
        </section>

        <footer className="mt-4 flex justify-end">
          <span className="text-[9px] px-2 py-0.5 rounded-full border border-[#d4af37]/60 bg-black/60 text-[#d4af37]/90">
            SUPER2 • mobile
          </span>
        </footer>
      </main>
    </div>
  );
}

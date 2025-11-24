import React, { useEffect, useState } from "react";
import { fetchPixHistory, PixHistoryDay } from "./api";

export default function Super2HistoryLab() {
  const [data, setData] = useState<PixHistoryDay[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setErr(null);
      const dias = await fetchPixHistory();
      setData(dias);
    } catch (e: any) {
      setErr(e?.message ?? "Falha ao carregar histórico.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="min-h-screen bg-black text-[#f5f5f5] flex items-start justify-center pt-10 pb-20">
      <main className="w-[360px] max-w-full rounded-2xl border border-[#d4af37]/40 bg-black/80 backdrop-blur-xl px-4 pb-4 pt-3">
        <header className="mb-2">
          <div className="text-sm font-semibold tracking-wide text-[#d4af37] drop-shadow-[0_0_4px_#d4af37]">
            AUREA GOLD • LAB
          </div>
          <div className="text-[10px] opacity-70">
            Super2 — Histórico (LAB)
          </div>
        </header>

        <button
          onClick={load}
          className="mb-3 h-8 rounded-md border border-[#d4af37]/60 bg-gradient-to-r from-[#171900] to-[#181200] text-[11px] hover:from-[#271700] hover:to-[#413b00] active:scale-[0.98] transition"
        >
          Recarregar histórico
        </button>

        {err && (
          <div className="mb-2 text-[11px] text-red-400">
            {err}
          </div>
        )}

        {loading && (
          <div className="mb-2 text-[11px] text-[#d4af37]">
            Carregando histórico...
          </div>
        )}

        <section className="mt-1 text-[11px]">
          <div className="super2-section-title mb-1">
            Histórico diário (resumo)
          </div>

          {data.length === 0 ? (
            <div className="text-[10px] text-zinc-400">
              Nenhum dado retornado pela API.
            </div>
          ) : (
            <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
              {data.map((d) => {
                const label = new Date(`${d.dia}T00:00:00`).toLocaleDateString(
                  "pt-BR",
                  { day: "2-digit", month: "2-digit" }
                );
                const net = d.entradas - d.saidas;
                return (
                  <div
                    key={d.dia}
                    className="flex items-center justify-between rounded-md border border-[#d4af37]/30 bg-black/70 px-2 py-1"
                  >
                    <div className="flex flex-col">
                      <span className="text-[10px] opacity-70">{label}</span>
                      <span className="text-[10px] text-zinc-300">
                        Entradas: R$ {d.entradas.toFixed(2).replace(".", ",")} • Saídas: R${" "}
                        {d.saidas.toFixed(2).replace(".", ",")}
                      </span>
                    </div>
                    <div
                      className={`text-[11px] font-semibold ${
                        net >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      R$ {net.toFixed(2).replace(".", ",")}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

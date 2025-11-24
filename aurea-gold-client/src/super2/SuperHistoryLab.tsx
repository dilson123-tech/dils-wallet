import React, { useEffect, useState } from "react";
import {
  fetchPixBalance,
  fetchPixHistory,
  PixDayPoint,
} from "./api";

// Lab isolado para testar histórico do PIX (Super2)
export default function SuperHistoryLab() {
  const [dias, setDias] = useState<PixDayPoint[]>([]);
  // aqui usamos any mesmo, só para o lab não depender de tipo exportado
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      setErr(null);

      // usa MESMA API do painel Super2
      const [balance, hist] = await Promise.all([
        fetchPixBalance(),
        fetchPixHistory(), // sem parâmetro, assinatura atual da função
      ]);
      console.log("LAB balance raw =>", balance);
      console.log("LAB history raw =>", hist);

      setDias(balance.ultimos_7d || []);
      // normaliza histórico (API pode vir como array OU objeto {dias/history/items/results})
        const arr = Array.isArray(hist?.history)
          ? hist.history
          : Array.isArray(hist?.dias)
          ? hist.dias
          : Array.isArray(hist)
          ? hist
          : Array.isArray(hist?.items)
          ? hist.items
          : Array.isArray(hist?.results)
          ? hist.results
          : [];
        setHistory(arr);
    } catch (e: any) {
      setErr(e?.message ?? "Falha ao carregar histórico.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);


  const rows = Array.isArray(history) ? history : [];


  return (
    <div className="min-h-screen bg-black text-[#f5f5f5] flex flex-col items-center pt-6 px-3">
      <div className="text-sm font-semibold text-[#d4af37] mb-2">
        <div className="mb-2 text-[10px] text-zinc-400">
          debug: dias={dias.length} | rows={rows.length} | historyType={Array.isArray(history) ? "array" : typeof history}
        </div>

        SUPER2 • LAB de histórico
      </div>

      <button
        onClick={load}
        className="mb-3 px-3 py-1.5 rounded-md border border-[#d4af37]/70 bg-black/40 text-[11px] hover:bg-black/70 active:scale-[0.98]"
      >
        Recarregar histórico
      </button>

      {err && (
        <div className="mb-2 text-[11px] text-red-400">
          Erro ao carregar: {err}
        </div>
      )}

      {loading && (
        <div className="mb-2 text-[11px] text-[#d4af37]">
          Carregando dados do PIX...
        </div>
      )}

      {/* Resumo diário (entradas/saídas) */}
      <section className="w-full max-w-md mb-4 text-[11px]">
        <div className="mb-1 text-[#d4af37]">Resumo diário (últimos 7 dias)</div>

        {dias.length === 0 ? (
          <div className="text-[10px] text-zinc-400">
            Nenhum dado retornado pela API.
          </div>
        ) : (
          <div className="space-y-1">
            {dias.map((d) => {
              const label = new Date(d.dia + "T00:00:00").toLocaleDateString(
                "pt-BR",
                { day: "2-digit", month: "2-digit" }
              );
              return (
                <div
                  key={d.dia}
                  className="flex items-center justify-between rounded-md border border-[#d4af37]/30 bg-black/70 px-2 py-1"
                >
                  <div className="flex flex-col">
                    <span className="text-[10px] opacity-70">{label}</span>
                    <span className="text-[10px]">
                      Entradas: R$ {d.entradas.toFixed(2).replace(".", ",")}
                    </span>
                    <span className="text-[10px]">
                      Saídas: R$ {d.saidas.toFixed(2).replace(".", ",")}
                    </span>
                  </div>
                  <div className="text-[11px] font-semibold">
                    R$ {(d.entradas - d.saidas).toFixed(2).replace(".", ",")}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Histórico de registros (tabela simples) */}
      <section className="w-full max-w-md text-[11px]">
        <div className="mb-1 text-[#d4af37]">Histórico recente de PIX</div>

        {rows.length === 0 ? (
          <div className="text-[10px] text-zinc-400">
            Nenhum PIX encontrado para este usuário.
          </div>
        ) : (
          <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
            {rows.map((h: any, idx: number) => {
                const isDia = typeof h?.dia === "string" && typeof h?.entradas === "number";
                if (isDia) {
                  const label = new Date(h.dia + "T00:00:00").toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
                  const net = (h.entradas || 0) - (h.saidas || 0);
                  return (
                    <div
                      key={h.dia || idx}
                      className="flex items-center justify-between rounded-md border border-[#d4af37]/30 bg-black/70 px-2 py-1"
                    >
                      <div className="flex flex-col">
                        <span className="text-[10px] opacity-70">{label}</span>
                        <span className="text-[10px]">Entradas: R$ {h.entradas.toFixed(2).replace(".", ",")}</span>
                        <span className="text-[10px]">Saídas: R$ {h.saidas.toFixed(2).replace(".", ",")}</span>
                      </div>
                      <div className={`text-[11px] font-semibold ${net >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        R$ {net.toFixed(2).replace(".", ",")}
                      </div>
                    </div>
                  );
                }

                // fallback antigo (quando vier transações cruas)
                return (
                  <div
                    key={h.id || idx}
                    className="flex items-center justify-between rounded-md border border-[#d4af37]/30 bg-black/70 px-2 py-1"
                  >
                    <div className="flex flex-col">
                      <span className="text-[10px] opacity-70">
                        {h.tipo === "envio" ? "Enviado" : "Recebido"}
                      </span>
                      {h.descricao && (
                        <span className="text-[10px] text-zinc-300 max-w-[180px] truncate">
                          {h.descricao}
                        </span>
                      )}
                    </div>
                    <div
                      className={`text-[11px] font-semibold ${
                        h.tipo === "envio" ? "text-red-400" : "text-emerald-400"
                      }`}
                    >
                      {`${h.tipo === "envio" ? "-" : "+"} R$ ${Number(h.valor || 0)
                        .toFixed(2)
                        .replace(".", ",")}`}
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </section>
    </div>
  );
}

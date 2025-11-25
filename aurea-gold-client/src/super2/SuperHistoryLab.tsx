import React, { useState } from "react";
import { fetchPixHistory, sendPix } from "./api";

type PixHistoryAny = any;

export default function SuperHistoryLab() {
  const [history, setHistory] = useState<PixHistoryAny[]>([]);
  const [status, setStatus] = useState<string>("Aguardando ação...");
  const [sending, setSending] = useState(false);
  const [loadingHist, setLoadingHist] = useState(false);

  async function reloadHistory() {
    try {
      setLoadingHist(true);
      setStatus("Carregando histórico via /api/v1/pix/history...");
      const hist: any = await fetchPixHistory();
      console.log("LAB history raw =>", hist);

      const arr = Array.isArray(hist)
        ? hist
        : Array.isArray(hist?.dias)
        ? hist.dias
        : Array.isArray(hist?.history)
        ? hist.history
        : Array.isArray(hist?.items)
        ? hist.items
        : Array.isArray(hist?.results)
        ? hist.results
        : [];

      setHistory(arr);
      setStatus(`Histórico normalizado com ${arr.length} registros.`);
    } catch (e: any) {
      console.error(e);
      setStatus(`Erro ao carregar histórico: ${e?.message ?? String(e)}`);
    } finally {
      setLoadingHist(false);
    }
  }

  async function doTestSend() {
    try {
      setSending(true);
      setStatus("Enviando PIX de teste (LAB) R$ 1,23...");
      const resp = await sendPix({
        dest: "dilsonpereira231@gmail.com",
        valor: 1.23,
        descricao: "LAB Super2",
      });
      console.log("LAB sendPix resp =>", resp);
      setStatus(
        resp && (resp as any).ok
          ? `PIX de teste OK, id ${(resp as any).tx?.id ?? "?"}.`
          : "Resposta recebida, ver console."
      );
    } catch (e: any) {
      console.error(e);
      setStatus(`Erro no sendPix (LAB): ${e?.message ?? String(e)}`);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="min-h-screen bg-black text-[#f5f5f5] flex flex-col items-center pt-6 px-3">
      <div className="text-sm font-semibold text-[#d4af37] mb-2">
        Super2 LAB • PIX
      </div>

      <div className="flex gap-2 mb-3">
        <button
          onClick={reloadHistory}
          className="px-3 py-1 rounded-md bg-zinc-900 border border-[#d4af37]/60 text-[11px] hover:bg-zinc-800 disabled:opacity-60"
          disabled={loadingHist}
        >
          {loadingHist ? "Carregando histórico..." : "Recarregar histórico"}
        </button>
        <button
          onClick={doTestSend}
          className="px-3 py-1 rounded-md bg-emerald-600 border border-emerald-400 text-[11px] hover:bg-emerald-500 disabled:opacity-60"
          disabled={sending}
        >
          {sending ? "Enviando..." : "Enviar PIX teste"}
        </button>
      </div>

      <div className="text-[11px] text-zinc-300 mb-3 max-w-md text-center whitespace-pre-wrap">
        {status}
      </div>

      <div className="w-full max-w-md border border-zinc-700 rounded-md bg-zinc-950/70 p-2 text-[10px] leading-tight overflow-auto max-h-[60vh]">
        {history.length === 0 ? (
          <div className="text-zinc-500">
            Nenhum registro em memória. Clique em &quot;Recarregar histórico&quot;.
          </div>
        ) : (
          <pre>{JSON.stringify(history.slice(0, 20), null, 2)}</pre>
        )}
      </div>
    </div>
  );
}

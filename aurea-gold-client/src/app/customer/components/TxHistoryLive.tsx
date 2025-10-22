import React, { useEffect, useRef, useState } from "react";
import { apiGet } from "@/lib/api";
import { formatBRL } from "@/lib/money";

type Tx = { id?: string; ts?: string; type?: string; description?: string; amount?: number };

export default function TxHistoryLive(){
  const [items, setItems] = useState<Tx[]>([]);
  const timer = useRef<number | null>(null);
  const backoff = useRef<number>(30000);
  const alive = () => document.visibilityState === "visible";

  async function fetchHistory(){
    const r = await apiGet("/api/v1/pix/history?limit=10");
    const j = await r.json();
    setItems(Array.isArray(j) ? j : (j?.items ?? []));
  }

  useEffect(() => {
    fetchHistory();

    function onPix(){ fetchHistory(); }
    function onLogin(){ backoff.current = 30000; fetchHistory(); }
    window.addEventListener("pix:updated", onPix);
    window.addEventListener("auth:login", onLogin);

    async function tick(){
      try{
        if (alive()) await fetchHistory();
        backoff.current = 30000;
      }catch{
        backoff.current = Math.min(backoff.current * 2, 5 * 60_000);
      }finally{
        timer.current = window.setTimeout(tick, backoff.current) as any;
      }
    }
    timer.current = window.setTimeout(tick, backoff.current) as any;

    return () => {
      window.removeEventListener("pix:updated", onPix);
      window.removeEventListener("auth:login", onLogin);
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, []);

  return (
    <div className="p-4 md:p-6 rounded-2xl mt-6" style={{background:"linear-gradient(180deg,#1A1A1A,#0E0E0E)"}}>
      <h3 className="text-xl font-semibold text-white mb-4">Transações</h3>
      <div className="divide-y divide-gray-800">
        {items.length === 0 && (
          <div className="text-gray-400 text-sm py-4">Sem movimento recente.</div>
        )}
        {items.map((tx, i) => (
          <div key={tx.id || i} className="py-3 flex items-center justify-between">
            <div className="text-gray-300">
              <div className="text-sm">{tx.description || tx.type || "PIX"}</div>
              <div className="text-xs text-gray-500">{tx.ts ? new Date(tx.ts).toLocaleString("pt-BR") : ""}</div>
            </div>
            <div className={`text-sm font-semibold ${((tx.amount ?? 0) >= 0) ? "text-green-400" : "text-red-400"}`}>
              {formatBRL(tx.amount ?? 0)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import React, { useEffect, useRef, useState } from "react";
import { apiGet } from "@/lib/api";
import { formatBRL } from "@/lib/money";

export default function BalanceLive(){
  const [balance, setBalance] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string>("");

  const timer = useRef<number | null>(null);
  const backoff = useRef<number>(30000); // 30s
  const alive = () => document.visibilityState === "visible";

  async function fetchBalance(){
    const r = await apiGet("/balance","dilsonpereira231@gmail.com");
    const j = await r.json();
    setBalance(j?.balance ?? 0);
  }

  useEffect(() => {
    let closed = false;

    async function boot(){
      try{
        setLoading(true);
        await fetchBalance();
      }catch(e:any){
        if (!closed) setErr(e?.message ?? "Erro ao carregar saldo");
      }finally{
        if (!closed) setLoading(false);
      }
    }
    boot();

    function onPix(){ fetchBalance(); }
    function onLogin(){ backoff.current = 30000; fetchBalance(); }

    window.addEventListener("pix:updated", onPix);
    window.addEventListener("auth:login", onLogin);

    async function tick(){
      try{
        if (alive()) await fetchBalance();
        backoff.current = 30000;
      }catch{
        backoff.current = Math.min(backoff.current * 2, 5 * 60_000);
      }finally{
        timer.current = window.setTimeout(tick, backoff.current) as any;
      }
    }
    timer.current = window.setTimeout(tick, backoff.current) as any;

    return () => {
      closed = true;
      window.removeEventListener("pix:updated", onPix);
      window.removeEventListener("auth:login", onLogin);
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, []);

  return (
    <div className="p-4 md:p-6 rounded-2xl" style={{background:"linear-gradient(180deg,#1A1A1A,#0E0E0E)"}}>
      <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Saldo</h2>
      <p className="text-sm text-gray-400 mb-6">Visão geral da sua conta Aurea.</p>

      <div className="flex items-baseline gap-3">
        <div className="text-4xl md:text-5xl font-extrabold text-yellow-400">
          {loading ? "…" : formatBRL(balance)}
        </div>
        {err && <span className="text-red-400 text-sm">{err}</span>}
      </div>

      <div className="mt-4 flex gap-2">
        <button className="px-4 py-2 rounded-xl bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">PIX</button>
        <button className="px-4 py-2 rounded-xl bg-gray-800 text-gray-200 border border-gray-700">Transferir</button>
      </div>
    </div>
  );
}

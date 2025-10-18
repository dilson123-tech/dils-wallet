import React, { useEffect, useState } from "react";

type BalanceResp = { balance?: number };

const fmtBRL = (v: number | null | undefined): string => {
  if (typeof v === "number" && Number.isFinite(v)) {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
  }
  return "—";
};

export default function Dashboard() {
  const [balance, setBalance] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${globalThis.globalThis.BASE_API}/api/v1/accounts/2/balance`);
        const b: BalanceResp = await readJson(r);
        console.log(">>> backend respondeu:", b);
        console.log(">>> resposta bruta do backend:", b);
        console.log(">>> resposta bruta do backend:", b);
        setBalance(Number.isFinite(Number(b?.balance)) ? Number(b!.balance) : null);
      } catch (e) {
        console.error("[Aurea][Component] fetch error", e);
        setBalance(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <p className="p-6 text-[var(--gold)]">Carregando dados...</p>;
  }

  return (
    <div className="p-6 text-white">
      <h1 className="text-3xl font-bold mb-6 text-[var(--gold)]">Painel do Cliente — Aurea Gold</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 rounded-2xl bg-[#111] shadow-md border border-[var(--gold)]/20">
          <h2 className="text-xl font-semibold mb-2 text-[var(--gold)]">Saldo (LIVE)</h2>
            <div style={{marginTop:"4px",fontSize:"12px",color:"#9ca3af"}}>[DEBUG DASHBOARD LIVE]</div>
            <div style={{fontSize:"12px",color:"#999"}}>[DEBUG DASHBOARD LIVE]</div>
          <p>Visão geral da sua conta Aurea.</p>
            <p className="text-3xl font-bold mt-4 text-[var(--gold)]">{balance === null ? "—" : fmtBRL(balance)}</p>
            <div style={{fontSize:"12px",color:"#9ca3af"}}>debug balance: {String(balance)}</div>
            <div className="text-xs text-gray-400 mt-2">debug balance: {String(balance)}</div>
          <pre className="text-xs text-gray-400 mt-2">debug: {JSON.stringify({ balance })}</pre>
        </div>

        <div className="p-4 rounded-2xl bg-[#111] shadow-md border border-[var(--gold)]/20">
          <h2 className="text-xl font-semibold mb-2 text-[var(--gold)]">Atividade</h2>
          <p className="mb-4">Últimas movimentações aparecerão aqui.</p>
        </div>
      </div>

      <footer className="text-sm text-gray-400 mt-8">
        © {new Date().getFullYear()} Aurea Bank — excelência em experiência financeira.
      </footer>
    </div>
  );
}

import React from "react";
import { fetchSummary } from "@/services/summary";
import PixChart from "./PixChart";

export default function SummaryKpis() {
  const [s, setS] = React.useState<any>(null);

  React.useEffect(() => {
    (async () => {
      try {
        const data = await fetchSummary();
        setS(data || {});
      } catch (e) {
        console.error("SummaryKpis fail", e);
        setS({});
      }
    })();
  }, []);

  const totalEnvios     = Number(s?.total_envios ?? 0);
  const totalTransacoes = Number(s?.total_transacoes ?? 0);
  const recebimentos    = Number(s?.recebimentos ?? 0);
  const entradas        = Number(s?.entradas ?? 0);
  const saldoEstimado   = Number(s?.saldo_estimado ?? 0);

  const brl = (v:number=0) =>
    new Intl.NumberFormat("pt-BR", { style:"currency", currency:"BRL" }).format(v);

  return (
    <div className="grid gap-3" style={{gridTemplateColumns:"repeat(2, minmax(0,1fr))"}}>
      
      <div className="p-3 rounded-lg" style={{border:"1px solid rgba(255,215,0,.25)"}}>
        <div className="text-xs opacity-70">Envios</div>
        <div className="text-lg font-semibold">{brl(totalEnvios)}</div>
        <div className="text-xs opacity-60">{totalTransacoes} transações</div>
      </div>

      <div className="p-3 rounded-lg" style={{border:"1px solid rgba(255,215,0,.25)"}}>
        <div className="text-xs opacity-70">Recebimentos</div>
        <div className="text-lg font-semibold">{brl(recebimentos)}</div>
        <div className="text-xs opacity-60">{entradas} entradas</div>
      </div>

      <div className="p-3 rounded-lg col-span-2" style={{border:"1px solid rgba(255,215,0,.25)"}}>
        <div className="text-xs opacity-70 mb-1">Histórico PIX</div>
        <PixChart txs={s?.txs ?? []} />
      </div>

    </div>
  );
}

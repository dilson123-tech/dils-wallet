import React from "react";
import { fetchSummary } from "@/services/summary";

export default function PixPanel() {
  const [s, setS] = React.useState<any>(null);

  React.useEffect(() => {
    (async () => {
      try {
        const data = await fetchSummary();
        setS(data || {});
      } catch (e) {
        console.error("PixPanel summary fail", e);
        setS({});
      }
    })();
  }, []);

  // Fallbacks seguros
  const total_envios = Number(s?.total_envios ?? s?.envios ?? 0);
  const total_transacoes = Number(s?.total_transacoes ?? s?.transacoes ?? 0);
  const recebimentos = Number(s?.recebimentos ?? 0);
  const entradas = Number(s?.entradas ?? 0);
  const saldo_estimado = Number(s?.saldo_estimado ?? s?.saldo ?? 0);

  const brl = (v: number = 0) =>
    new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL"
    }).format(v);

  return (
    <div style={{ color: "white", padding: "12px" }}>
      <h2 className="text-xl font-bold mb-2">Resumo PIX</h2>

      <div style={{
        border: "1px solid rgba(255,215,0,.3)",
        padding: "8px",
        borderRadius: 8,
        marginBottom: 16
      }}>
        <div>Envios</div>
        <div>{brl(total_envios)}</div>
        <div>{total_transacoes} transações</div>

        <div style={{ marginTop: 8 }}>Recebimentos</div>
        <div>{brl(recebimentos)}</div>
        <div>{entradas} entradas</div>

        <div style={{ marginTop: 8 }}>Saldo estimado</div>
        <div>{brl(saldo_estimado)}</div>
      </div>
    </div>
  );
}

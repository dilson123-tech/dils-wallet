import React from "react";
import { fetchSummary, SummaryTx } from "@/services/summary";

export default function RecentPixList() {
  const [txs, setTxs] = React.useState<SummaryTx[]>([]);

  const brl = (v: number = 0) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);

  React.useEffect(() => {
    (async () => {
      try {
        const s = await fetchSummary();
        setTxs(s?.txs ?? []);
      } catch (e) {
        console.error("summary fail", e);
      }
    })();
  }, []);

  return (
    <div className="pix-list">
      <div className="text-sm text-gray-500 mb-2">Últimas PIX (10)</div>
      <table className="aurea-table compact w-full">
        <tbody>
          {(txs ?? []).slice(0, 10).map((t: any, i: number) => {
            const tipo = (t?.tipo ?? "PIX").toUpperCase();
            const valor = Number(t?.valor ?? 0);
            const dir = tipo.includes("ENVIO") ? "neg" : "pos";
            return (
              <tr key={t?.id ?? i}>
                <td className="w-24 uppercase">{tipo}</td>
                <td className="truncate">{t?.descricao ?? "—"}</td>
                <td className="text-right">
                  <span className={`amount ${dir}`}>{brl(valor)}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

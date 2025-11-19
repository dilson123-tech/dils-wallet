import React, { useEffect, useState } from "react";
import { API_BASE } from "../lib/api";

interface AITx {
  id: number;
  tipo: string;
  valor: number;
  descricao: string;
}

interface AIData {
  total_envios: number;
  total_transacoes: number;
  recebimentos: number;
  entradas: number;
  saldo_estimado: number;
  txs?: AITx[];
}

function fmtBRL(v: number): string {
  return (
    "R$ " +
    v
      .toFixed(2)
      .replace(".", ",")
  );
}

export default function AureaAISummary() {
  const [data, setData] = useState<AIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        setLoading(true);
        const r = await fetch(`${API_BASE}/api/v1/ai/summary`);
        if (!alive) return;
        if (!r.ok) throw new Error("Erro ao buscar IA Summary");
        const j = (await r.json()) as AIData;
        setData(j);
      } catch (e: any) {
        if (!alive) return;
        setErr(e?.message ?? "Falha ao carregar IA");
      } finally {
        if (alive) setLoading(false);
      }
    }

    load();
    return () => {
      alive = false;
    };
  }, []);

  if (loading)
    return (
      <p className="mt-3 text-[11px] text-[#d4af37]">
        Carregando IA…
      </p>
    );

  if (err)
    return (
      <p className="mt-3 text-[11px] text-red-400">
        ⚠ {err}
      </p>
    );

  if (!data) return null;

  const negativo = data.saldo_estimado < 0;

  let maiorEnvio: AITx | null = null;
  if (data.txs && data.txs.length > 0) {
    maiorEnvio = data.txs.reduce<AITx | null>((acc, t) => {
      if (!acc) return t;
      return t.valor > acc.valor ? t : acc;
    }, null as AITx | null);
  }

  return (
    <div className="mt-4 p-3 rounded-2xl border border-[#d4af37]/40 bg-black/40 shadow-[0_0_14px_#d4af3720]">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-[12px] font-bold tracking-wide text-[#d4af37] drop-shadow-[0_0_4px_#d4af37]">
          Inteligência Financeira • IA 3.0
        </h2>
        <span className="text-[9px] px-2 py-0.5 rounded-full border border-[#d4af37]/50 text-[#d4af37]/90">
          ONLINE
        </span>
      </div>

      <div className="text-[11px] space-y-1 opacity-90">
        <p>
          Total enviado:{" "}
          <span className="font-semibold">
            {fmtBRL(data.total_envios)}
          </span>
        </p>
        <p>
          Transações:{" "}
          <span className="font-semibold">
            {data.total_transacoes}
          </span>
        </p>
        <p>
          Saldo estimado:{" "}
          <span className={negativo ? "text-red-400 font-semibold" : "text-green-400 font-semibold"}>
            {fmtBRL(data.saldo_estimado)}
          </span>
        </p>
      </div>

      {maiorEnvio && (
        <div className="mt-2 text-[11px]">
          <p className="opacity-80">
            Maior envio recente:{" "}
            <span className="font-semibold">
              {maiorEnvio.descricao} ({fmtBRL(maiorEnvio.valor)})
            </span>
          </p>
        </div>
      )}

      <div className="mt-2 text-[11px]">
        {negativo ? (
          <p className="text-red-400 font-semibold">
            ⚠ Gastos maiores que entradas. Controle recomendado.
          </p>
        ) : (
          <p className="text-green-400 font-semibold">
            ✔ Movimentação equilibrada.
          </p>
        )}
      </div>
    </div>
  );
}

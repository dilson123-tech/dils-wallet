import React, { useEffect, useState } from "react";
import { API_BASE, USER_EMAIL } from "./api";

type AIHeadlineResponse = {
  nivel: string;
  headline: string;
  subheadline: string;
  resumo: string;
  destaques: string[];
  recomendacao: string;
  saldo_atual?: number;
  entradas_mes?: number;
  saidas_mes?: number;
  entradas_7d?: number;
  saidas_7d?: number;
  total_contas_7d?: number;
  qtd_contas_7d?: number;
  entradas_previstas?: number;
};

const IaHeadlineLab: React.FC = () => {
  const [data, setData] = useState<AIHeadlineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`${API_BASE}/api/v1/ai/headline-lab`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Email": USER_EMAIL,
          },
          body: JSON.stringify({
            message:
              "resumo do painel Aurea Gold para modulo de credito inteligente ia 3.0",
          }),
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const json = await res.json();
        if (!active) return;
        setData(json as AIHeadlineResponse);
      } catch (err) {
        console.error("IaHeadlineLab error:", err);
        if (!active) return;
        setError("Erro ao carregar IA 3.0 (Painel 3 LAB).");
      } finally {
        if (!active) return;
        setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="w-full max-w-3xl mx-auto space-y-3 text-[11px] text-zinc-100">
      <h2 className="text-xs font-semibold text-amber-300">
        Painel 3 • IA 3.0 Headline (LAB)
      </h2>

      {loading && (
        <p className="text-[11px] text-amber-300">
          Carregando análise da IA 3.0...
        </p>
      )}

      {error && (
        <p className="text-[11px] text-red-400">
          {error}
        </p>
      )}

      {!loading && !error && data && (
        <div className="border border-amber-500/60 rounded-lg p-3 space-y-2 bg-black/60">
          <div className="text-[10px] uppercase tracking-[0.16em] text-amber-400">
            Headline do dia
          </div>
          <div className="text-sm font-semibold text-amber-200">
            {data.headline}
          </div>
          <p className="text-[11px] text-zinc-200">
            {data.subheadline}
          </p>
          <p className="text-[11px] text-zinc-300 whitespace-pre-line">
            {data.resumo}
          </p>
          {data.destaques?.length > 0 && (
            <ul className="mt-1 list-disc list-inside text-[10px] text-zinc-300 space-y-0.5">
              {data.destaques.map((d, idx) => (
                <li key={idx}>{d}</li>
              ))}
            </ul>
          )}
          <p className="mt-1 text-[10px] text-emerald-300">
            {data.recomendacao}
          </p>
        </div>
      )}
    </div>
  );
};

export default IaHeadlineLab;
export { IaHeadlineLab };

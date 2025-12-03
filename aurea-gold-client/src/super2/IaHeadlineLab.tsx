import React, { useEffect, useState } from "react";
import { IaHeadlineCard } from "./IaHeadlineCard";
import type { AureaIaHeadlinePanel } from "./ia3Types";

type ApiHeadlineResponse = AureaIaHeadlinePanel;

export const IaHeadlineLab: React.FC = () => {
  console.debug("[IaHeadlineLab] renderizando Painel 3 Headline LAB");

  const [data, setData] = useState<AureaIaHeadlinePanel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch("/api/v1/ai/headline-lab", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-User-Email": "dilsonpereira231@gmail.com",
            },
            body: JSON.stringify({
              message:
                "Analise o painel SUPER2 (saldo, PIX, entradas, saídas e histórico) e gere uma headline executiva em linguagem Aurea Gold.",
            }),
          });
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const json: ApiHeadlineResponse = await res.json();
        if (active) {
          setData(json);
        }
      } catch (err) {
        console.error("IaHeadlineLab error:", err);
        if (active) {
          setError("Erro ao carregar IA 3.0 (Painel 3 LAB).");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="w-full max-w-3xl mx-auto space-y-3">
      <p className="text-[11px] text-zinc-400">
        Painel 3 • IA 3.0 Headline (LAB)
      </p>

      {loading && (
        <div className="text-[11px] text-zinc-400">
          Carregando análise da IA 3.0...
        </div>
      )}

      {error && (
        <div className="text-[11px] text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && <IaHeadlineCard data={data ?? undefined} />}
    </div>
  );
};

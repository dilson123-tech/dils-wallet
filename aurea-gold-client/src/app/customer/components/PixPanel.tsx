import React, { useEffect, useState } from "react";
import PixModal from "@/components/PixModal";

// base da API local (ajusta se precisar apontar pro Railway depois)
const API_BASE = "http://localhost:8080/api/v1/pix";

type PixHistoryItem = {
  id: number;
  tipo: "entrada" | "saida";
  valor: number;
  descricao: string;
  created_at: string;
};

export default function PixPanel() {
  const [saldo, setSaldo] = useState<number | null>(null);
  const [history, setHistory] = useState<PixHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function fetchBalanceAndHistory() {
    try {
      setLoading(true);
      setErrorMsg(null);

      // GET /balance
      const resBalance = await fetch(API_BASE + "/balance");
      if (!resBalance.ok) {
        throw new Error("Falha ao buscar saldo PIX");
      }
      const dataBalance = await resBalance.json();
      setSaldo(dataBalance.saldo ?? 0);

      // GET /history
      const resHist = await fetch(API_BASE + "/history");
      if (!resHist.ok) {
        throw new Error("Falha ao buscar histórico PIX");
      }
      const dataHist = await resHist.json();
      setHistory(Array.isArray(dataHist) ? dataHist : []);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Erro inesperado");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchBalanceAndHistory();
  }, []);

  async function handleSendPix(payload: {
    chave: string;
    valor: number;
    descricao: string;
  }) {
    try {
      setErrorMsg(null);

      // POST /send
      const res = await fetch(API_BASE + "/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        let body: any = {};
        try {
          body = await res.json();
        } catch (_) {
          /* ignore */
        }
        throw new Error(body.detail || "Falha ao enviar PIX");
      }

      // sucesso: fecha modal e recarrega saldo+histórico
      setShowModal(false);
      await fetchBalanceAndHistory();
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "Erro ao enviar PIX");
    }
  }
  function formatMoney(v: number | null): string {
    if (v === null || v === undefined) return "R$ 0,00";
    return v.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 2,
    });
  }

  function formatDate(iso: string) {
    const d = new Date(iso);
    return d.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // tokens Aurea Gold
  const goldText = "text-[#d4af37]";
  const goldBg = "bg-[#d4af37]";
  const goldBorder = "border-[#d4af37]";

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-4 md:p-8 flex flex-col gap-6">

      {/* Header topo */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div>
          <h1 className={"text-2xl font-semibold " + goldText + " tracking-wide"}>
            PIX • Aurea Gold
          </h1>
          <p className="text-sm text-neutral-400">
            Envie e receba PIX instantâneo. Controle total em tempo real.
          </p>
        </div>

        <button
          onClick={function () { setShowModal(true); }}
          className={
            "px-4 py-2 rounded-xl font-semibold text-black " +
            goldBg +
            " hover:brightness-110 active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(212,175,55,0.6)]"
          }
        >
          Enviar PIX
        </button>
      </div>

      {/* Erro global */}
      {errorMsg ? (
        <div className="bg-red-500/10 text-red-400 border border-red-500/40 rounded-lg px-4 py-2 text-sm">
          {errorMsg}
        </div>
      ) : null}

      {/* Cards saldo / entradas / saídas */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Saldo atual */}
        <div
          className={
            "relative rounded-2xl border " +
            goldBorder +
            " bg-[#1a1a1a] p-5 shadow-[0_0_30px_rgba(212,175,55,0.15)] flex flex-col justify-between"
          }
        >
          <div className="text-xs text-neutral-400 font-light">
            Saldo disponível (PIX)
          </div>
          <div className={"text-3xl font-bold " + goldText + " leading-tight"}>
            {loading ? "..." : formatMoney(saldo)}
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">
            Valor liberado agora para PIX de saída.
          </div>

          <div className="pointer-events-none absolute inset-0 rounded-2xl border border-[#ffffff0a] shadow-[0_0_120px_rgba(212,175,55,0.3)_inset]" />
        </div>

        {/* Entradas */}
        <div className="rounded-2xl border border-neutral-700 bg-[#101010] p-5 flex flex-col justify-between">
          <div className="text-xs text-neutral-400 font-light">
            Últimos PIX recebidos
          </div>
          <div className="text-xl font-semibold text-green-400 leading-tight">
            {loading
              ? "..."
              : formatMoney(
                  history
                    .filter(function (t) {
                      return t.tipo === "entrada";
                    })
                    .slice(0, 5)
                    .reduce(function (acc, t) {
                      return acc + t.valor;
                    }, 0)
                )}
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">
            Soma das últimas entradas.
          </div>
        </div>

        {/* Saídas */}
        <div className="rounded-2xl border border-neutral-700 bg-[#101010] p-5 flex flex-col justify-between">
          <div className="text-xs text-neutral-400 font-light">
            Últimos PIX enviados
          </div>
          <div className="text-xl font-semibold text-red-400 leading-tight">
            {loading
              ? "..."
              : formatMoney(
                  history
                    .filter(function (t) {
                      return t.tipo === "saida";
                    })
                    .slice(0, 5)
                    .reduce(function (acc, t) {
                      return acc + t.valor;
                    }, 0)
                )}
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">
            Soma das últimas saídas.
          </div>
        </div>
      </section>
      {/* Histórico PIX */}
      <section className="bg-[#0f0f0f] border border-neutral-800 rounded-2xl overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.8)]">
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 bg-[#1a1a1a]">
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-neutral-200">
              Histórico PIX
            </span>
            <span className="text-[11px] text-neutral-500">
              Entradas e saídas recentes
            </span>
          </div>
          <span
            className={
              "text-[11px] font-medium px-2 py-1 rounded-lg border " +
              goldBorder +
              " " +
              goldText +
              " bg-[#1a1a1a]"
            }
          >
            {history.length} movimentos
          </span>
        </div>

        <div className="max-h-[320px] overflow-y-auto divide-y divide-neutral-900 text-sm">
          {loading ? (
            <div className="p-4 text-neutral-500 text-center text-xs">
              Carregando histórico...
            </div>
          ) : history.length === 0 ? (
            <div className="p-4 text-neutral-500 text-center text-xs">
              Nenhum PIX encontrado.
            </div>
          ) : (
            history.map(function (item) {
              return (
                <div
                  key={item.id}
                  className="flex items-start justify-between px-4 py-3 hover:bg-white/[0.02] transition-colors"
                >
                  <div className="flex flex-col">
                    <span
                      className={
                        "font-semibold " +
                        (item.tipo === "entrada"
                          ? "text-green-400"
                          : "text-red-400")
                      }
                    >
                      {item.tipo === "entrada" ? "+ " : "- "}
                      {formatMoney(item.valor)}
                    </span>

                    <span className="text-neutral-300 text-[13px]">
                      {item.descricao || "PIX"}
                    </span>

                    <span className="text-[11px] text-neutral-500">
                      {formatDate(item.created_at)}
                    </span>
                  </div>

                  <div
                    className={
                      "text-[10px] px-2 py-1 rounded-md font-medium h-fit " +
                      (item.tipo === "entrada"
                        ? "bg-green-500/10 text-green-400 border border-green-500/30"
                        : "bg-red-500/10 text-red-400 border border-red-500/30")
                    }
                  >
                    {item.tipo === "entrada" ? "Recebido" : "Enviado"}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>

      {showModal ? (
        <PixModal
          onClose={function () { setShowModal(false); }}
          onConfirm={handleSendPix}
        />
      ) : null}
    </div>
  );
}

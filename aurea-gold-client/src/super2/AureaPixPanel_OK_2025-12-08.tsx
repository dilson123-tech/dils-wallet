import React, { useEffect, useMemo, useState } from "react";
import { API_BASE, USER_EMAIL, fetchPixHistory, PixHistoryItem } from "./api";
import { getToken } from "../lib/auth";

const __pixAuthHeaders = (): Record<string, string> => {
  const tok = getToken();
  if (!tok || tok === "null" || tok === "undefined") return {};
  return { Authorization: `Bearer ${tok}` };
};


type PixAction = "send" | "charge" | "statement" | null;

type AureaPixPanelProps = {
  initialAction?: PixAction | null;
};

function formatBRL(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "R$ 0,00";
  }

  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function AureaPixPanel({
  initialAction = null,
}: AureaPixPanelProps) {
  const [activeAction, setActiveAction] = useState<PixAction>(null);

  // estados para saldo/entradas/saídas do backend
  const [saldoPix, setSaldoPix] = useState<number | null>(null);
  const [entradasMes, setEntradasMes] = useState<number | null>(null);
  const [saidasMes, setSaidasMes] = useState<number | null>(null);
  const [saldoSource, setSaldoSource] = useState<"real" | "simulado">(
    "simulado"
  );
  const [balanceLoading, setBalanceLoading] = useState(false);
  const [balanceError, setBalanceError] = useState<string | null>(null);
  const [balanceReloadToken, setBalanceReloadToken] = useState(0);

  // envio de PIX
  const [sendPixKey, setSendPixKey] = useState("");
  const [sendPixAmount, setSendPixAmount] = useState("");
  const [sendPixDescription, setSendPixDescription] = useState("");
  const [sendPixLoading, setSendPixLoading] = useState(false);
  const [sendPixError, setSendPixError] = useState<string | null>(null);
  const [sendPixSuccess, setSendPixSuccess] = useState<string | null>(null);

  // cobrança (modo LAB – ainda visual)
  const [chargePixAmount, setChargePixAmount] = useState("");
  const [chargePixDescription, setChargePixDescription] = useState("");
  const [chargePixRef, setChargePixRef] = useState("");
  const [chargePixSuccess, setChargePixSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (initialAction) {
      setActiveAction(initialAction);
    }
  }, [initialAction]);

  // carrega saldo/entradas/saídas do endpoint /api/v1/pix/balance
  useEffect(() => {
    let alive = true; // flag para evitar atualizar state depois do unmount

    const loadBalance = async () => {
      try {
        setBalanceLoading(true);
        setBalanceError(null);

        const resp = await fetch(`${API_BASE}/api/v1/pix/balance`, {
          headers: {
            Authorization: `Bearer ${getToken()}`,
"Content-Type": "application/json",
            "X-User-Email": USER_EMAIL,
          },
        });

        if (!resp.ok) {
          console.warn(
            "[AureaPixPanel] Falha ao buscar /api/v1/pix/balance:",
            resp.status
          );
          if (!alive) return;
          setBalanceError(
            "Não consegui atualizar os dados do PIX agora. Tente novamente em instantes."
          );
          return;
        }

        const data: any = await resp.json();

        const saldo =
          typeof data?.saldo === "number"
            ? data.saldo
            : typeof data?.balance === "number"
            ? data.balance
            : null;

        const entradas =
          typeof data?.entradas_mes === "number" ? data.entradas_mes : null;

        const saidas =
          typeof data?.saidas_mes === "number" ? data.saidas_mes : null;

        const modo =
          data?.source === "real" || data?.source === "REAL" ? "real" : "simulado";

        if (!alive) return;

        setSaldoPix(saldo);
        setEntradasMes(entradas);
        setSaidasMes(saidas);
        setSaldoSource(modo);
      } catch (err) {
        console.error("[AureaPixPanel] Erro ao carregar /api/v1/pix/balance:", err);
        if (!alive) return;
        setBalanceError(
          "Erro ao carregar os dados do PIX. Tente novamente em instantes."
        );
      } finally {
        if (!alive) return;
        setBalanceLoading(false);
      }
    };

    loadBalance();

    return () => {
      alive = false;
    };
  }, [balanceReloadToken]);

  const handleReloadBalance = () => {
    setBalanceReloadToken((prev) => prev + 1);
  };

  const handleSubmitSendPix = async (e: React.FormEvent) => {
    e.preventDefault();
    setSendPixError(null);
    setSendPixSuccess(null);

    const key = sendPixKey.trim();
    const numeric = sendPixAmount.replace(".", "").replace(",", ".");
    const amount = Number(numeric);

    if (!key) {
      setSendPixError("Informe a chave PIX ou destinatário.");
      return;
    }

    if (!amount || !Number.isFinite(amount) || amount <= 0) {
      setSendPixError("Informe um valor válido para enviar.");
      return;
    }

    try {
      setSendPixLoading(true);

      const idemKey =
        typeof crypto !== "undefined" &&
        "randomUUID" in crypto &&
        typeof crypto.randomUUID === "function"
          ? crypto.randomUUID()
          : `pix-${Date.now()}-${Math.random().toString(36).slice(2)}`;

      const resp = await fetch(`${API_BASE}/api/v1/pix/send`, {
        method: "POST",
        headers: { ...__pixAuthHeaders(), 
          "Content-Type": "application/json",
          "X-User-Email": USER_EMAIL,
          "Idempotency-Key": idemKey,
        },
        body: JSON.stringify({
          valor: amount,
          msg: sendPixDescription || "PIX enviado pelo app Aurea Gold",
          dest: key,
          idem_key: idemKey,
        }),
      });

      if (!resp.ok) {
        console.warn("[AureaPixPanel] Falha ao enviar PIX:", resp.status);
        setSendPixError(
          "Não consegui enviar o PIX agora. Tente novamente em instantes."
        );
        return;
      }

      const result: any = await resp.json().catch(() => null);

      if (result && result.status === "duplicate") {
        setSendPixSuccess(
          "PIX já havia sido registrado. Evitamos um envio duplicado."
        );
      } else {
        setSendPixSuccess("PIX registrado com sucesso no backend Aurea Gold.");
      }

      setTimeout(() => {
        setSendPixSuccess(null);
      }, 3000);

      setSendPixKey("");
      setSendPixAmount("");
      setSendPixDescription("");
      handleReloadBalance();
    } catch (err) {
      console.error("[AureaPixPanel] Erro inesperado ao enviar PIX:", err);
      setSendPixError(
        "Erro inesperado ao enviar PIX. Tente novamente em instantes."
      );
    } finally {
      setSendPixLoading(false);
    }
  };

  const handleGenerateCharge = (e: React.FormEvent) => {
    e.preventDefault();
    setChargePixSuccess(null);

    const numeric = chargePixAmount.replace(".", "").replace(",", ".");
    const amount = Number(numeric);

    if (!amount || amount <= 0) {
      setChargePixSuccess("Defina um valor válido antes de gerar a cobrança.");
      return;
    }

    const ref = `AG-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
    setChargePixRef(ref);
    setChargePixSuccess(
      "Cobrança simulada criada. Quando o backend estiver plugado, vamos gerar QR Code/BR Code real."
    );
  };

  // histórico do extrato
  const [history, setHistory] = useState<PixHistoryItem[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // carrega histórico quando o usuário entra no modo EXTRATO
  useEffect(() => {
    if (activeAction !== "statement") return;
    if (history !== null || historyLoading) return;

    setHistoryLoading(true);
    setHistoryError(null);

    Promise.resolve(fetchPixHistory())
      .then((raw) => {
        let arr: unknown = raw;

        if (Array.isArray(raw)) {
          arr = raw;
        } else if (raw && typeof raw === "object") {
          const anyRaw = raw as any;
          arr = anyRaw.items ?? anyRaw.history ?? anyRaw.data ?? [];
        }

        if (!Array.isArray(arr)) {
          setHistory([]);
          return;
        }

        setHistory(arr as PixHistoryItem[]);
      })
      .catch((err: any) => {
        setHistoryError(
          err?.message ||
            "Não consegui carregar o extrato do PIX agora. Tente novamente em instantes."
        );
      })
      .finally(() => {
        setHistoryLoading(false);
      });
  }, [activeAction, history, historyLoading]);

  const resumo = useMemo(() => {
    if (!history || history.length === 0) {
      return {
        totalEnvios: 0,
        totalRecebidos: 0,
        totalTaxas: 0,
        liquido: 0,
        taxaMediaPercentual: 0,
      };
    }

    let totalEnvios = 0;
    let totalRecebidos = 0;
    let totalTaxas = 0;

    for (const item of history) {
      if (item.tipo === "envio") {
        totalEnvios += item.valor;

        if (typeof item.taxa_valor === "number") {
          totalTaxas += item.taxa_valor;
        }
      } else if (item.tipo === "recebido") {
        totalRecebidos += item.valor;
      }
    }

    const liquido = totalRecebidos - totalEnvios - totalTaxas;
    const taxaMediaPercentual =
      totalEnvios > 0 ? (totalTaxas / totalEnvios) * 100 : 0;

    return {
      totalEnvios,
      totalRecebidos,
      totalTaxas,
      liquido,
      taxaMediaPercentual,
    };
  }, [history]);

  const saldoPixDisplay = saldoPix !== null ? formatBRL(saldoPix) : "R$ 0,00";
  const entradasMesDisplay =
    entradasMes !== null ? formatBRL(entradasMes) : "R$ 0,00";
  const saidasMesDisplay =
    saidasMes !== null ? formatBRL(saidasMes) : "R$ 0,00";

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* HEADER */}
      <header className="mb-4">
        <div className="text-[10px] uppercase tracking-wide text-zinc-400">
          Aurea Gold • Área PIX oficial
        </div>
        <h1 className="text-lg md:text-xl font-semibold text-amber-300 mt-1">
          PIX • Carteira Aurea Gold
        </h1>
        <p className="text-xs text-zinc-400 mt-1 max-w-xl">
          Essa é a visão dedicada do PIX no app Aurea Gold. Vamos evoluir este
          painel para ser a central de transferências, extrato rápido e atalhos.
        </p>

        <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/40 bg-zinc-950/80 px-3 py-1">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[10px] uppercase tracking-wide text-amber-200">
              {saldoSource === "real"
                ? "Dados reais carregados do backend Aurea Gold"
                : "Modo simulado • aguardando conexão completa do PIX"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {balanceLoading && (
              <span className="text-[10px] text-zinc-400">
                Atualizando dados do PIX...
              </span>
            )}
            <button
              type="button"
              onClick={handleReloadBalance}
              className="rounded-full border border-amber-500/60 bg-black/60 px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-amber-200 hover:bg-amber-500/10 active:scale-[0.97] transition"
            >
              Atualizar dados PIX
            </button>
          </div>
        </div>

        {balanceError && (
          <p className="mt-2 text-[11px] text-rose-300">{balanceError}</p>
        )}

        <div className="h-px w-32 bg-amber-500 mt-3" />
      </header>

      {/* CARDS PRINCIPAIS */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
        <div className="rounded-xl border border-amber-500/40 bg-zinc-950/80 p-3">
          <div className="text-[10px] uppercase tracking-wide text-zinc-400 mb-1">
            Saldo PIX
          </div>
          <div className="text-2xl font-semibold text-amber-300">
            {saldoPixDisplay}
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">
            {saldoSource === "real"
              ? "Saldo carregado diretamente do backend Aurea Gold."
              : "Valor simulado por enquanto. Na versão conectada, esse card mostra o saldo real da carteira PIX."}
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-emerald-300 mb-1">
            Entradas do mês
          </div>
          <div className="text-lg font-semibold text-emerald-300">
            {entradasMesDisplay}
          </div>
          <p className="text-[11px] text-emerald-200/80 mt-1">
            Total de PIX recebidos no mês atual, conforme os registros do Aurea
            Gold.
          </p>
        </div>

        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-rose-300 mb-1">
            Saídas do mês
          </div>
          <div className="text-lg font-semibold text-rose-300">
            {saidasMesDisplay}
          </div>
          <p className="text-[11px] text-rose-200/80 mt-1">
            Total de PIX enviados no mês atual, somando transferências e
            pagamentos feitos pela carteira Aurea Gold.
          </p>
        </div>
      </section>

      {/* AÇÕES RÁPIDAS */}
      <section className="mb-4">
        <h2 className="text-[11px] uppercase tracking-wide text-zinc-400 mb-2">
          Ações rápidas
        </h2>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setActiveAction("send")}
            className={`px-3 py-2 rounded-full text-[11px] font-semibold uppercase tracking-wide transition active:scale-[0.97] ${
              activeAction === "send"
                ? "bg-amber-500 text-black shadow-[0_0_18px_rgba(251,191,36,0.6)]"
                : "bg-amber-500 text-black/90"
            }`}
          >
            Enviar PIX
          </button>

          <button
            type="button"
            onClick={() => setActiveAction("charge")}
            className={`px-3 py-2 rounded-full text-[11px] uppercase tracking-wide transition active:scale-[0.97] ${
              activeAction === "charge"
                ? "border border-amber-400 bg-black text-amber-200 shadow-[0_0_14px_rgba(251,191,36,0.5)]"
                : "border border-amber-500/60 text-amber-300 bg-transparent"
            }`}
          >
            Cobrar via PIX
          </button>

          <button
            type="button"
            onClick={() => setActiveAction("statement")}
            className={`px-3 py-2 rounded-full text-[11px] uppercase tracking-wide transition active:scale-[0.97] ${
              activeAction === "statement"
                ? "border border-zinc-200 bg-zinc-900 text-zinc-50"
                : "border border-zinc-700 text-zinc-200 bg-transparent"
            }`}
          >
            Ver extrato PIX
          </button>
        </div>

        {/* PAINEL DE AÇÃO SELECIONADA */}
        <div className="mt-3 rounded-xl border border-zinc-800 bg-black/50 p-3 text-[11px] text-zinc-200">
          {!activeAction && (
            <p className="text-zinc-400">
              Selecione uma ação acima para ver os detalhes aqui. Nesta área
              vamos colocar, na próxima fase, os formulários e integrações
              reais de PIX do Aurea Gold.
            </p>
          )}

          {activeAction === "send" && (
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold text-amber-300 mb-1">
                  Enviar PIX (modo LAB)
                </h3>
                <p className="text-zinc-300">
                  Preencha os campos abaixo para testar o envio. Usamos o
                  endpoint real quando disponível e bloqueamos duplicidades via
                  Idempotency-Key.
                </p>
              </div>

              <form
                className="grid gap-2 md:grid-cols-2"
                onSubmit={handleSubmitSendPix}
              >
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-zinc-400">
                    Chave PIX ou destinatário
                  </span>
                  <input
                    className="rounded-lg border border-zinc-700 bg-black px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-500"
                    value={sendPixKey}
                    onChange={(e) => setSendPixKey(e.target.value)}
                    placeholder="CPF, CNPJ, telefone, e-mail ou chave aleatória"
                  />
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-zinc-400">
                    Valor
                  </span>
                  <input
                    className="rounded-lg border border-zinc-700 bg-black px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-500"
                    value={sendPixAmount}
                    onChange={(e) => setSendPixAmount(e.target.value)}
                    placeholder="Ex: 125,90"
                  />
                </label>

                <label className="md:col-span-2 flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-zinc-400">
                    Descrição (opcional)
                  </span>
                  <input
                    className="rounded-lg border border-zinc-700 bg-black px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-500"
                    value={sendPixDescription}
                    onChange={(e) => setSendPixDescription(e.target.value)}
                    placeholder="Ex: pagamento da mensalidade Aurea Gold"
                  />
                </label>

                <div className="md:col-span-2 flex flex-wrap items-center gap-2">
                  <button
                    type="submit"
                    disabled={sendPixLoading}
                    className="rounded-full border border-amber-500/60 bg-amber-500/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-wide text-amber-200 hover:bg-amber-500/20 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {sendPixLoading ? "Enviando..." : "Enviar agora"}
                  </button>
                  {sendPixSuccess && (
                    <span className="text-[11px] text-emerald-300">
                      {sendPixSuccess}
                    </span>
                  )}
                  {sendPixError && (
                    <span className="text-[11px] text-rose-300">
                      {sendPixError}
                    </span>
                  )}
                </div>
              </form>
            </div>
          )}

          {activeAction === "charge" && (
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold text-amber-300 mb-1">
                  Cobrar via PIX (modo LAB)
                </h3>
                <p className="text-zinc-300">
                  Simulamos a criação da cobrança. Quando o backend estiver
                  plugado, este fluxo vai gerar QR Code/BR Code real e escutar o
                  status do pagamento.
                </p>
              </div>

              <form
                className="grid gap-2 md:grid-cols-2"
                onSubmit={handleGenerateCharge}
              >
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-zinc-400">
                    Valor da cobrança
                  </span>
                  <input
                    className="rounded-lg border border-amber-500/40 bg-black px-3 py-2 text-sm text-amber-100 outline-none focus:border-amber-400"
                    value={chargePixAmount}
                    onChange={(e) => setChargePixAmount(e.target.value)}
                    placeholder="Ex: 59,90"
                  />
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-zinc-400">
                    Descrição/identificador
                  </span>
                  <input
                    className="rounded-lg border border-amber-500/40 bg-black px-3 py-2 text-sm text-amber-100 outline-none focus:border-amber-400"
                    value={chargePixDescription}
                    onChange={(e) => setChargePixDescription(e.target.value)}
                    placeholder="Ex: assinatura Aurea Gold"
                  />
                </label>

                <div className="md:col-span-2 flex flex-wrap items-center gap-2">
                  <button
                    type="submit"
                    className="rounded-full border border-amber-500/60 bg-amber-500/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-wide text-amber-200 hover:bg-amber-500/20 active:scale-[0.98]"
                  >
                    Gerar cobrança simulada
                  </button>

                  {chargePixSuccess && (
                    <span className="text-[11px] text-emerald-300">
                      {chargePixSuccess}
                    </span>
                  )}

                  {chargePixRef && (
                    <span className="text-[10px] text-amber-300">
                      Ref: {chargePixRef}
                    </span>
                  )}
                </div>
              </form>
            </div>
          )}

          {activeAction === "statement" && (
            <div>
              <h3 className="font-semibold text-amber-300 mb-1">
                Extrato PIX (modo real + LAB)
              </h3>
              <p className="text-zinc-300 mb-2">
                Aqui você acompanha os envios e recebimentos de PIX e, quando
                houver, as taxas repassadas pelo parceiro e o resultado líquido
                de cada operação.
              </p>

              {/* RESUMO FINANCEIRO COM TAXAS */}
              <div className="mt-1 rounded-lg border border-zinc-700 bg-black/60 p-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                <div>
                  <div className="text-zinc-500 uppercase tracking-wide">
                    Envios do período
                  </div>
                  <div className="font-semibold text-rose-300">
                    {formatBRL(resumo.totalEnvios)}
                  </div>
                </div>

                <div>
                  <div className="text-zinc-500 uppercase tracking-wide">
                    Recebimentos
                  </div>
                  <div className="font-semibold text-emerald-300">
                    {formatBRL(resumo.totalRecebidos)}
                  </div>
                </div>

                <div>
                  <div className="text-zinc-500 uppercase tracking-wide">
                    Taxas do período
                  </div>
                  <div className="font-semibold text-amber-300">
                    {formatBRL(resumo.totalTaxas)}
                  </div>
                  <div className="text-[9px] text-zinc-500">
                    {resumo.totalEnvios > 0
                      ? `${resumo.taxaMediaPercentual.toLocaleString("pt-BR", {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 2,
                        })}% médio sobre envios`
                      : "Sem envios no período"}
                  </div>
                </div>

                <div>
                  <div className="text-zinc-500 uppercase tracking-wide">
                    Resultado líquido
                  </div>
                  <div
                    className={`font-semibold ${
                      resumo.liquido >= 0
                        ? "text-emerald-300"
                        : "text-rose-300"
                    }`}
                  >
                    {formatBRL(resumo.liquido)}
                  </div>
                </div>
              </div>

              {historyLoading && (
                <p className="mt-2 text-[10px] text-zinc-400">
                  Carregando extrato do PIX...
                </p>
              )}

              {historyError && (
                <p className="mt-2 text-[10px] text-red-400">{historyError}</p>
              )}

              {!historyLoading && !historyError && (
                <div>
                  {(!history || history.length === 0) && (
                    <p className="mt-2 text-[10px] text-zinc-400">
                      Ainda não encontramos movimentações de PIX registradas
                      para este usuário. Assim que o backend começar a salvar as
                      transações, elas aparecerão aqui.
                    </p>
                  )}

                  {history && history.length > 0 && (
                    <div className="mt-3 space-y-1.5 max-h-60 overflow-y-auto pr-1">
                      {history.slice(0, 30).map((item) => {
                        const isEnvio = item.tipo === "envio";

                        const taxaPercent =
                          typeof item.taxa_percentual === "number"
                            ? item.taxa_percentual
                            : undefined;

                        const taxaValor =
                          typeof item.taxa_valor === "number" ? item.taxa_valor : 0;

                        const valorLiquido =
                          typeof item.valor_liquido === "number"
                            ? item.valor_liquido
                            : isEnvio
                            ? item.valor - taxaValor
                            : item.valor;

                        const created =
                          (item.timestamp || item.created_at) &&
                          new Date(item.timestamp || item.created_at || "").toLocaleString("pt-BR");

                        const chipLabel = isEnvio ? "Envio PIX" : "PIX recebido";
                        const mainColor = isEnvio
                          ? "text-rose-300"
                          : "text-emerald-300";
                        const borderColor = isEnvio
                          ? "border-rose-500/40"
                          : "border-emerald-500/40";
                        const bgColor = isEnvio
                          ? "bg-rose-950/40"
                          : "bg-emerald-950/20";

                        const cardClassName = [
                          "rounded-lg",
                          "border",
                          borderColor,
                          bgColor,
                          "px-2.5",
                          "py-2",
                          "flex",
                          "flex-col",
                          "gap-1",
                        ].join(" ");

                        return (
                          <div
                            key={
                              (item as any).id ||
                              `${item.tipo}-${item.timestamp || item.created_at || ""}-${item.valor}`
                            }
                            className={cardClassName}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span className="inline-flex h-5 px-2 items-center rounded-full border border-zinc-600 bg-black/60 text-[9px] uppercase tracking-wide text-zinc-200">
                                  {chipLabel}
                                </span>
                                {created && (
                                  <span className="text-[9px] text-zinc-500">
                                    {created}
                                  </span>
                                )}
                              </div>
                              <div className={`text-sm font-semibold ${mainColor}`}>
                                {formatBRL(item.valor)}
                              </div>
                            </div>

                            <div className="text-[11px] text-zinc-200">
                              {item.descricao || "PIX"}
                            </div>

                            <div className="flex flex-wrap gap-1 text-[9px] text-zinc-300">
                              {typeof taxaValor === "number" && taxaValor > 0 && (
                                <span className="inline-flex items-center rounded-full bg-black/40 border border-amber-500/60 px-2 py-[1px]">
                                  Taxa: {formatBRL(taxaValor)}
                                </span>
                              )}

                              {typeof valorLiquido === "number" && (
                                <span className="inline-flex items-center rounded-full bg-black/40 border border-zinc-600 px-2 py-[1px]">
                                  Líquido: {formatBRL(valorLiquido)}
                                </span>
                              )}

                              {typeof taxaPercent === "number" && (
                                <span className="inline-flex items-center rounded-full bg-black/40 border border-amber-500/40 px-2 py-[1px] text-amber-200">
                                  Taxa:{" "}
                                  {taxaPercent.toLocaleString("pt-BR", {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2,
                                  })}
                                  %
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
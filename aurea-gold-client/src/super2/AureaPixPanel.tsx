import React, { useEffect, useMemo, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  CircleHelp,
  Copy,
  Gauge,
  History,
  KeyRound,
  QrCode,
  ReceiptText,
  RefreshCw,
  Send,
  ShieldCheck,
} from "lucide-react";
import { API_BASE, USER_EMAIL, fetchPixHistory, fetchWalletPartnerStatus, type PixHistoryItem, type WalletPartnerStatus } from "./api";
import { apiGet } from "../app/lib/http";
import { withAuth } from "../lib/api";
import { getToken } from "../lib/auth";

type PixAction = "send" | "charge" | "statement" | null;

type AureaPixPanelProps = {
  initialAction?: PixAction | null;
};

type PixInsightMetrics = {
  total_transacoes: number;
  entradas_brutas: number;
  saidas_brutas: number;
  taxas_totais: number;
  saldo_liquido_estimado: number;
  entradas_7d: number;
  saidas_7d: number;
  entradas_mes: number;
  saidas_mes: number;
};

type PixInsightResponse = {
  nivel: string;
  headline: string;
  subheadline: string;
  resumo: string;
  metricas: PixInsightMetrics;
};

type PixHubTileProps = {
  title: string;
  subtitle: string;
  Icon: LucideIcon;
  active?: boolean;
  disabled?: boolean;
  onClick?: () => void;
};

function PixHubTile({
  title,
  subtitle,
  Icon,
  active = false,
  disabled = false,
  onClick,
}: PixHubTileProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex flex-col items-center justify-center text-center shadow-[0_8px_18px_rgba(15,23,42,0.14)] transition active:scale-[0.98] ${
        active
          ? "bg-[linear-gradient(180deg,#F8E46D_0%,#D2A900_100%)] ring-2 ring-[#FFF1A6]"
          : "bg-[linear-gradient(180deg,#E9CF43_0%,#CBA500_100%)]"
      } ${disabled ? "cursor-not-allowed opacity-70" : "hover:brightness-105"}`} style={{ height: 72, width: "85%", justifySelf: "center", padding: "8px 6px", boxSizing: "border-box" }}
    >
      <div className="mb-1 flex items-center justify-center rounded-[14px] bg-white/18" style={{ width: 34, height: 34 }}><Icon size={20} strokeWidth={2.4} className="text-[#0B2536]" /></div>

      <div
        className="text-[#0B2536]"
        style={{
          fontSize: 11.8,
          lineHeight: 1,
          fontFamily: '"Arial Black", Arial, sans-serif',
          fontWeight: 900,
        }}
      >
        {title}
      </div>

      <p className="mt-1 leading-tight text-[#123047]/80" style={{ fontSize: 10.2, fontWeight: 800, lineHeight: 1.05 }}>
        {subtitle}
      </p>
    </button>
  );
}

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


function formatDescricaoPublicaPix(
  descricao: string | null | undefined
): string {
  if (!descricao) return "";

  const lower = descricao.toLowerCase();

  // Se a descrição mencionar taxa, não mostramos o texto original para o cliente.
  // Isso evita exibir coisas como "PIX com taxa 0,8%".
  if (lower.includes("taxa")) {
    return "Movimento registrado pela carteira PIX Aurea Gold.";
  }

  return descricao;
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

  const [walletPartnerStatus, setWalletPartnerStatus] =
    useState<WalletPartnerStatus | null>(null);
  const [walletPartnerStatusError, setWalletPartnerStatusError] =
    useState<string | null>(null);

  // estados para IA 3.0 do PIX (dados oficiais)
  const [pixInsight, setPixInsight] = useState<PixInsightResponse | null>(null);
  const [pixInsightLoading, setPixInsightLoading] = useState(false);
  const [pixInsightError, setPixInsightError] = useState<string | null>(null);
  const [pixInsightReloadToken, setPixInsightReloadToken] = useState(0);

  const pixInsightMetrics: PixInsightMetrics = pixInsight?.metricas ?? {
    total_transacoes: 0,
    entradas_brutas: 0,
    saidas_brutas: 0,
    taxas_totais: 0,
    saldo_liquido_estimado: 0,
    entradas_7d: 0,
    saidas_7d: 0,
    entradas_mes: 0,
    saidas_mes: 0,
  };

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

  useEffect(() => {
    let alive = true;

    fetchWalletPartnerStatus()
      .then((status) => {
        if (!alive) return;
        setWalletPartnerStatus(status);
        setWalletPartnerStatusError(null);
      })
      .catch((err) => {
        console.error("[AureaPixPanel] Erro ao carregar status do parceiro:", err);
        if (!alive) return;
        setWalletPartnerStatusError("Não consegui confirmar o modo da wallet agora.");
      });

    return () => {
      alive = false;
    };
  }, []);

  // carrega saldo/entradas/saídas do endpoint /api/v1/pix/balance
  useEffect(() => {
    let alive = true; // flag para evitar atualizar state depois do unmount

    const loadBalance = async () => {
      try {
        setBalanceLoading(true);
        setBalanceError(null);

                  const data: any = await apiGet("/api/v1/pix/balance?days=7");
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

  // carrega IA 3.0 do PIX (dados oficiais) em /api/v1/ai/chat
  useEffect(() => {
    let alive = true;

    const loadPixInsight = async () => {
        try {
          setPixInsightLoading(true);
          setPixInsightError(null);

          const token = getToken();

          if (!token) {
            if (!alive) return;
            setPixInsightError("Sessão inválida. Entre novamente na Aurea Gold.");
            return;
          }

          const resp = await fetch(`${API_BASE}/api/v1/ai/chat`, withAuth({
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              message: "Analise o PIX do usuário (últimos movimentos/mes). Seja direto: riscos, oportunidades e próximos passos.",
            }),
          }));

          if (!resp.ok) {
            console.warn(
              "[AureaPixPanel] Falha ao buscar /api/v1/ai/chat:",
              resp.status
            );
            if (!alive) return;
            setPixInsightError(
              "Não consegui carregar a IA do PIX 3.0 agora. Tente novamente em instantes."
            );
            return;
          }

          const data: any = await resp.json();

          if (!alive) return;
          setPixInsight(data || null);
        } catch (err) {
          console.error(
            "[AureaPixPanel] Erro ao carregar /api/v1/ai/chat:",
            err
          );
          if (!alive) return;
          setPixInsightError(
            "Erro ao carregar a IA do PIX 3.0. Tente novamente em instantes."
          );
        } finally {
          if (!alive) return;
          setPixInsightLoading(false);
        }
      };

    loadPixInsight();

    return () => {
      alive = false;
    };
  }, [pixInsightReloadToken]);

  const handleReloadBalance = () => {
    setBalanceReloadToken((prev) => prev + 1);
  };

  const handleReloadPixInsight = () => {
    setPixInsightReloadToken((prev) => prev + 1);
  };

  const isDemoWallet =
    walletPartnerStatus?.wallet_mode !== "partner" ||
    walletPartnerStatus?.real_money !== true;

  const walletModeLabel = walletPartnerStatus
    ? isDemoWallet
      ? "Modo demonstração"
      : "Modo parceiro real"
    : "Verificando modo da carteira";

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

        const token = getToken();

        if (!token) {
          setSendPixError("Você precisa entrar na Aurea Gold para enviar PIX.");
          return;
        }

        const resp = await fetch(`${API_BASE}/api/v1/pix/send`, withAuth({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": idemKey,
          },
          body: JSON.stringify({
            dest: key,
            valor: amount,
            msg: (sendPixDescription || "PIX enviado pelo app Aurea Gold").trim(),
          }),
        }));

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
          setSendPixSuccess(
            isDemoWallet
              ? "PIX demo registrado. Não houve movimentação financeira real."
              : "PIX registrado com sucesso no backend Aurea Gold."
          );
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
      "Cobrança demo criada. Não houve cobrança real. Quando o parceiro financeiro estiver plugado, vamos gerar QR Code/BR Code real."
    );
  };

  
  const handleAskPixInsight = async () => {
    if (iaPixLoading) return;

    setIaPixError(null);
    setIaPixLoading(true);

    try {
      // monta um resumo textual para a IA 3.0 com base nos totais atuais
      const resumoTexto = [
        `Envios do período: ${formatBRL(resumo.totalEnvios)}`,
        `Recebimentos do período: ${formatBRL(resumo.totalRecebidos)}`,
        `Taxas do período: ${formatBRL(resumo.totalTaxas)}`,
        `Resultado líquido: ${formatBRL(resumo.liquido)}`,
        resumo.totalEnvios > 0
          ? ` sobre envios: ${resumo.taxaMediaPercentual.toLocaleString("pt-BR", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}%`
          : "Ainda não há envios para calcular taxa média.",
      ].join(" | ");

      const mensagem =
        "[MODO INSIGHT PIX] Analise o extrato do PIX do mês com foco em risco,  e sustentabilidade financeira. Dados resumidos: " +
        resumoTexto +
        ". Dê um diagnóstico objetivo (alertas, pontos fortes, recomendações práticas).";

        const tok = getToken();
        if (!tok) {
          throw new Error("Sessão inválida. Entre novamente na Aurea Gold.");
        }

        const resp = await fetch(`${API_BASE}/api/v1/ai/chat`, withAuth({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: mensagem }),
        }));

      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }

      const data: any = await resp.json().catch(() => null);
      const reply =
        data && typeof data.reply === "string"
          ? data.reply
          : JSON.stringify(data, null, 2);

      setIaPixInsight(reply);
    } catch (err) {
      console.error("[AureaPixPanel] Erro ao pedir insight da IA 3.0:", err);
      setIaPixError(
        "Não consegui falar com a IA 3.0 agora para analisar o extrato. Tente novamente em instantes."
      );
    } finally {
      setIaPixLoading(false);
    }
  };


  // normaliza payloads variados do backend para um formato único no front
  const normalizePixHistoryItem = (x: any): PixHistoryItem | null => {
    if (!x || typeof x !== "object") return null;

    const low = (v: any) => String(v ?? "").toLowerCase().trim();
    const num = (v: any) => {
      const n = Number(v);
      return Number.isFinite(n) ? n : 0;
    };

    const t = low(x.tipo ?? x.type ?? x.kind ?? x.direction);
    const isEnvio =
      ["envio","saida","send","out","debit","debito","pagamento","payment"].includes(t) ||
      Boolean(x.is_out) ||
      (typeof x.valor === "number" && x.valor < 0) ||
      (typeof x.amount === "number" && x.amount < 0) ||
      (typeof x.value === "number" && x.value < 0);

    const isRecebido =
      ["recebido","entrada","receive","in","credit","credito","recebimento"].includes(t) ||
      Boolean(x.is_in) ||
      Boolean(x.recebido);

    const tipo: "envio" | "recebido" = isEnvio && !isRecebido ? "envio" : "recebido";

    const valorRaw = x.valor ?? x.amount ?? x.value ?? x.valor_bruto ?? x.valor_total ?? 0;
    const valor = Math.abs(num(valorRaw));

    const taxa_valor = num(x.taxa_valor ?? x.fee_value ?? x.fee ?? x.taxa ?? 0);
    const taxa_percentual = num(x.taxa_percentual ?? x.fee_percent ?? x.taxa_percent ?? 0);

    const netRaw = x.valor_liquido ?? x.net ?? x.valorLiquido;
    const valor_liquido = Number.isFinite(Number(netRaw))
      ? num(netRaw)
      : (tipo === "envio" ? Math.max(0, valor - taxa_valor) : valor);

    const created_at = x.created_at ?? x.createdAt ?? x.timestamp ?? x.data ?? x.date ?? null;
    const descricao = String(x.descricao ?? x.description ?? x.memo ?? x.nome ?? "");

    return {
      ...(x as any),
      tipo,
      valor,
      taxa_valor,
      taxa_percentual,
      valor_liquido,
      created_at,
      descricao,
    } as PixHistoryItem;
  };


  // histórico do extrato
  const [history, setHistory] = useState<PixHistoryItem[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [iaPixInsight, setIaPixInsight] = useState<string | null>(null);
  const [iaPixLoading, setIaPixLoading] = useState(false);
  const [iaPixError, setIaPixError] = useState<string | null>(null);


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

        const normalized = (arr as any[])
          .map(normalizePixHistoryItem)
          .filter(Boolean) as PixHistoryItem[];
        setHistory(normalized);
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

  const saldoPixDisplay = saldoPix !== null ? formatBRL(Math.max(0, saldoPix)) : "R$ 0,00";
  const entradasMesDisplay =
    entradasMes !== null ? formatBRL(entradasMes) : "R$ 0,00";
  const saidasMesDisplay =
    saidasMes !== null ? formatBRL(saidasMes) : "R$ 0,00";


  // PIX_EARLY_INTERNAL_PAGE_OK
  if (activeAction) {
    const pixPageTitle =
      activeAction === "send"
        ? "Enviar PIX"
        : activeAction === "charge"
        ? "Cobrança Pix"
        : "Extrato PIX";

    return (
      <section className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto px-4 pt-8 pb-32">
        <section className="rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.14),transparent_28%),linear-gradient(180deg,rgba(7,59,88,0.98),rgba(6,30,47,0.98))] px-5 pt-5 pb-6 text-white shadow-[0_14px_32px_rgba(0,0,0,0.18)]">
          <button
            type="button"
            onClick={() => setActiveAction(null)}
            className="inline-flex items-center rounded-full border border-emerald-300/30 bg-emerald-400/14 px-3 py-1 text-[11px] font-black text-emerald-200 shadow-[0_8px_18px_rgba(16,185,129,0.12)]"
          >
            ← Voltar para Pix
          </button>

          <p className="mt-5 text-[10px] uppercase tracking-[0.18em] text-[#D4AF37]">
            Pix Aurea
          </p>

          <h1
            className="mt-2 text-[#F5C842]"
            style={{
              fontSize: 26,
              lineHeight: 1,
              fontFamily: '"Arial Black", Arial, sans-serif',
              fontWeight: 900,
              letterSpacing: "-0.02em",
            }}
          >
            {pixPageTitle}
          </h1>

          <p className="mt-3 text-[14px] leading-relaxed text-[#E6EDF5]">
            {activeAction === "send"
              ? "Envio preparado em modo seguro. No sandbox, nenhum dinheiro real é movimentado."
              : activeAction === "charge"
              ? "Cobrança Pix preparada para QR Code, BR Code e link quando houver parceiro homologado."
              : "Histórico e leitura operacional dos movimentos Pix da carteira."}
          </p>
        </section>

        <section className="mt-5 rounded-[28px] bg-[linear-gradient(180deg,#16364B_0%,#0D2436_100%)] px-5 pt-5 pb-6 text-[#f4f8ff] shadow-[0_10px_22px_rgba(0,0,0,0.12)]">
          {activeAction === "send" && (
            <div className="space-y-3">
              <h3
                className="text-[#F5C842]"
                style={{
                  fontSize: 18,
                  lineHeight: 1,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  fontWeight: 900,
                }}
              >
                Enviar PIX
              </h3>

              <p className="text-[13px] leading-relaxed text-[#D7D0BE]">
                Preencha os campos abaixo para registrar o fluxo. No modo demonstração, isso não movimenta dinheiro real.
              </p>

              <form className="grid gap-3" onSubmit={handleSubmitSendPix}>
                <input
                  className="rounded-[16px] border border-amber-500/20 bg-black/60 px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-400"
                  value={sendPixKey}
                  onChange={(e) => setSendPixKey(e.target.value)}
                  placeholder="Chave PIX ou destinatário"
                />

                <input
                  className="rounded-[16px] border border-amber-500/20 bg-black/60 px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-400"
                  value={sendPixAmount}
                  onChange={(e) => setSendPixAmount(e.target.value)}
                  placeholder="Valor"
                />

                <input
                  className="rounded-[16px] border border-amber-500/20 bg-black/60 px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-400"
                  value={sendPixDescription}
                  onChange={(e) => setSendPixDescription(e.target.value)}
                  placeholder="Descrição opcional"
                />

                <button
                  type="submit"
                  disabled={sendPixLoading}
                  className="rounded-[18px] bg-[linear-gradient(180deg,#E6C84F_0%,#C99A06_100%)] px-4 py-3 text-[12px] font-black text-[#0A1F2E] shadow-[0_8px_18px_rgba(15,23,42,0.14)] disabled:opacity-60"
                  style={{ fontFamily: '"Arial Black", Arial, sans-serif' }}
                >
                  {sendPixLoading ? "Registrando..." : isDemoWallet ? "Registrar teste demo" : "Enviar agora"}
                </button>

                {sendPixSuccess && <p className="text-[11px] text-emerald-300">{sendPixSuccess}</p>}
                {sendPixError && <p className="text-[11px] text-rose-300">{sendPixError}</p>}
              </form>
            </div>
          )}

          {activeAction === "charge" && (
            <div className="space-y-3">
              <h3
                className="text-[#F5C842]"
                style={{
                  fontSize: 18,
                  lineHeight: 1,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  fontWeight: 900,
                }}
              >
                Cobrança Pix
              </h3>

              <p className="text-[13px] leading-relaxed text-[#D7D0BE]">
                Simulamos a criação da cobrança. Quando o parceiro estiver plugado, este fluxo vai gerar QR Code/BR Code real.
              </p>

              <form className="grid gap-3" onSubmit={handleGenerateCharge}>
                <input
                  className="rounded-[16px] border border-amber-500/20 bg-black/60 px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-400"
                  value={chargePixAmount}
                  onChange={(e) => setChargePixAmount(e.target.value)}
                  placeholder="Valor da cobrança"
                />

                <input
                  className="rounded-[16px] border border-amber-500/20 bg-black/60 px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-400"
                  value={chargePixDescription}
                  onChange={(e) => setChargePixDescription(e.target.value)}
                  placeholder="Descrição/identificador"
                />

                <button
                  type="submit"
                  className="rounded-[18px] bg-[linear-gradient(180deg,#E6C84F_0%,#C99A06_100%)] px-4 py-3 text-[12px] font-black text-[#0A1F2E] shadow-[0_8px_18px_rgba(15,23,42,0.14)]"
                  style={{ fontFamily: '"Arial Black", Arial, sans-serif' }}
                >
                  Gerar cobrança simulada
                </button>

                {chargePixSuccess && <p className="text-[11px] text-emerald-300">{chargePixSuccess}</p>}
                {chargePixRef && <p className="text-[10px] text-[#D4AF37]">Ref: {chargePixRef}</p>}
              </form>
            </div>
          )}

          {activeAction === "statement" && (
            <div className="space-y-3">
              <h3
                className="text-[#F5C842]"
                style={{
                  fontSize: 18,
                  lineHeight: 1,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  fontWeight: 900,
                }}
              >
                Extrato PIX
              </h3>

              <div className="grid grid-cols-1 gap-3">
                <div className="rounded-[20px] border border-amber-500/16 bg-[rgba(12,30,42,0.74)] px-4 py-3">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">Saldo Pix</p>
                  <p className="mt-1 text-lg font-black text-[#f4f8ff]">{saldoPixDisplay}</p>
                </div>

                <div className="rounded-[20px] border border-amber-500/16 bg-[rgba(12,30,42,0.74)] px-4 py-3">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">Entradas</p>
                  <p className="mt-1 text-lg font-black text-[#f4f8ff]">{entradasMesDisplay}</p>
                </div>

                <div className="rounded-[20px] border border-amber-500/16 bg-[rgba(12,30,42,0.74)] px-4 py-3">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-[#D4AF37]">Saídas</p>
                  <p className="mt-1 text-lg font-black text-[#f4f8ff]">{saidasMesDisplay}</p>
                </div>
              </div>
            </div>
          )}
        </section>
      </section>
    );
  }


  return (
      <section className="w-full max-w-[390px] sm:max-w-[430px] md:max-w-[960px] mx-auto px-4 pt-8 pb-32">
        <section className="rounded-[30px] bg-[radial-gradient(circle_at_top_right,rgba(212,175,55,0.14),transparent_28%),linear-gradient(180deg,rgba(7,59,88,0.98),rgba(6,30,47,0.98))] px-5 pt-6 pb-7 text-white shadow-[0_14px_32px_rgba(0,0,0,0.18)]">
          <div className="aurea-pix-safe-badge inline-flex items-center justify-center rounded-full border border-amber-300/20 bg-amber-400/10 px-3 py-1 text-[11px] font-semibold tracking-[0.02em] text-[#F6D66B]">
            Pix em modo seguro
          </div>

          <h1
            className="aurea-pix-hero-title mt-5 text-[#F5C842]"
            style={{
              fontSize: 26,
              lineHeight: 1,
              fontFamily: '"Arial Black", Arial, sans-serif',
              fontWeight: 900,
              letterSpacing: "-0.02em",
            }}
          >
            Pix Aurea
          </h1>

          <p className="aurea-pix-hero-copy mt-3 text-[15px] leading-relaxed text-[#E6EDF5]">
            Envie, cobre e acompanhe seus Pix com segurança. No sandbox, nada movimenta dinheiro real.
          </p>
        </section>

        <section className="mt-5 rounded-[28px] bg-[linear-gradient(180deg,#16364B_0%,#0D2436_100%)] px-5 pt-5 pb-6 shadow-[0_10px_22px_rgba(0,0,0,0.12)]">
          <div
            className="text-[#D6DEE8]"
            style={{
              fontSize: 13,
              fontFamily: '"Arial Black", Arial, sans-serif',
              fontWeight: 900,
            }}
          >
            Pix rápido
          </div>

          <div
            className="mt-5 grid grid-cols-3"
            style={{ gap: 8 }}
          >
            <PixHubTile title="Enviar" subtitle="Pix de saída" Icon={Send} active={activeAction === "send"} onClick={() => setActiveAction("send")} />
            <PixHubTile title="Cobrar" subtitle="Gerar cobrança" Icon={QrCode} active={activeAction === "charge"} onClick={() => setActiveAction("charge")} />
            <PixHubTile title="QR Code" subtitle="Cobrança Pix" Icon={QrCode} active={activeAction === "charge"} onClick={() => setActiveAction("charge")} />
            <PixHubTile title="Copia" subtitle="BR Code" Icon={Copy} active={activeAction === "charge"} onClick={() => setActiveAction("charge")} />
            <PixHubTile title="Extrato" subtitle="Histórico" Icon={History} active={activeAction === "statement"} onClick={() => setActiveAction("statement")} />
            <PixHubTile title="Chaves" subtitle="Em breve" Icon={KeyRound} disabled />
            <PixHubTile title="Limites" subtitle="Bloqueio real" Icon={Gauge} disabled />
            <PixHubTile title="Recibos" subtitle="Sem fake" Icon={ReceiptText} disabled />
            <PixHubTile title="Ajuda" subtitle="Suporte" Icon={CircleHelp} disabled />
          </div>

          <div className="mt-6 rounded-[24px] border border-white/12 bg-[linear-gradient(180deg,rgba(13,43,63,0.98),rgba(8,26,40,0.98))] px-4 pt-4 pb-5 shadow-[0_12px_24px_rgba(0,0,0,0.16)]">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-[14px] bg-white/8 text-[#F5C842]">
                <ShieldCheck size={24} strokeWidth={2.3} />
              </div>

              <div className="min-w-0 flex-1">
                <h3
                  className="text-[#F8FAFC]"
                  style={{
                    fontSize: 20,
                    lineHeight: 1.1,
                    fontFamily: '"Arial Black", Arial, sans-serif',
                    fontWeight: 900,
                  }}
                >
                  Pix protegido
                </h3>

                <p className="mt-2 text-[14px] leading-relaxed text-[#CBD5E1]">
                  {isDemoWallet
                    ? "Dinheiro real, Pix real e comprovante real permanecem bloqueados até parceiro homologado."
                    : `Provedor ${walletPartnerStatus?.provider || "partner"} ativo para operação real.`}
                </p>

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                    Saldo {saldoPixDisplay}
                  </span>
                  <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                    Entradas {entradasMesDisplay}
                  </span>
                  <span className="rounded-full bg-white/8 px-3 py-1 text-[11px] font-semibold text-[#E6EDF5]">
                    Saídas {saidasMesDisplay}
                  </span>
                  <button
                    type="button"
                    onClick={handleReloadBalance}
                    className="inline-flex items-center gap-1.5 rounded-full bg-[#F5C842] px-3 py-1 text-[11px] font-black text-[#0B2536] active:scale-[0.97]"
                  >
                    <RefreshCw size={13} className={balanceLoading ? "animate-spin" : ""} />
                    Atualizar
                  </button>
                </div>

                {walletPartnerStatusError && (
                  <p className="mt-2 text-[11px] text-rose-200">{walletPartnerStatusError}</p>
                )}

                {balanceError && (
                  <p className="mt-2 text-[11px] text-rose-200">{balanceError}</p>
                )}
              </div>
            </div>
          </div>

        {/* PAINEL DE AÇÃO SELECIONADA */}
        <div className="aurea-pix-action-panel mt-4 rounded-[24px] border border-amber-500/14 bg-[linear-gradient(180deg,rgba(12,30,42,0.88),rgba(8,26,40,0.96))] px-5 py-4 text-[11px] text-[#f4f8ff] shadow-[0_12px_26px_rgba(0,0,0,0.18)]">
          <div className="aurea-pix-mode-card mb-4 rounded-[20px] border border-amber-500/12 bg-[linear-gradient(180deg,rgba(212,175,55,0.07),rgba(6,20,30,0.58))] px-4 py-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)]">
            <div className="aurea-pix-mode-label text-[10px] uppercase tracking-[0.11em] text-[#D4AF37]">
              {walletModeLabel}
            </div>
            <p className="aurea-pix-mode-copy mt-2 max-w-[310px] text-[12px] leading-snug text-[#D7D0BE]">
              {isDemoWallet
                ? "Fluxos de PIX em demonstração, sem movimentar dinheiro real. A operação real será ativada somente via parceiro financeiro homologado."
                : `Provedor ${walletPartnerStatus?.provider || "partner"} ativo para operação real.`}
            </p>
            {walletPartnerStatusError && (
              <p className="mt-1 text-[11px] text-rose-300">{walletPartnerStatusError}</p>
            )}
          </div>

          {!activeAction && (
            <p className="text-[#B8AD95]">
              Selecione uma ação para abrir os fluxos operacionais do PIX. Esta área concentra envio, cobrança e extrato da carteira.
            </p>
          )}

          {activeAction === "send" && (
            <div className="space-y-3">
              <div>
                <h3 className="font-semibold text-[#D4AF37] mb-1">
                  Enviar PIX
                </h3>
                <p className="text-[#D7D0BE]">
                  Preencha os campos abaixo para registrar o fluxo. No modo
                  demonstração, isso não movimenta dinheiro real. No modo parceiro,
                  o envio será roteado pela camada financeira homologada.
                </p>
              </div>

              <form
                className="grid gap-2 md:grid-cols-2"
                onSubmit={handleSubmitSendPix}
              >
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-[#B8AD95]">
                    Chave PIX ou destinatário
                  </span>
                  <input
                    className="rounded-lg border border-amber-500/12 bg-black px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-500"
                    value={sendPixKey}
                    onChange={(e) => setSendPixKey(e.target.value)}
                    placeholder="CPF, CNPJ, telefone, e-mail ou chave aleatória"
                  />
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-[#B8AD95]">
                    Valor
                  </span>
                  <input
                    className="rounded-lg border border-amber-500/12 bg-black px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-500"
                    value={sendPixAmount}
                    onChange={(e) => setSendPixAmount(e.target.value)}
                    placeholder="Ex: 125,90"
                  />
                </label>

                <label className="md:col-span-2 flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-wide text-[#B8AD95]">
                    Descrição (opcional)
                  </span>
                  <input
                    className="rounded-lg border border-amber-500/12 bg-black px-3 py-2 text-sm text-zinc-50 outline-none focus:border-amber-500"
                    value={sendPixDescription}
                    onChange={(e) => setSendPixDescription(e.target.value)}
                    placeholder="Ex: pagamento da mensalidade Aurea Gold"
                  />
                </label>

                <div className="md:col-span-2 flex flex-wrap items-center gap-2">
                  <button
                    type="submit"
                    disabled={sendPixLoading}
                    className="rounded-full border border-amber-500/60 bg-amber-500/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-wide text-amber-100 hover:bg-amber-500/20 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {sendPixLoading ? (isDemoWallet ? "Registrando demo..." : "Enviando...") : (isDemoWallet ? "Registrar teste demo" : "Enviar agora")}
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
                <h3 className="font-semibold text-[#D4AF37] mb-1">
                  Cobrar via PIX
                </h3>
                <p className="text-[#D7D0BE]">
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
                  <span className="text-[10px] uppercase tracking-wide text-[#B8AD95]">
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
                  <span className="text-[10px] uppercase tracking-wide text-[#B8AD95]">
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
                    className="rounded-full border border-amber-500/60 bg-amber-500/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-wide text-amber-100 hover:bg-amber-500/20 active:scale-[0.98]"
                  >
                    Gerar cobrança simulada
                  </button>

                  {chargePixSuccess && (
                    <span className="text-[11px] text-emerald-300">
                      {chargePixSuccess}
                    </span>
                  )}

                  {chargePixRef && (
                    <span className="text-[10px] text-[#D4AF37]">
                      Ref: {chargePixRef}
                    </span>
                  )}
                </div>
              </form>
            </div>
          )}

          {activeAction === "statement" && (
            <div>
              {/* Cards premium de resumo do período */}
              <div className="mb-3 grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-3">
                <div className="rounded-2xl border border-amber-500/70 bg-gradient-to-br from-black via-zinc-950 to-amber-950/30 px-3 py-2.5">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-amber-100/80 mb-1">
                    Envios do período
                  </p>
                  <p className="text-sm md:text-base font-semibold text-amber-100">
                    {formatBRL(resumo.totalEnvios)}
                  </p>
                  <p className="text-[9px] text-[#B8AD95] mt-1">
                    Somando todos os PIX enviados pela carteira Aurea Gold.
                  </p>
                </div>

                <div className="rounded-2xl border border-emerald-500/70 bg-gradient-to-br from-black via-zinc-950 to-emerald-900/30 px-3 py-2.5">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-emerald-200/90 mb-1">
                    Recebimentos do período
                  </p>
                  <p className="text-sm md:text-base font-semibold text-emerald-100">
                    {formatBRL(resumo.totalRecebidos)}
                  </p>
                  <p className="text-[9px] text-emerald-200/80 mt-1">
                    Entradas de PIX recebidas neste período.
                  </p>
                </div>

                <div className="rounded-2xl border border-amber-400/80 bg-gradient-to-br from-black via-zinc-950 to-amber-800/40 px-3 py-2.5">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-amber-100 mb-1">
                    Resultado líquido
                  </p>
                  <p
                              className={`text-sm md:text-base font-semibold ${resumo.liquido >= 0 ? "text-emerald-200" : "text-rose-300"}`}

                  >
                    {formatBRL(resumo.liquido)}
                  </p>
                  <p className="text-[9px] text-[#D7D0BE] mt-1">
                    Diferença entre o que saiu e o que entrou no período.
                  </p>
                </div>
              </div>

              {/* IA 3.0 – Insight do mês com dados oficiais */}
              <div className="mb-3 rounded-2xl border border-amber-500/60 bg-gradient-to-br from-zinc-950 via-black to-amber-950/40 p-3 md:p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.16em] text-amber-100/80">
                      IA 3.0 • Analisar extrato
                    </p>

                    {pixInsightLoading && (
                      <p className="text-[10px] text-[#B8AD95] mt-1">
                        Carregando análise oficial do PIX...
                      </p>
                    )}

                    {pixInsightError && (
                      <p className="text-[10px] text-rose-300 mt-1">
                        {pixInsightError}
                      </p>
                    )}

                    {!pixInsightLoading && !pixInsightError && pixInsight && (
                      <>
                        <p className="text-sm md:text-base font-semibold text-amber-100 mt-1">
                          {pixInsight.headline}
                        </p>
                        <p className="text-[11px] text-[#f4f8ff] mt-1">
                          {pixInsight.subheadline}
                        </p>
                        <p className="text-[10px] text-[#B8AD95] mt-1">
                          {pixInsight.resumo}
                        </p>
                      </>
                    )}

                    {!pixInsightLoading && !pixInsightError && !pixInsight && (
                      <p className="text-[10px] text-[#B8AD95] mt-1">
                        Assim que o histórico oficial de PIX começar a ser
                        registrado na carteira, a IA 3.0 passa a analisar os
                        dados reais das suas movimentações.
                      </p>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={handleReloadPixInsight}
                    className="self-start rounded-full border border-amber-500/70 bg-black/40 px-2.5 py-1 text-[10px] font-medium text-amber-100 hover:bg-amber-500/10 transition"
                  >
                    Atualizar IA do PIX
                  </button>
                </div>

                {pixInsight && !pixInsightLoading && !pixInsightError && (
                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                    <div>
                      <div className="text-[#D7D0BE] uppercase tracking-wide">
                        Saldo líquido estimado
                      </div>
                      <div
                      className={`font-semibold ${pixInsightMetrics.saldo_liquido_estimado >= 0 ? "text-emerald-300" : "text-rose-300"}`}
                      >
                        {formatBRL(pixInsightMetrics.saldo_liquido_estimado)}
                      </div>
                    </div>

                    <div>
                      <div className="text-[#D7D0BE] uppercase tracking-wide">
                        Entradas mês
                      </div>
                      <div className="font-semibold text-emerald-300">
                        {formatBRL(pixInsightMetrics.entradas_mes)}
                      </div>
                    </div>

                    <div>
                      <div className="text-[#D7D0BE] uppercase tracking-wide">
                        Saídas mês
                      </div>
                      <div className="font-semibold text-rose-300">
                        {formatBRL(pixInsightMetrics.saidas_mes)}
                      </div>
                    </div>

                    <div>
                      <div className="text-[#D7D0BE] uppercase tracking-wide">
                        Movimentação 7 dias
                      </div>
                      <div className="font-semibold text-amber-100">
                        {formatBRL(
                          pixInsightMetrics.entradas_7d -
                            pixInsightMetrics.saidas_7d
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <h3 className="font-semibold text-[#D4AF37] mb-1">
                Extrato PIX
              </h3>
              <p className="text-[#D7D0BE] mb-2">
                Aqui você acompanha os envios e recebimentos de PIX e os detalhes de cada operação.
              </p>

              {/* RESUMO FINANCEIRO COM TAXAS */}
              <div className="mt-1 rounded-lg border border-amber-500/12 bg-[rgba(12,30,42,0.88)] p-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                <div>
                  <div className="text-[#D7D0BE] uppercase tracking-wide">
                    Envios do período
                  </div>
                  <div className="font-semibold text-rose-300">
                    {formatBRL(resumo.totalEnvios)}
                  </div>
                </div>

                <div>
                  <div className="text-[#D7D0BE] uppercase tracking-wide">
                    Recebimentos
                  </div>
                  <div className="font-semibold text-emerald-300">
                    {formatBRL(resumo.totalRecebidos)}
                  </div>
                </div>

                {/* Bloco interno de taxas do período (escondido para o cliente final) */}
                <div className="hidden">
                  <div className="text-[#D7D0BE] uppercase tracking-wide">
                    Taxas do período
                  </div>
                  <div className="font-semibold text-[#D4AF37]">
                    {formatBRL(resumo.totalTaxas)}
                  </div>
                  <div className="text-[9px] text-[#D7D0BE]">
                    {resumo.totalEnvios > 0
                      ? `${resumo.taxaMediaPercentual.toLocaleString("pt-BR", {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 2,
                        })}% médio sobre envios`
                      : "Sem envios no período"}
                  </div>
                </div>

                <div>
                  <div className="text-[#D7D0BE] uppercase tracking-wide">
                    Resultado líquido
                  </div>
                  <div
                    className={`font-semibold ${pixInsightMetrics.saldo_liquido_estimado >= 0 ? "text-emerald-300" : "text-rose-300"}`}
                  >
                    {formatBRL(resumo.liquido)}
                  </div>
                </div>
              </div>

              {/* IA 3.0 insight sobre o extrato PIX */}
              <div className="mt-3 rounded-[18px] border border-amber-500/12 bg-[rgba(12,30,42,0.76)] p-4 text-[10px] space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="uppercase tracking-wide text-amber-100">
                    IA 3.0 • Analisar extrato
                  </p>
                  <button
                    type="button"
                    onClick={handleAskPixInsight}
                    disabled={iaPixLoading}
                    className="rounded-full border border-amber-500/18 bg-amber-500/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-100 hover:bg-amber-400/10 active:scale-[0.97] disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {iaPixLoading ? "Analisando..." : "Pedir análise"}
                  </button>
                </div>

                {iaPixError && (
                  <p className="text-[10px] text-rose-300">{iaPixError}</p>
                )}

                {iaPixInsight && !iaPixError && (
                  <p className="text-[11px] text-[#f4f8ff] whitespace-pre-line">
                    {iaPixInsight}
                  </p>
                )}

                {!iaPixInsight && !iaPixError && !iaPixLoading && (
                  <p className="text-[10px] text-[#B8AD95]">
                    Use a IA 3.0 para interpretar o extrato, apontar riscos,
                    oportunidades de economia e sugerir ajustes no uso do PIX.
                  </p>
                )}
              </div>

              {historyLoading && (
                <p className="mt-2 text-[10px] text-[#B8AD95]">
                  Carregando extrato do PIX...
                </p>
              )}

              {historyError && (
                <p className="mt-2 text-[10px] text-red-400">{historyError}</p>
              )}

              {!historyLoading && !historyError && (
                <div>
                  {(!history || history.length === 0) && (
                    <p className="mt-2 text-[10px] text-[#B8AD95]">
                      Ainda não encontramos movimentações de PIX registradas
                      para este usuário. Assim que o backend começar a salvar as
                      transações, elas aparecerão aqui.
                    </p>
                  )}

                  {history && history.length > 0 && (
                    <div className="mt-3 space-y-1.5 max-h-64 md:max-h-72 lg:max-h-80 overflow-y-auto pr-1 border border-amber-500/12 rounded-[18px] bg-[rgba(12,30,42,0.62)] p-2">
                      <div className="flex items-center justify-between text-[10px] text-[#D7D0BE] mb-2 pb-2 border-b border-amber-500/12 pr-1">
                        <span className="uppercase tracking-[0.16em] text-amber-100">
                          Movimentações recentes
                        </span>
                        <span className="rounded-full border border-amber-500/16 bg-amber-500/10 px-2 py-0.5 text-[9px] text-amber-100">
                          {history.length > 30
                            ? "Mostrando 30 de " + history.length + " lançamentos"
                            : history.length + (history.length === 1 ? " lançamento" : " lançamentos")}
                        </span>
                      </div>
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
                          "rounded-xl",
                          "border",
                          borderColor,
                          bgColor,
                          "px-3.5",
                          "py-3",
                          "flex",
                          "flex-col",
                          "gap-1.5",
                          "transition",
                          "duration-150",
                          "transform",
                          "shadow-sm",
                          "hover:shadow-xl",
                          "hover:border-amber-500/18",
                          "hover:bg-amber-500/10",
                          "hover:-translate-y-[1px]",
                          "cursor-default",
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
                                <span className="inline-flex h-5 px-2 items-center rounded-full border border-amber-500/12 bg-[rgba(12,30,42,0.88)] text-[9px] uppercase tracking-[0.12em] text-[#f4f8ff]">
                                  {chipLabel}
                                </span>
                                {created && (
                                  <span className="text-[9px] text-[#D7D0BE]">
                                    {created}
                                  </span>
                                )}
                              </div>
                              <div className={`text-sm font-semibold ${mainColor}`}>
                                {formatBRL(valorLiquido)}
                              </div>
                            </div>

                            <div className="text-[11px] text-[#f4f8ff]">
                              {formatDescricaoPublicaPix(item.descricao) || "PIX"}
                            </div>

                            <div className="text-[9px] text-[#D7D0BE] mt-1">
                              Movimento registrado pela carteira PIX Aurea Gold.
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
    </section>
  );
}

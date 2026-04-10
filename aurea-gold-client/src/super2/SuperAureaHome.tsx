import React, { useEffect, useState } from "react";
import {API_BASE, USER_EMAIL, sendPix, fetchPixList, type PixListItem} from "./api";
import { IaHeadlineLab } from "./IaHeadlineLab";
import AureaAIChat from "./AureaAIChat";
import AureaPixChart from "./AureaPixChart";
import { apiGet } from "../lib/api";
import { getToken } from "../lib/auth";
import { saveTokens } from "../auth/authClient";

type PixShortcutAction = "enviar" | "receber" | "extrato";

type SuperAureaHomeProps = {
  onPixShortcut?: (action: PixShortcutAction) => void;
};

function handlePixShortcutFallback(action: PixShortcutAction) {
  alert(
    "Atalho em construção. Em breve este botão vai levar direto para o painel correspondente do Aurea Gold. 😉"
  );
}

function handleOpenFullIA() {
  const el = document.getElementById("aurea-ai-chat-panel");
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

type AureaServiceKey =
  | "negocios"
  | "ajuda"
  | "open_finance"
  | "cobrar"
  | "qrcode"
  | "emprestimos"
  | "cartoes"
  | "seguros_assistencias"
  | "recarga_celular"
  | "assinaturas"
  | "cofrinhos"
  | "investimentos"
  | "criptomoedas"
  | "informe_rendimentos"
  // Serviços de negócio inspirados no Mercado Pago
  | "vendas"
  | "produtos"
  | "relatorios_faturamento"
  | "gestao_caixa"
  | "taxas_parcelas"
  | "maquininhas"
  | "config_negocio";

function handleServiceShortcut(service: AureaServiceKey) {
  alert(
    "Funcionalidade em construção.\n\n" +
      "Esta área do Aurea Gold vai ser ligada a fluxos reais (ex.: empréstimos, cartões, investimentos, cofrinhos, etc.).\n" +
      "Por enquanto, ela está aqui como protótipo visual do aplicativo oficial."
  );
}

  function formatBRL(value: number | null): string {
    if (value === null || Number.isNaN(value)) {
      return "R$ 0,00";
    }

    return "R$ " + value.toFixed(2).replace(".", ",");
  }

export default function SuperAureaHome({ onPixShortcut }: SuperAureaHomeProps) {
  const [saldoReal, setSaldoReal] = useState<number | null>(null);
  const [saldoModo, setSaldoModo] = useState<"simulado" | "real">("simulado");

  const DEV_LOGIN_ENABLED =
    (import.meta as any).env?.DEV ||
    new URLSearchParams(window.location.search).get("devlogin") === "1";

  const [needAuth, setNeedAuth] = useState(false);
  const [authEmail, setAuthEmail] = useState("");
  const [authPass, setAuthPass] = useState("");
  const [authErr, setAuthErr] = useState<string | null>(null);
  const [authBusy, setAuthBusy] = useState(false);

  async function doDevLogin() {
    if (!DEV_LOGIN_ENABLED) return;
    setAuthErr(null);
    setAuthBusy(true);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: authEmail.trim(), password: authPass }),
      });

      const txt = await resp.text();
      if (!resp.ok) throw new Error(txt || `login ${resp.status}`);

      const j = JSON.parse(txt);
      const atRaw = String(j?.access_token || "");
      const rtRaw = String(j?.refresh_token || "");

      const pickJwt = (v: string) =>
        (v.match(/eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+/) || [])[0] || "";

      const at = (pickJwt(atRaw) || atRaw).trim();
      const rt = rtRaw.trim();

      if (!at || at.length < 20) throw new Error("access_token vazio/curto");

      saveTokens(at, rt && rt.length >= 24 ? rt : null);

      location.reload();
    } catch (e: any) {
      console.warn("❌ Dev login falhou:", e);
      setAuthErr(e?.message || String(e));
    } finally {
      setAuthBusy(false);
    }
  }

  const [saldoUpdatedAt, setSaldoUpdatedAt] = useState<string | null>(null);
  const [entradasMes, setEntradasMes] = useState<number | null>(null);
  const [saidasMes, setSaidasMes] = useState<number | null>(null);
  const [pixInsight, setPixInsight] = useState<string | null>(null);
  const [pixInsightLoading, setPixInsightLoading] = useState(false);
  const [pixInsightError, setPixInsightError] = useState<string | null>(null);

  // ---- PIX MODALS (Send / Extrato) ----
  const [reloadKey, setReloadKey] = useState(0);

  const [pixSendOpen, setPixSendOpen] = useState(false);
  const [pixSendDest, setPixSendDest] = useState("");
  const [pixSendValor, setPixSendValor] = useState("");
  const [pixSendMsg, setPixSendMsg] = useState("");
  const [pixSendBusy, setPixSendBusy] = useState(false);
  const [pixSendErr, setPixSendErr] = useState<string | null>(null);
  const [pixSendOk, setPixSendOk] = useState<string | null>(null);

  const [pixExtratoOpen, setPixExtratoOpen] = useState(false);
  const [pixExtratoBusy, setPixExtratoBusy] = useState(false);
  const [pixExtratoErr, setPixExtratoErr] = useState<string | null>(null);
  const [pixExtratoItems, setPixExtratoItems] = useState<PixListItem[] | null>(null);

    const [forecastNivel, setForecastNivel] = useState<
      | "ok"
      | "atencao"
      | "alerta"
      | "critico"
      | "observacao"
      | "indisponivel"
      | null
    >(null);
    const [forecastPrevisaoFimMes, setForecastPrevisaoFimMes] =
      useState<number | null>(null);

    useEffect(() => {
  let alive = true;

  async function loadSaldo() {
    const tok = getToken();
    if (!tok) {
      // Sem token: não chama endpoints protegidos (evita 401 em loop)
      return;
    }

    try {
      // --- 1) Saldo + entradas/saídas via /api/v1/pix/balance ---
      const data: any = await apiGet("/api/v1/pix/balance?days=7");

      const saldo =
        typeof data?.saldo === "number"
          ? data.saldo
          : typeof data?.balance === "number"
          ? data.balance
          : null;

      const entradas = typeof data?.entradas_mes === "number" ? data.entradas_mes : null;
      const saidas = typeof data?.saidas_mes === "number" ? data.saidas_mes : null;
      const modoReal = data?.source === "real" ? "real" : "simulado";

      if (alive && saldo !== null) {
        setSaldoReal(saldo);
        setSaldoModo(modoReal);
        if (modoReal === "real") setNeedAuth(false);
        if (modoReal === "real") setSaldoUpdatedAt(new Date().toISOString());
        else setSaldoUpdatedAt(null);
        setEntradasMes(entradas);
        setSaidasMes(saidas);
      }

      // --- 2) Forecast PIX ---
      const forecastData: any = await apiGet("/api/v1/pix/forecast");

      if (!alive) return;

      if (
        typeof forecastData?.nivel_risco === "string" &&
        ["ok", "atencao", "alerta", "critico", "observacao", "indisponivel"].includes(
          forecastData.nivel_risco,
        )
      ) {
        setForecastNivel(forecastData.nivel_risco);
      } else {
        setForecastNivel(null);
      }

      if (typeof forecastData?.previsao_fim_mes === "number") {
        setForecastPrevisaoFimMes(forecastData.previsao_fim_mes);
      } else {
        setForecastPrevisaoFimMes(null);
      }
    } catch (e) {
      console.error("[SuperAureaHome] Erro no loadSaldo():", e);
    }
  }

  loadSaldo();

  return () => {
    alive = false;
  };
}, [reloadKey]);
async function handleHomeInsight() {
    if (pixInsightLoading) return;
    setPixInsightError(null);
    setPixInsightLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/api/v1/ai/headline`, {
        method: "POST",
        headers: (() => {
            // AUREA_AI_AUTH_HEADER: injeta Bearer quando houver token
            const h: Record<string, string> = { "Content-Type": "application/json" };
            const tok = getToken();
            if (tok) h["Authorization"] = `Bearer ${tok}`;
            return h;
          })(),
        body: JSON.stringify({
          message: "resumo rápido do mês no pix"
        })
      });

      if (!resp.ok) {
        setPixInsightError("Erro ao buscar Insight PIX");
        return;
      }

      const data = await resp.json();
      setPixInsight(data?.headline || "Insight PIX disponível");
    } catch (err) {
        if (/401|Token ausente/i.test(String(err))) setNeedAuth(true);

      setPixInsightError("Falha de comunicação com IA");
    } finally {
      setPixInsightLoading(false);
    }
  }


  
  // AUREA_PIX_MODALS_V1
  function openPixSend() {
    if (!getToken()) {
      setNeedAuth(true);
      return;
    }
    setPixSendOk(null);
    setPixSendErr(null);
    setPixSendOpen(true);
  }

  async function submitPixSend() {
    if (pixSendBusy) return;
    const tok = getToken();
    if (!tok) {
      setNeedAuth(true);
      setPixSendErr("Sem token. Abra pelo link/QR com #at=...");
      return;
    }
    const dest = pixSendDest.trim();
    const v = Number(String(pixSendValor).replace(",", "."));
    if (!dest) {
      setPixSendErr("Informe o destino (chave/conta).");
      return;
    }
    if (!(v > 0)) {
      setPixSendErr("Informe um valor válido.");
      return;
    }
    setPixSendBusy(true);
    setPixSendErr(null);
    try {
      await sendPix({ dest, valor: v, msg: (pixSendMsg.trim() || null) });
      setPixSendOk("PIX enviado ✅");
      setPixSendDest("");
      setPixSendValor("");
      setPixSendMsg("");
      setReloadKey((k) => k + 1);
    } catch (e: any) {
      const msg = String(e?.message || e);
      if (/401|Token ausente/i.test(msg)) setNeedAuth(true);
      setPixSendErr("Falha ao enviar PIX.");
    } finally {
      setPixSendBusy(false);
    }
  }

  async function openPixExtrato() {
    const tok = getToken();
    if (!tok) {
      setNeedAuth(true);
      return;
    }
    setPixExtratoOpen(true);
    setPixExtratoBusy(true);
    setPixExtratoErr(null);
    try {
      const items = await fetchPixList(50);
      setPixExtratoItems(items || []);
    } catch (e: any) {
      const msg = String(e?.message || e);
      if (/401|Token ausente/i.test(msg)) setNeedAuth(true);
      setPixExtratoErr("Falha ao carregar extrato.");
      setPixExtratoItems(null);
    } finally {
      setPixExtratoBusy(false);
    }
  }

const saldoDisplay =
    saldoModo === "real" ? formatBRL(saldoReal) : "R$ 12.345,67";

  const saldoUpdatedHHMM = saldoUpdatedAt
    ? new Date(saldoUpdatedAt).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
    : null;

  const resultadoMes =
    entradasMes !== null && saidasMes !== null
      ? entradasMes - saidasMes
      : null;

  const resultadoClass =
    resultadoMes !== null && resultadoMes >= 0
      ? "text-emerald-300"
      : "text-red-300";

  const resultadoLabel =
    resultadoMes !== null && resultadoMes >= 0 ? "superávit" : "déficit";

  // --- PIX Atalhos (wire definitivo) ---
  function handlePixAtalho(action: "send" | "receive" | "extrato") {
  
    const tok = getToken();
    if (!tok) {
      setNeedAuth(true);
      return;
    }

    if (action === "send") {
      setPixSendErr(null);
      setPixSendOk(null);
      setPixSendDest("");
      setPixSendValor("");
      setPixSendMsg("");
      setPixSendOpen(true);
      return;
    }

    if (action === "extrato") {
      void openPixExtrato();
      return;
    }

    alert("Receber PIX / QR Code: em breve ✅");
  }


  return (
    <section className="w-full max-w-5xl mx-auto space-y-4 md:space-y-6">
      {/* Modo de dados (real vs simulado) */}
      <div className="mb-2 text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.18em]">
        {saldoModo === "real"
          ? "Dados reais carregados do backend Aurea Gold"
          : "Modo simulado • aguardando conexão completa do PIX"}
      </div>

      {DEV_LOGIN_ENABLED && saldoModo !== "real" && needAuth && (
          <div className="rounded-2xl border border-amber-500/40 bg-zinc-950/70 p-4 md:p-5">
            <p className="text-[11px] md:text-xs text-amber-200/80 uppercase tracking-[0.18em]">
              Conectar ao backend (DEV)
            </p>
            <p className="mt-1 text-xs md:text-sm text-zinc-300">
              Sem token nessa origem (<span className="text-zinc-100">{typeof window !== "undefined" ? window.location.origin : ""}</span>). Faça login e pronto.
            </p>

            <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2">
              <input
                className="w-full rounded-xl bg-black/40 border border-zinc-700 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                placeholder="email/username"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                autoComplete="username"
              />
              <input
                className="w-full rounded-xl bg-black/40 border border-zinc-700 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                placeholder="senha"
                type="password"
                value={authPass}
                onChange={(e) => setAuthPass(e.target.value)}
                autoComplete="current-password"
              />
              <button
                className="rounded-xl bg-amber-500/90 hover:bg-amber-500 text-black font-semibold px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={authBusy || !authEmail || !authPass}
                onClick={doDevLogin}
              >
                {authBusy ? "Conectando..." : "Conectar"}
              </button>
            </div>

            {authErr && <p className="mt-2 text-xs text-red-300">{authErr}</p>}

            <p className="mt-2 text-[10px] text-zinc-500">
              Dica: isso aparece só em DEV (Vite) ou se abrir com <span className="text-zinc-300">?devlogin=1</span>.
            </p>
          </div>
        )}

        {/* Card de saldo principal */}
      <div className="rounded-2xl border border-amber-500/60 bg-gradient-to-br from-black via-zinc-950 to-zinc-900 p-4 md:p-6 shadow-[0_0_40px_rgba(251,191,36,0.18)] flex flex-col md:flex-row justify-between gap-4">
        <div>
          <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.18em]">
            Saldo disponível • Aurea Gold
          </p>
          <p className="mt-1 text-3xl md:text-4xl font-semibold text-amber-300">
            {saldoDisplay}
          </p>
          <p className="mt-1 text-[10px] md:text-[11px] text-zinc-400">
            {saldoModo === "real"
              ? "Saldo atualizado em tempo quase real do seu Aurea Gold (via PIX)."
              : "Valor simulado por enquanto. Na versão conectada, esse saldo vem em tempo real do seu Aurea Gold."}
          </p>
            {saldoModo === "real" && saldoUpdatedHHMM && (
              <p className="mt-1 text-[10px] md:text-[11px] text-zinc-500">
                Atualizado às {saldoUpdatedHHMM}
              </p>
            )}
        </div>

        {/* Card de previsão do mês (forecast PIX) */
        }
        <div className="rounded-2xl border border-amber-500/40 bg-zinc-950/80 p-4 md:p-5 space-y-2">
          <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.18em]">
            Previsão do mês • IA 3.0
          </p>

          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <p className="text-xs md:text-sm text-zinc-300">
                Nível de risco atual:&nbsp;
                <span className="text-xs md:text-sm font-semibold text-zinc-50">
                  {forecastNivel === "critico" && "Crítico"}
                  {forecastNivel === "atencao" && "Atenção"}
                  {forecastNivel === "observacao" && "Observação"}
                  {forecastNivel === "ok" && "Tranquilo"}
                  {!forecastNivel && "—"}
                </span>
              </p>

              <p className="text-[11px] md:text-xs text-zinc-400 mt-1">
                Previsão de saldo ao fim do mês:&nbsp;
                <span className="block text-[11px] md:text-xs text-zinc-100 font-semibold mt-1">
                  {forecastPrevisaoFimMes !== null
                    ? forecastPrevisaoFimMes.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
                    : "Carregando previsão do mês..."}
                </span>
                <span className="text-zinc-100 font-medium">
                </span>
              </p>
            </div>

            <div className="text-[10px] md:text-xs text-zinc-400 md:text-right">
              <p>
                A projeção usa seu histórico PIX do mês para estimar se você termina
                no positivo ou negativo.
              </p>
              <p className="mt-1 text-zinc-500">
                Quanto mais movimentações reais, mais precisa fica a previsão.
              </p>
            </div>
          </div>
        </div>

        {/* Atalhos rápidos PIX */}
        <div className="min-w-[240px] md:min-w-[280px]">
          <div className="mb-3">
            <p className="text-[10px] uppercase tracking-[0.28em] ag-gold-text">
              Ações rápidas
            </p>
            <h3 className="mt-1 text-sm md:text-base font-semibold ag-title">
              PIX e movimentações principais
            </h3>
          </div>

          <div className="grid grid-cols-1 gap-3">
            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("enviar") : handlePixShortcutFallback("enviar"))}
              className="ag-card text-left px-4 py-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-1">
                  <span className="text-2xl leading-none">↑</span>
                  <span className="text-sm font-semibold text-white">
                    Enviar PIX
                  </span>
                  <span className="text-[11px] ag-subtitle leading-relaxed">
                    Transferência imediata com fluxo rápido e seguro.
                  </span>
                </div>
                <span className="text-[10px] uppercase ag-gold-text tracking-[0.2em]">
                  Enviar
                </span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("receber") : handlePixShortcutFallback("receber"))}
              className="ag-card text-left px-4 py-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-1">
                  <span className="text-2xl leading-none">↓</span>
                  <span className="text-sm font-semibold text-white">
                    Receber PIX
                  </span>
                  <span className="text-[11px] ag-subtitle leading-relaxed">
                    Gere cobrança, QR Code e recebimentos com agilidade.
                  </span>
                </div>
                <span className="text-[10px] uppercase ag-gold-text tracking-[0.2em]">
                  Cobrar
                </span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("extrato") : handlePixShortcutFallback("extrato"))}
              className="ag-card text-left px-4 py-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-col gap-1">
                  <span className="text-2xl leading-none">≡</span>
                  <span className="text-sm font-semibold text-white">
                    Ver extrato PIX
                  </span>
                  <span className="text-[11px] ag-subtitle leading-relaxed">
                    Consulte lançamentos recentes e acompanhe movimentações.
                  </span>
                </div>
                <span className="text-[10px] uppercase ag-gold-text tracking-[0.2em]">
                  Extrato
                </span>
              </div>
            </button>
          </div>
        </div>

{/* ===== RESUMO FINANCEIRO PREMIUM ===== */}
      </div>
      <div className="ag-hero px-5 py-5 mb-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.16em]">
              Resumo financeiro do mês
            </p>
            <p className="text-sm md:text-base text-zinc-100">
              Leitura consolidada da sua operação financeira no mês, com foco em clareza, resultado e tomada de decisão.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-amber-400/70 bg-black/70 px-3 py-1 text-[10px] text-amber-200">
            Base operacional • leitura protegida
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-[11px]">
          <div className="rounded-xl border border-emerald-500/50 bg-emerald-900/30 px-3 py-2">
            <p className="text-[10px] text-emerald-200/90 uppercase tracking-[0.14em]">
              Entradas no mês
            </p>
            <p className="mt-1 text-lg font-semibold text-emerald-300">
              {entradasMes !== null ? formatBRL(entradasMes) : "R$ 8.500,00"}
            </p>
            <p className="mt-1 text-[10px] text-emerald-100/80">
              Somando PIX recebidos e créditos principais.
            </p>
          </div>

          <div className="rounded-xl border border-red-500/50 bg-red-900/20 px-3 py-2">
            <p className="text-[10px] text-red-200/90 uppercase tracking-[0.14em]">
              Saídas no mês
            </p>
            <p className="mt-1 text-lg font-semibold text-red-300">
              {saidasMes !== null ? formatBRL(saidasMes) : "R$ 6.200,00"}
            </p>
            <p className="mt-1 text-[10px] text-red-100/80">
              Pagamentos, transferências e débitos recorrentes.
            </p>
          </div>

          <div className="col-span-2 md:col-span-1 rounded-xl border border-amber-500/50 bg-black/60 px-3 py-2 flex flex-col justify-between">
            <p className="text-[10px] text-amber-200/90 uppercase tracking-[0.14em]">
              Resultado do mês
            </p>
            <p className="mt-1 text-lg font-semibold">
              {resultadoMes !== null ? (
                <span className={resultadoClass}>
                  {formatBRL(resultadoMes)} ({resultadoLabel})
                </span>
              ) : (
                <span className="text-zinc-100">
                  R$ 2.300,00 (simulação)
                </span>
              )}
            </p>
            <p className="mt-1 text-[10px] text-zinc-400">
              Diferença entre todas as entradas e saídas do mês. Use este número para ajustar
              reservas, investimentos e gastos do seu negócio.
            </p>
          </div>
        </div>

        <div className="mt-2 flex flex-col md:flex-row md:items-center md:justify-between gap-2 text-[10px] text-zinc-300">
          <div>
            <span className="uppercase tracking-[0.16em] text-amber-300">
              Plano atual: Essencial
            </span>
            <span className="ml-1 text-zinc-400">
              {" "}
              — IA financeira completa e relatórios avançados ficam nos planos Pro, Gold e Empresarial.
            </span>
          </div>
          <button
            type="button"
            onClick={() => (window.location.href = "/planos")}
            className="inline-flex items-center justify-center rounded-full border border-amber-400/80 px-3 py-1 text-[10px] text-amber-100 hover:bg-amber-400/10 active:scale-[0.97] transition"
          >
            Ver planos e benefícios
          </button>
        </div>
      </div>

      {/* Insight IA 3.0 • PIX */}
      <div className="rounded-2xl border border-amber-500/50 bg-gradient-to-br from-black via-zinc-950 to-black p-4 md:p-5 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.16em]">
              IA 3.0 • Situação do seu PIX no mês
            </p>
            <p className="text-[11px] md:text-sm text-zinc-200">
              Diagnóstico rápido usando saldo, entradas, saídas e previsão do mês.
            </p>
          </div>
          <button
            type="button"
            onClick={handleHomeInsight}
            disabled={pixInsightLoading}
            className="inline-flex items-center justify-center rounded-full border border-amber-400/80 bg-black/80 px-3 py-1 text-[10px] text-amber-100 hover:bg-amber-400/10 active:scale-[0.97] disabled:opacity-60 disabled:cursor-not-allowed transition"
          >
            {pixInsightLoading ? "Analisando..." : "Atualizar insight do mês"}
          </button>
        </div>

        {pixInsightError && (
          <p className="text-[11px] text-rose-300">
            {pixInsightError}
          </p>
        )}

        {!pixInsightError && pixInsight && (
          <p className="text-[11px] text-zinc-100 whitespace-pre-line">
            {pixInsight}
          </p>
        )}

        {!pixInsightError && !pixInsight && !pixInsightLoading && (
          <p className="text-[10px] text-zinc-400">
            Toque em "Atualizar insight do mês" para a IA 3.0 ler seu cenário PIX
            e apontar se o momento é de atenção, risco ou folga de caixa.
          </p>
        )}
      </div>

      {/* PIX • Visão rápida */}
      <div className="rounded-2xl border border-emerald-500/50 bg-gradient-to-br from-black via-zinc-950 to-black p-4 md:p-5 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <p className="text-[10px] md:text-[11px] text-emerald-200/80 uppercase tracking-[0.16em]">
              PIX • Visão rápida
            </p>
            <p className="text-[11px] md:text-sm text-zinc-200">
              Gráfico resumindo as movimentações recentes de PIX. Nesta versão, usamos seus
              dados reais dos últimos 7 dias (se não houver movimentações, o gráfico fica zerado).
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/70 bg-black/70 px-3 py-1 text-[10px] text-emerald-200">
            /api/v1/pix/7d • Somente leitura
          </span>
        </div>

        {/* ===== SALDO PREMIUM AUREA GOLD ===== */}
        <div className="ag-hero px-5 py-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex flex-col gap-2">
            <span className="text-[10px] uppercase tracking-[0.28em] ag-soft">
              Saldo disponível
            </span>

            <div className="text-3xl md:text-4xl font-semibold text-white gold-glow">
              {formatBRL(saldoReal)}
            </div>

            <div className="flex items-center gap-2 text-[11px] ag-subtitle">
              <span
                className={`h-2 w-2 rounded-full ${
                  saldoModo === "real" ? "bg-emerald-400" : "bg-yellow-400"
                }`}
              />
              {saldoModo === "real" ? "Saldo real sincronizado" : "Modo simulado"}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 min-w-[240px]">
            <div className="ag-card px-4 py-3">
              <div className="text-[10px] uppercase ag-soft">
                Entradas (mês)
              </div>
              <div className="text-lg font-semibold text-emerald-400 mt-1">
                {formatBRL(entradasMes)}
              </div>
            </div>

            <div className="ag-card px-4 py-3">
              <div className="text-[10px] uppercase ag-soft">
                Saídas (mês)
              </div>
              <div className="text-lg font-semibold text-red-400 mt-1">
                {formatBRL(saidasMes)}
              </div>
            </div>
          </div>
        </div>
      </div>

        <div className="rounded-xl border border-emerald-500/40 bg-black/80 px-2 py-2 md:px-3 md:py-3">
          <AureaPixChart />
        </div>
      </div>

      {/* Serviços Aurea Gold (estilo prateleira Mercado Pago / Nubank) */}
      <div className="rounded-2xl border border-amber-500/40 bg-black/90 p-4 md:p-5 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.16em]">
              Serviços Aurea Gold
            </p>
            <p className="text-[11px] md:text-sm text-zinc-200">
              Tudo o que você espera de uma carteira digital completa, organizado em um
              só lugar.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-zinc-600/80 bg-zinc-950 px-3 py-1 text-[10px] text-zinc-300">
            Protótipo visual • Em construção
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] md:text-[11px]">
          {/* Coluna 1 */}
          <button
            type="button"
            onClick={() => handleServiceShortcut("negocios")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-amber-500/60 bg-zinc-950 px-3 py-2 hover:border-amber-300/80 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            <span className="font-semibold text-amber-200">Negócio Aurea</span>
            <span className="text-[9px] text-zinc-400">
              Conta para MEI, PJ e empreendedores.
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleServiceShortcut("vendas")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 hover:border-amber-300/70 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            <span className="font-semibold text-zinc-100">Vendas</span>
            <span className="text-[9px] text-zinc-400">
              Acompanhe faturamento, tickets médios e volume diário.
            </span>
          </button>

          {/* Coluna 2 */}
          <button
            type="button"
            onClick={() => handleServiceShortcut("produtos")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 hover:border-amber-300/70 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            <span className="font-semibold text-zinc-100">Produtos</span>
            <span className="text-[9px] text-zinc-400">
              Cadastre itens, categorias e controle de estoque.
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleServiceShortcut("relatorios_faturamento")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 hover:border-amber-300/70 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            <span className="font-semibold text-zinc-100">
              Relatórios &amp; faturamento
            </span>
            <span className="text-[9px] text-zinc-400">
              Visão financeira, DRE simplificado e exportações.
            </span>
          </button>

          {/* Coluna 3 */}
          <button
            type="button"
            onClick={() => handleServiceShortcut("gestao_caixa")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 hover:border-amber-300/70 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            <span className="font-semibold text-zinc-100">Gestão de caixa</span>
            <span className="text-[9px] text-zinc-400">
              Entradas, saídas, reservas e projeção de fluxo.
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleServiceShortcut("taxas_parcelas")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 hover:border-amber-300/70 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            <span className="font-semibold text-zinc-100">Taxas &amp; parcelas</span>
            <span className="text-[9px] text-zinc-400">
              Veja quanto paga por venda e simule cenários.
            </span>
          </button>

          {/* Coluna 4 */}
          <button
            type="button"
            onClick={() => handleServiceShortcut("maquininhas")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 hover:border-amber-300/70 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            <span className="font-semibold text-zinc-100">Maquininhas / Tap</span>
            <span className="text-[9px] text-zinc-400">
              Conecte sua maquininha ou solução parceira ao Aurea.
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleServiceShortcut("config_negocio")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 hover:border-amber-300/70 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            <span className="font-semibold text-zinc-100">
              Configurações do negócio
            </span>
            <span className="text-[9px] text-zinc-400">
              Dados da empresa, colaboradores e permissões.
            </span>
          </button>
        </div>
      </div>

      {/* Bloco IA 3.0: Headline + Chat */}
      <div className="grid md:grid-cols-2 gap-4 md:gap-6">
        {/* Headline executiva */}
        <div className="rounded-2xl border border-amber-500/40 bg-zinc-950/90 p-3 md:p-4">
          <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.16em] mb-2">
            IA 3.0 • Headline executiva
          </p>
          <p className="text-[11px] text-zinc-300 mb-3">
            Resumo automático do seu painel Aurea Gold. Nesta versão beta, os dados ainda
            são simulados, mas o formato já é o mesmo da versão executiva.
          </p>
          <IaHeadlineLab />
        </div>

        {/* Chat IA 3.0 completo */}
        <div className="rounded-2xl border border-amber-500/40 bg-black/90 p-3 md:p-4 flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.16em]">
                Falar com a IA 3.0
              </p>
              <p className="text-[11px] text-zinc-300">
                Tire dúvidas sobre saldo, entradas, saídas e histórico do seu Aurea Gold.
              </p>
            </div>
            <button
              type="button"
              onClick={handleOpenFullIA}
              className="px-3 py-1.5 rounded-full border border-amber-400/80 bg-black/80 text-[10px] text-amber-100 hover:border-amber-200 active:scale-[0.97] transition"
            >
              Abrir IA completa
            </button>
          </div>

          <div id="aurea-ai-chat-panel">
            <AureaAIChat />
          </div>
        </div>
      </div>
    
      {/* Acesso a planos Aurea Gold */}
      <div className="mt-6 text-center">
        <button
          type="button"
          onClick={() => window.open('/planos', '_blank')}
          className="text-[10px] md:text-[11px] text-amber-300 underline hover:text-amber-200 transition"
        >
          Conhecer planos Aurea Gold
        </button>
      </div>


      {/* PIX Modals */}
      {pixSendOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-2xl border border-amber-500/40 bg-zinc-950 p-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-amber-200">Enviar PIX</h3>
              <button
                className="text-zinc-400 hover:text-zinc-200 text-sm"
                onClick={() => { setPixSendOpen(false); setPixSendErr(null); setPixSendOk(null); }}
              >
                Fechar
              </button>
            </div>

            <div className="mt-3 space-y-2">
              <input
                className="w-full rounded-xl bg-black/40 border border-zinc-700 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                placeholder="Destino (chave PIX / conta)"
                value={pixSendDest}
                onChange={(e) => setPixSendDest(e.target.value)}
              />
              <input
                className="w-full rounded-xl bg-black/40 border border-zinc-700 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                placeholder="Valor (ex: 10,50)"
                value={pixSendValor}
                onChange={(e) => setPixSendValor(e.target.value)}
                inputMode="decimal"
              />
              <input
                className="w-full rounded-xl bg-black/40 border border-zinc-700 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                placeholder="Mensagem (opcional)"
                value={pixSendMsg}
                onChange={(e) => setPixSendMsg(e.target.value)}
              />

              {pixSendErr && <p className="text-xs text-red-300">{pixSendErr}</p>}
              {pixSendOk && <p className="text-xs text-emerald-300">{pixSendOk}</p>}

              <button
                className="w-full rounded-xl bg-amber-500/90 hover:bg-amber-500 text-black font-semibold px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={pixSendBusy || !pixSendDest || !pixSendValor}
                onClick={submitPixSend}
              >
                {pixSendBusy ? "Enviando..." : "Confirmar envio"}
              </button>
            </div>
          </div>
        </div>
      )}

      {pixExtratoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-amber-500/40 bg-zinc-950 p-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-amber-200">Extrato PIX</h3>
              <button
                className="text-zinc-400 hover:text-zinc-200 text-sm"
                onClick={() => { setPixExtratoOpen(false); setPixExtratoErr(null); }}
              >
                Fechar
              </button>
            </div>

            {pixExtratoBusy && <p className="mt-3 text-xs text-zinc-400">Carregando...</p>}
            {pixExtratoErr && <p className="mt-3 text-xs text-red-300">{pixExtratoErr}</p>}

            {!pixExtratoBusy && !pixExtratoErr && (
              <div className="mt-3 max-h-[70vh] overflow-auto space-y-2">
                {(pixExtratoItems || []).length === 0 ? (
                  <p className="text-xs text-zinc-400">Sem movimentações (ainda).</p>
                ) : (
                  (pixExtratoItems || []).map((it) => (
                    <div key={it.id} className="flex items-start justify-between gap-3 border-b border-zinc-800/70 pb-2">
                      <div className="min-w-0">
                        <p className="text-xs text-zinc-200">
                          <span className="text-zinc-400">#{it.id}</span> • {String(it.tipo || "").toUpperCase()}
                        </p>
                        {it.descricao && <p className="text-[11px] text-zinc-400 truncate">{it.descricao}</p>}
                      </div>
                      <div className="text-xs text-amber-200 whitespace-nowrap">
                        {formatBRL(Number(it.valor || 0))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}

</section>
  );
}

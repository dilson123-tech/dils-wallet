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
    <section className="w-full max-w-[960px] mx-auto space-y-5 md:space-y-6 px-[2px] sm:px-0">
      <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col">
          <span className="text-[10px] sm:text-[11px] uppercase tracking-[0.14em] sm:tracking-[0.22em] text-[#86c0ff]">
            Aurea Gold • Conta
          </span>
          <h2 className="mt-1 text-[1.35rem] sm:text-2xl md:text-3xl font-bold text-[#f4f8ff] leading-tight">
            Sua carteira digital
          </h2>
        </div>

        <span
          className={`self-start sm:self-auto inline-flex items-center rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.18em] ${
            saldoModo === "real"
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              : "border-sky-500/30 bg-sky-500/10 text-sky-200"
          }`}
        >
          {saldoModo === "real" ? "Conta conectada" : "Modo demonstração"}
        </span>
      </div>

      {DEV_LOGIN_ENABLED && saldoModo !== "real" && needAuth && (
          <div className="rounded-2xl border border-sky-500/40 bg-[linear-gradient(180deg,rgba(10,20,40,0.94),rgba(7,15,30,0.98))] p-4 md:p-5">
            <p className="text-[11px] md:text-xs text-sky-200/80 uppercase tracking-[0.18em]">
              Conectar ao backend (DEV)
            </p>
            <p className="mt-1 text-xs md:text-sm text-[#d7e7ff]">
              Sem token nessa origem (<span className="text-[#f4f8ff]">{typeof window !== "undefined" ? window.location.origin : ""}</span>). Faça login e pronto.
            </p>

            <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2">
              <input
                className="w-full rounded-xl bg-[rgba(8,18,35,0.88)] border border-sky-500/30 px-3 py-2 text-sm text-[#f4f8ff] placeholder:text-[#7f97bb]"
                placeholder="email/username"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                autoComplete="username"
              />
              <input
                className="w-full rounded-xl bg-[rgba(8,18,35,0.88)] border border-sky-500/30 px-3 py-2 text-sm text-[#f4f8ff] placeholder:text-[#7f97bb]"
                placeholder="senha"
                type="password"
                value={authPass}
                onChange={(e) => setAuthPass(e.target.value)}
                autoComplete="current-password"
              />
              <button
                className="rounded-xl bg-[linear-gradient(135deg,#5aa0ff,#86c0ff)] hover:brightness-110 text-[#06101f] font-semibold px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={authBusy || !authEmail || !authPass}
                onClick={doDevLogin}
              >
                {authBusy ? "Conectando..." : "Conectar"}
              </button>
            </div>

            {authErr && <p className="mt-2 text-xs text-red-300">{authErr}</p>}

            <p className="mt-2 text-[10px] text-[#8fa8cf]">
              Dica: isso aparece só em DEV (Vite) ou se abrir com <span className="text-[#bfd0ec]">?devlogin=1</span>.
            </p>
          </div>
        )}

        {/* Card de saldo principal */}
      <div className="rounded-[30px] border border-sky-500/40 bg-[radial-gradient(circle_at_top_right,rgba(134,192,255,0.18),transparent_24%),linear-gradient(180deg,rgba(8,18,35,0.98),rgba(7,15,30,0.98))] p-4 sm:p-5 md:p-6 shadow-[0_20px_56px_rgba(2,8,20,0.46),0_0_42px_rgba(90,160,255,0.12)] space-y-4">
        <div>
          <p className="text-[10px] sm:text-[11px] md:text-[12px] text-[#86c0ff] uppercase tracking-[0.14em] sm:tracking-[0.18em]">
            Saldo em conta
          </p>
          <p className="mt-2 text-[2.4rem] sm:text-5xl md:text-6xl font-bold text-[#f4f8ff] leading-[0.95]">
            {saldoDisplay}
          </p>
          <p className="mt-2 text-[12px] md:text-[13px] text-[#bfd0ec]">
            {saldoModo === "real"
              ? "Disponível para movimentar agora."
              : "Prévia visual enquanto a conta roda em modo demonstração."}
          </p>
            {saldoModo === "real" && saldoUpdatedHHMM && (
              <p className="mt-1 text-[10px] md:text-[11px] text-[#8fa8cf]">
                Atualizado às {saldoUpdatedHHMM}
              </p>
            )}
        </div>

        <div className="w-full">
          <div className="mb-3 flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.14em] sm:tracking-[0.24em] text-[#86c0ff]">
                Ações rápidas
              </p>
              <h3 className="mt-1 text-lg md:text-xl font-bold text-[#f4f8ff]">
                Mover dinheiro
              </h3>
            </div>
            <span className="inline-flex items-center rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-[10px] text-[#86c0ff]">
              Pix
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 sm:gap-2.5">
            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("enviar") : handlePixShortcutFallback("enviar"))}
              className="ag-card rounded-[20px] px-2.5 py-2.5 sm:px-3 sm:py-3 min-h-[96px] sm:min-h-[112px] flex flex-col justify-between text-left border border-sky-500/20 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/12 text-emerald-300 text-xl">
                ↑
              </span>
              <div className="flex flex-col gap-0.5">
                <span className="text-[12px] sm:text-[13px] font-bold text-[#f4f8ff]">Enviar</span>
                <span className="text-[10px] sm:text-[11px] text-[#bfd0ec]">PIX</span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("receber") : handlePixShortcutFallback("receber"))}
              className="ag-card rounded-[20px] px-2.5 py-2.5 sm:px-3 sm:py-3 min-h-[112px] flex flex-col justify-between text-left border border-sky-500/20 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-sky-500/12 text-sky-300 text-xl">
                ↓
              </span>
              <div className="flex flex-col gap-0.5">
                <span className="text-[12px] sm:text-[13px] font-bold text-[#f4f8ff]">Receber</span>
                <span className="text-[10px] sm:text-[11px] text-[#bfd0ec]">Cobrar</span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("extrato") : handlePixShortcutFallback("extrato"))}
              className="ag-card rounded-[20px] px-2.5 py-2.5 sm:px-3 sm:py-3 min-h-[112px] flex flex-col justify-between text-left border border-sky-500/20 bg-[linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))]"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-sky-500/12 text-sky-300 text-xl">
                ≡
              </span>
              <div className="flex flex-col gap-0.5">
                <span className="text-[12px] sm:text-[13px] font-bold text-[#f4f8ff]">Extrato</span>
                <span className="text-[10px] sm:text-[11px] text-[#bfd0ec]">Histórico</span>
              </div>
            </button>
          </div>
        </div>

        <div className="rounded-[24px] border border-sky-500/28 bg-[linear-gradient(180deg,rgba(10,20,40,0.96),rgba(7,15,30,0.98))] p-4 md:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-[10px] sm:text-[11px] md:text-[12px] text-[#86c0ff] uppercase tracking-[0.14em] sm:tracking-[0.18em]">
                Previsão do mês • IA 3.0
              </p>
              <p className="mt-2 text-sm text-[#f4f8ff]">
                Risco atual:&nbsp;
                <span className="font-semibold text-white">
                  {forecastNivel === "critico" && "Crítico"}
                  {forecastNivel === "atencao" && "Atenção"}
                  {forecastNivel === "observacao" && "Observação"}
                  {forecastNivel === "ok" && "Tranquilo"}
                  {!forecastNivel && "—"}
                </span>
              </p>
            </div>

            <div className="text-left sm:text-right w-full sm:w-auto">
              <p className="text-[10px] uppercase tracking-[0.16em] text-[#8fa8cf]">
                Projeção final
              </p>
              <p className="mt-1 text-sm font-semibold text-[#f4f8ff]">
                {forecastPrevisaoFimMes !== null
                  ? forecastPrevisaoFimMes.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
                  : "Carregando..."}
              </p>
            </div>
          </div>

          <p className="mt-3 text-[10px] sm:text-[11px] text-[#bfd0ec]">
            Leitura baseada no histórico PIX do mês.
          </p>
        </div>

{/* ===== RESUMO FINANCEIRO PREMIUM ===== */}
      </div>
      <div className="ag-hero px-4 py-4 sm:px-5 sm:py-5 mb-6 space-y-4 rounded-[28px] border border-sky-500/30 bg-[radial-gradient(circle_at_top_right,rgba(134,192,255,0.16),transparent_20%),radial-gradient(circle_at_bottom_left,rgba(47,111,203,0.16),transparent_28%),linear-gradient(180deg,rgba(10,20,40,0.98),rgba(7,15,30,0.98))] shadow-[0_26px_58px_rgba(2,8,20,0.46),0_0_48px_rgba(90,160,255,0.16)]">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <p className="text-[10px] md:text-[11px] text-sky-200/80 uppercase tracking-[0.16em]">
              Resumo financeiro do mês
            </p>
            <p className="text-sm md:text-base text-[#f4f8ff]">
              Entradas, saídas e resultado do mês em uma leitura rápida.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-sky-400/60 bg-sky-500/10 px-3 py-1 text-[10px] text-sky-200">
            Base operacional • leitura protegida
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-[11px]">
          <div className="ag-card px-4 py-3 border border-[rgba(96,214,159,0.28)] bg-[radial-gradient(circle_at_top_right,rgba(96,214,159,0.10),transparent_26%),linear-gradient(180deg,rgba(25,32,18,0.96),rgba(11,14,10,0.98))] shadow-[0_14px_28px_rgba(0,0,0,0.30)]">
            <p className="text-[10px] text-emerald-200/90 uppercase tracking-[0.14em]">
              Entradas no mês
            </p>
            <p className="mt-1 text-lg font-semibold text-emerald-300">
              {entradasMes !== null ? formatBRL(entradasMes) : "R$ 8.500,00"}
            </p>
            <p className="mt-1 text-[10px] text-emerald-100/80">
              Entradas confirmadas no período.
            </p>
          </div>

          <div className="ag-card px-4 py-3 border border-[rgba(255,123,143,0.28)] bg-[radial-gradient(circle_at_top_right,rgba(255,123,143,0.10),transparent_26%),linear-gradient(180deg,rgba(38,18,18,0.96),rgba(15,9,9,0.98))] shadow-[0_14px_28px_rgba(0,0,0,0.30)]">
            <p className="text-[10px] text-red-200/90 uppercase tracking-[0.14em]">
              Saídas no mês
            </p>
            <p className="mt-1 text-lg font-semibold text-red-300">
              {saidasMes !== null ? formatBRL(saidasMes) : "R$ 6.200,00"}
            </p>
            <p className="mt-1 text-[10px] text-red-100/80">
              Saídas efetivas registradas.
            </p>
          </div>

          <div className="col-span-2 md:col-span-1 ag-card px-4 py-3 flex flex-col justify-between border border-sky-500/28 bg-[radial-gradient(circle_at_top_right,rgba(134,192,255,0.12),transparent_24%),linear-gradient(180deg,rgba(12,24,46,0.96),rgba(7,15,30,0.98))] shadow-[0_14px_28px_rgba(0,0,0,0.30)]">
            <p className="text-[10px] text-sky-200/90 uppercase tracking-[0.14em]">
              Resultado do mês
            </p>
            <p className="mt-1 text-lg font-semibold">
              {resultadoMes !== null ? (
                <span className={resultadoClass}>
                  {formatBRL(resultadoMes)} ({resultadoLabel})
                </span>
              ) : (
                <span className="text-[#f4f8ff]">
                  R$ 2.300,00 (simulação)
                </span>
              )}
            </p>
            <p className="mt-1 text-[10px] sm:text-[11px] text-[#bfd0ec]">
              Saldo líquido consolidado do período.
            </p>
          </div>
        </div>

        <div className="mt-2 flex flex-col md:flex-row md:items-center md:justify-between gap-2 text-[10px] text-[#bfd0ec]">
          <div>
            <span className="uppercase tracking-[0.16em] text-sky-300">
              Plano Essencial
            </span>
            <span className="ml-1 text-[#bfd0ec]">
              {" "}
              — Recursos avançados ficam nos planos Pro, Gold e Empresarial.
            </span>
          </div>
          <button
            type="button"
            onClick={() => (window.location.href = "/planos")}
            className="inline-flex items-center justify-center rounded-full border border-sky-400/70 bg-sky-500/10 px-3 py-1 text-[10px] text-sky-100 hover:bg-sky-400/10 active:scale-[0.97] transition"
          >
            Explorar planos
          </button>
        </div>
      </div>


      {/* Conta em foco */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-5">
        <div className="rounded-2xl border border-sky-500/24 bg-[linear-gradient(180deg,rgba(10,20,40,0.96),rgba(7,15,30,0.98))] p-4 md:p-5">
          <p className="text-[10px] uppercase tracking-[0.16em] text-amber-200/80">
            Conta em foco
          </p>
          <h3 className="mt-2 text-[1.35rem] sm:text-lg md:text-xl font-bold text-[#f4f8ff]">
            Visão rápida da sua carteira
          </h3>

          <div className="mt-4 space-y-2.5 text-[11px]">
            <div className="flex items-center justify-between rounded-xl border border-sky-500/16 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] px-3 py-2.5">
              <span className="text-[#bfd0ec]">Status da conta</span>
              <span className={`font-medium ${saldoModo === "real" ? "text-emerald-300" : "text-amber-200"}`}>
                {saldoModo === "real" ? "Conectada" : "Demonstração"}
              </span>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-[rgba(247,217,142,0.14)] bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgba(255,255,255,0.015))] px-3 py-2.5">
              <span className="text-[#bfd0ec]">Resultado do mês</span>
              <span className={`font-medium ${resultadoMes !== null ? resultadoClass : "text-[#f4f8ff]"}`}>
                {resultadoMes !== null ? formatBRL(resultadoMes) : "R$ 0,00"}
              </span>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-[rgba(247,217,142,0.14)] bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgba(255,255,255,0.015))] px-3 py-2.5">
              <span className="text-[#bfd0ec]">Projeção final</span>
              <span className="font-medium text-[#f4f8ff]">
                {forecastPrevisaoFimMes !== null ? formatBRL(forecastPrevisaoFimMes) : "Carregando..."}
              </span>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-[rgba(247,217,142,0.14)] bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgba(255,255,255,0.015))] px-3 py-2.5">
              <span className="text-[#bfd0ec]">Leitura IA 3.0</span>
              <span className="font-semibold text-[#86c0ff]">
                {forecastNivel === "critico" && "Crítico"}
                {forecastNivel === "atencao" && "Atenção"}
                {forecastNivel === "observacao" && "Observação"}
                {forecastNivel === "ok" && "Tranquilo"}
                {!forecastNivel && "Em análise"}
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-sky-500/24 bg-[linear-gradient(180deg,rgba(10,20,40,0.96),rgba(7,15,30,0.98))] p-4 md:p-5">
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.16em] text-amber-200/80">
                Acessos úteis
              </p>
              <h3 className="mt-2 text-lg md:text-xl font-bold text-[#f4f8ff]">
                Continue sua operação
              </h3>
            </div>

            <button
              type="button"
              onClick={handleHomeInsight}
              disabled={pixInsightLoading}
              className="inline-flex items-center justify-center rounded-full border border-sky-400/50 bg-[linear-gradient(135deg,#5aa0ff,#86c0ff)] px-3 py-1.5 text-[11px] font-semibold text-[#06101f] shadow-[0_12px_24px_rgba(2,8,20,0.26)] hover:brightness-110 disabled:opacity-60"
            >
              {pixInsightLoading ? "Lendo..." : "Gerar insight"}
            </button>
          </div>

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("extrato") : handlePixShortcutFallback("extrato"))}
              className="ag-card rounded-[18px] px-3 py-3 min-h-[88px] text-left"
            >
              <span className="block text-[12px] sm:text-[13px] font-bold text-[#f4f8ff]">Extrato PIX</span>
              <span className="mt-1 block text-[10px] sm:text-[11px] text-[#bfd0ec]">Histórico da conta</span>
            </button>

            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("receber") : handlePixShortcutFallback("receber"))}
              className="ag-card rounded-[18px] px-3 py-3 min-h-[88px] text-left"
            >
              <span className="block text-[12px] sm:text-[13px] font-bold text-[#f4f8ff]">Cobrar</span>
              <span className="mt-1 block text-[10px] sm:text-[11px] text-[#bfd0ec]">QR Code e cobrança</span>
            </button>

            <button
              type="button"
              onClick={() => (window.location.href = "/planos")}
              className="ag-card rounded-[18px] px-3 py-3 min-h-[88px] text-left"
            >
              <span className="block text-[12px] sm:text-[13px] font-bold text-[#f4f8ff]">Planos</span>
              <span className="mt-1 block text-[10px] sm:text-[11px] text-[#bfd0ec]">Ver upgrades</span>
            </button>

            <button
              type="button"
              onClick={() => (onPixShortcut ? onPixShortcut("enviar") : handlePixShortcutFallback("enviar"))}
              className="ag-card rounded-[18px] px-3 py-3 min-h-[88px] text-left"
            >
              <span className="block text-[12px] sm:text-[13px] font-bold text-[#f4f8ff]">Enviar PIX</span>
              <span className="mt-1 block text-[10px] sm:text-[11px] text-[#bfd0ec]">Transferir agora</span>
            </button>
          </div>

          <div className="mt-4 rounded-xl border border-sky-500/16 bg-[rgba(10,20,40,0.58)] px-3 py-3">
            {pixInsightError ? (
              <p className="text-[11px] text-rose-300">{pixInsightError}</p>
            ) : pixInsight ? (
              <p className="text-[13px] text-[#f4f8ff] whitespace-pre-line">{pixInsight}</p>
            ) : (
              <p className="text-[12px] text-[#bfd0ec]">
                A home agora fica focada em conta. PIX detalhado, gestão e módulos profundos ficam nas outras abas.
              </p>
            )}
          </div>
        </div>
      </div>


      {/* PIX Modals */}
      {pixSendOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-2xl border border-amber-500/40 bg-zinc-950 p-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-amber-200">Enviar PIX</h3>
              <button
                className="text-[#bfd0ec] hover:text-zinc-200 text-sm"
                onClick={() => { setPixSendOpen(false); setPixSendErr(null); setPixSendOk(null); }}
              >
                Fechar
              </button>
            </div>

            <div className="mt-3 space-y-2">
              <input
                className="w-full rounded-xl bg-black/40 border border-zinc-700 px-3 py-2 text-sm text-[#f4f8ff] placeholder:text-zinc-600"
                placeholder="Destino (chave PIX / conta)"
                value={pixSendDest}
                onChange={(e) => setPixSendDest(e.target.value)}
              />
              <input
                className="w-full rounded-xl bg-black/40 border border-zinc-700 px-3 py-2 text-sm text-[#f4f8ff] placeholder:text-zinc-600"
                placeholder="Valor (ex: 10,50)"
                value={pixSendValor}
                onChange={(e) => setPixSendValor(e.target.value)}
                inputMode="decimal"
              />
              <input
                className="w-full rounded-xl bg-black/40 border border-zinc-700 px-3 py-2 text-sm text-[#f4f8ff] placeholder:text-zinc-600"
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
                className="text-[#bfd0ec] hover:text-zinc-200 text-sm"
                onClick={() => { setPixExtratoOpen(false); setPixExtratoErr(null); }}
              >
                Fechar
              </button>
            </div>

            {pixExtratoBusy && <p className="mt-3 text-xs text-[#bfd0ec]">Carregando...</p>}
            {pixExtratoErr && <p className="mt-3 text-xs text-red-300">{pixExtratoErr}</p>}

            {!pixExtratoBusy && !pixExtratoErr && (
              <div className="mt-3 max-h-[70vh] overflow-auto space-y-2">
                {(pixExtratoItems || []).length === 0 ? (
                  <p className="text-xs text-[#bfd0ec]">Sem movimentações (ainda).</p>
                ) : (
                  (pixExtratoItems || []).map((it) => (
                    <div key={it.id} className="flex items-start justify-between gap-3 border-b border-zinc-800/70 pb-2">
                      <div className="min-w-0">
                        <p className="text-xs text-zinc-200">
                          <span className="text-[#bfd0ec]">#{it.id}</span> • {String(it.tipo || "").toUpperCase()}
                        </p>
                        {it.descricao && <p className="text-[12px] text-[#efe4cf] truncate">{it.descricao}</p>}
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

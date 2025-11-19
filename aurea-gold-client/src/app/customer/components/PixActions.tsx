import React from "react";
import { USER_EMAIL } from "@/lib/api";
import { sendQuickPix } from "@/services/pix";
import "./pix-panel.css";

const isDev = import.meta.env.DEV;

const brl = (v: number = 0) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);

function parseValor(input?: string): number | null {
  if (!input) return null;
  const n = parseFloat(String(input).trim().replace(/\./g, "").replace(",", "."));
  if (!Number.isFinite(n) || n <= 0) return null;
  return Math.round(n * 100) / 100;
}

function sanitizeDest(s?: string): string {
  return (s ?? "").trim();
}

export default function PixActions() {
  const [sending, setSending] = React.useState(false);

  const onSend = async () => {
    if (!isDev) {
      alert("Envio desabilitado em produção. Use ambiente de desenvolvimento.");
      return;
    }
    if (sending) return;

    // 1) pedir chave PIX (destino) – lembra último
    const lastDest = localStorage.getItem("pix:lastDest") || USER_EMAIL || "";
    const destIn = window.prompt("Chave PIX do destinatário (e-mail/CPF/CNPJ/Aleatória):", lastDest);
    const dest = sanitizeDest(destIn ?? undefined);
    if (!dest || dest.length < 5) {
      alert("Chave PIX inválida.");
      return;
    }

    // 2) pedir valor
    const valorStr = window.prompt("Valor do PIX (ex: 10,00)", "10,00");
    const valor = parseValor(valorStr ?? "");
    if (valor == null) {
      alert("Valor inválido.");
      return;
    }

    // 3) pedir motivo/descrição – lembra último
    const lastMsg = localStorage.getItem("pix:lastMsg") || "Teste via Aurea";
    const msgIn = window.prompt("Motivo/Descrição do PIX:", lastMsg) ?? "";
    const msg = msgIn.trim();
    if (!msg) {
      alert("Descrição obrigatória.");
      return;
    }

    // 4) confirmação
    const ok = window.confirm(
      `Confirmar envio?\nDestinatário: ${dest}\nValor: ${brl(valor)}\nDescrição: "${msg}"`
    );
    if (!ok) return;

    setSending(true);
    try {
      await sendQuickPix({ dest, valor, msg });
      // memoriza últimos usados
      localStorage.setItem("pix:lastDest", dest);
      localStorage.setItem("pix:lastMsg", msg);

      // notifica quem escuta e feedback
      window.dispatchEvent(new CustomEvent("aurea:pix:sent"));
      alert("AUREA • PIX enviado!");
    } catch (e) {
      console.error("AUREA • falha ao enviar PIX", e);
      alert("× Falha ao enviar PIX (veja o console).");
    } finally {
      setSending(false);
    }
  };

  const onClear = () => {
    try {
      const rows = document.querySelectorAll("tbody tr");
      rows.forEach((r) => ((r as HTMLElement).style.display = "none"));
      const msg = document.createElement("div");
      msg.className = "pix-empty-hint";
      msg.textContent = "Sem dados suficientes para o gráfico";
      document.querySelector(".pix-list")?.appendChild(msg);
      setTimeout(() => msg.remove(), 1500);
    } catch {}
  };

  return (
    <div className="pix-actions" data-aurea="pix-actions">
      <button
        className="btn-gold"
        onClick={onSend}
        disabled={sending || !isDev}
        title={isDev ? "" : "Desabilitado fora do ambiente de desenvolvimento"}
      >
      </button>
    </div>
  );
}

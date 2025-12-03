import React from "react";
import { IaHeadlineLab } from "./IaHeadlineLab";
import AureaAIChat from "./AureaAIChat";
import AureaPixChart from "./AureaPixChart";

function handlePixShortcut(action: "enviar" | "receber" | "extrato") {
  console.log(`[SuperAureaHome] Atalho PIX clicado: ${action}`);
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
  | "informe_rendimentos";

function handleServiceShortcut(service: AureaServiceKey) {
  console.log(`[SuperAureaHome] Atalho de serviço clicado: ${service}`);
  alert(
    "Funcionalidade em construção.\n\n" +
      "Esta área do Aurea Gold vai ser ligada a fluxos reais (ex.: empréstimos, cartões, investimentos, cofrinhos, etc.).\n" +
      "Por enquanto, ela está aqui como protótipo visual do aplicativo oficial."
  );
}

export default function SuperAureaHome() {
  return (
    <section className="w-full max-w-5xl mx-auto space-y-4 md:space-y-6">
      {/* Card de saldo principal */}
      <div className="rounded-2xl border border-amber-500/60 bg-gradient-to-br from-black via-zinc-950 to-zinc-900 p-4 md:p-6 shadow-[0_0_40px_rgba(251,191,36,0.18)] flex flex-col md:flex-row justify-between gap-4">
        <div>
          <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.18em]">
            Saldo disponível • Aurea Gold
          </p>
          <p className="mt-1 text-3xl md:text-4xl font-semibold text-amber-300">
            R$ 12.345,67
          </p>
          <p className="mt-1 text-[10px] md:text-[11px] text-zinc-400">
            Valor simulado por enquanto. Na versão conectada, esse saldo vem em
            tempo real do seu Aurea Gold.
          </p>
        </div>

        {/* Atalhos rápidos PIX */}
        <div className="flex flex-col gap-2 text-[10px] md:text-[11px] min-w-[190px]">
          <p className="text-[10px] text-zinc-400 uppercase tracking-[0.16em]">
            Atalhos rápidos PIX
          </p>
          <button
            type="button"
            onClick={() => handlePixShortcut("enviar")}
            className="px-3 py-1.5 rounded-lg border border-emerald-500/70 bg-emerald-900/60 text-emerald-50 text-left text-[11px] hover:border-emerald-300/80 active:scale-[0.98] transition"
          >
            Enviar PIX
            <span className="block text-[9px] text-emerald-100/80">
              Atalho para envio rápido de PIX
            </span>
          </button>
          <button
            type="button"
            onClick={() => handlePixShortcut("receber")}
            className="px-3 py-1.5 rounded-lg border border-amber-500/80 bg-black/60 text-amber-100 text-left text-[11px] hover:border-amber-300/90 active:scale-[0.98] transition"
          >
            Receber PIX
            <span className="block text-[9px] text-amber-100/80">
              Copiar chave ou gerar QR Code (em breve)
            </span>
          </button>
          <button
            type="button"
            onClick={() => handlePixShortcut("extrato")}
            className="px-3 py-1.5 rounded-lg border border-zinc-600/80 bg-zinc-900/80 text-zinc-100 text-left text-[11px] hover:border-amber-400/80 active:scale-[0.98] transition"
          >
            Ver extrato PIX
            <span className="block text-[9px] text-zinc-300/80">
              Acessar histórico detalhado do mês
            </span>
          </button>
        </div>
      </div>

      {/* Resumo rápido do mês */}
      <div className="rounded-2xl border border-amber-500/40 bg-gradient-to-br from-zinc-950 via-black to-zinc-950 p-4 md:p-5 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.16em]">
              Resumo rápido do mês
            </p>
            <p className="text-sm md:text-base text-zinc-100">
              Visão geral das entradas e saídas do seu Aurea Gold.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-amber-400/70 bg-black/70 px-3 py-1 text-[10px] text-amber-200">
            Modo LAB • Dados simulados
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-[11px]">
          <div className="rounded-xl border border-emerald-500/50 bg-emerald-900/30 px-3 py-2">
            <p className="text-[10px] text-emerald-200/90 uppercase tracking-[0.14em]">
              Entradas no mês
            </p>
            <p className="mt-1 text-lg font-semibold text-emerald-300">
              R$ 8.500,00
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
              R$ 6.200,00
            </p>
            <p className="mt-1 text-[10px] text-red-100/80">
              Pagamentos, transferências e débitos recorrentes.
            </p>
          </div>

          <div className="col-span-2 md:col-span-1 rounded-xl border border-amber-500/50 bg-black/60 px-3 py-2 flex flex-col justify-between">
            <p className="text-[10px] text-amber-200/90 uppercase tracking-[0.14em]">
              Destaque do mês
            </p>
            <p className="mt-1 text-[11px] text-zinc-100">
              Você está gastando{" "}
              <span className="text-emerald-300 font-semibold">
                menos que o mês passado
              </span>{" "}
              (simulação). Bom sinal para manter sua estratégia de reservas.
            </p>
          </div>
        </div>
      </div>

      {/* PIX • Visão rápida (LAB) */}
      <div className="rounded-2xl border border-emerald-500/50 bg-gradient-to-br from-black via-zinc-950 to-black p-4 md:p-5 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <p className="text-[10px] md:text-[11px] text-emerald-200/80 uppercase tracking-[0.16em]">
              PIX • Visão rápida (LAB)
            </p>
            <p className="text-[11px] md:text-sm text-zinc-200">
              Gráfico resumindo as movimentações recentes de PIX. Nesta versão, usamos o
              endpoint de laboratório para testar o comportamento visual.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/70 bg-black/70 px-3 py-1 text-[10px] text-emerald-200">
            /api/v1/pix/7d • Somente leitura
          </span>
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
          <button
            type="button"
            onClick={() => handleServiceShortcut("negocios")}
            className="flex flex-col items-start gap-0.5 rounded-xl border border-amber-500/50 bg-zinc-950 px-3 py-2 hover:border-amber-300/80 active:scale-[0.98] transition"
          >
            <span className="font-semibold text-amber-200">Negócios</span>
            <span className="text-[9px] text-zinc-400">
              Conta para MEI, PJ e empreendedores.
            </span>
          </button>
          {/* ... (resto dos botões de serviços, idênticos à versão anterior) ... */}
        </div>
      </div>

      {/* Bloco IA 3.0: Headline + Chat */}
      <div className="grid md:grid-cols-2 gap-4 md:gap-6">
        {/* Headline executiva */}
        <div className="rounded-2xl border border-amber-500/40 bg-zinc-950/90 p-3 md:p-4">
          <p className="text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.16em] mb-2">
            IA 3.0 • Headline executiva (LAB)
          </p>
          <p className="text-[11px] text-zinc-300 mb-3">
            Resumo automático do seu painel Aurea Gold. Nesta versão LAB, os dados ainda
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
    </section>
  );
}

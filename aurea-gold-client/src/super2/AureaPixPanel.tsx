import React, { useState } from "react";

/**
 * AureaPixPanel
 *
 * Painel oficial de PIX do aplicativo Aurea Gold.
 * Aqui vamos, aos poucos, plugar:
 *  - saldo PIX
 *  - entradas / saídas
 *  - gráficos
 *  - atalhos de envio e cobrança
 */
type PixAction = "send" | "charge" | "statement" | null;

export default function AureaPixPanel() {
  const [activeAction, setActiveAction] = useState<PixAction>(null);

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
        <div className="h-px w-32 bg-amber-500 mt-3" />
      </header>

      {/* CARDS PRINCIPAIS */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-4">
        <div className="rounded-xl border border-amber-500/40 bg-zinc-950/80 p-3">
          <div className="text-[10px] uppercase tracking-wide text-zinc-400 mb-1">
            Saldo PIX
          </div>
          <div className="text-2xl font-semibold text-amber-300">
            R$ 0,00
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">
            Em breve, esse valor será carregado diretamente do backend Aurea
            Gold, mostrando o saldo em tempo real.
          </p>
        </div>

        <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-emerald-300 mb-1">
            Entradas do mês
          </div>
          <div className="text-lg font-semibold text-emerald-300">
            R$ 0,00
          </div>
          <p className="text-[11px] text-emerald-200/80 mt-1">
            Aqui vamos exibir o total de PIX recebidos no mês atual.
          </p>
        </div>

        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-3">
          <div className="text-[10px] uppercase tracking-wide text-rose-300 mb-1">
            Saídas do mês
          </div>
          <div className="text-lg font-semibold text-rose-300">
            R$ 0,00
          </div>
          <p className="text-[11px] text-rose-200/80 mt-1">
            Aqui vamos exibir o total de PIX enviados no mês atual.
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
            <>
              <h3 className="font-semibold text-amber-300 mb-1">
                Enviar PIX (modo LAB)
              </h3>
              <p className="text-zinc-300 mb-1">
                Esta será a tela onde o cliente informa:
              </p>
              <ul className="list-disc list-inside text-zinc-300 space-y-1">
                <li>destinatário (chave, conta ou contato salvo);</li>
                <li>valor do PIX;</li>
                <li>descrição opcional;</li>
                <li>confirmação antes de enviar.</li>
              </ul>
              <p className="text-zinc-400 mt-2">
                Por enquanto estamos em modo visual. Na próxima etapa, vamos
                conectar com o backend do Aurea Gold e registrar o PIX real.
              </p>
            </>
          )}

          {activeAction === "charge" && (
            <>
              <h3 className="font-semibold text-amber-300 mb-1">
                Cobrar via PIX (modo LAB)
              </h3>
              <p className="text-zinc-300 mb-1">
                Aqui o cliente vai poder gerar cobranças PIX:
              </p>
              <ul className="list-disc list-inside text-zinc-300 space-y-1">
                <li>definir valor da cobrança;</li>
                <li>informar descrição/identificador;</li>
                <li>gerar QR Code ou link de pagamento;</li>
                <li>acompanhar se a cobrança foi paga.</li>
              </ul>
              <p className="text-zinc-400 mt-2">
                Tudo isso ficará registrado no histórico financeiro do Aurea
                Gold, integrado à IA 3.0 para avisos e resumos.
              </p>
            </>
          )}

          {activeAction === "statement" && (
            <>
              <h3 className="font-semibold text-amber-300 mb-1">
                Extrato PIX (modo LAB)
              </h3>
              <p className="text-zinc-300 mb-1">
                Esta área será o extrato rápido do PIX dentro do app:
              </p>
              <ul className="list-disc list-inside text-zinc-300 space-y-1">
                <li>lista de envios e recebimentos;</li>
                <li>filtros por período e tipo de transação;</li>
                <li>integração com a IA 3.0 para explicar o movimento;</li>
                <li>atalho direto para abrir detalhes na IA.</li>
              </ul>
              <p className="text-zinc-400 mt-2">
                Na próxima fase, vamos puxar esses dados direto do backend e
                cruzar com o painel IA 3.0.
              </p>
            </>
          )}
        </div>
      </section>

      {/* AVISO LAB */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
        <div className="text-[11px] font-semibold text-zinc-200 mb-1">
          Modo LAB ativado
        </div>
        <p className="text-[11px] text-zinc-400">
          Essa tela ainda está em modo laboratório. Os dados estão estáticos,
          servindo como guia visual. Na próxima fase, vamos plugar o backend
          de PIX e a IA 3.0 para análise automática dos movimentos.
        </p>
      </section>
    </div>
  );
}

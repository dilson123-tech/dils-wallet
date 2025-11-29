import React, { useState } from "react";
import { fetchPagamentosAI } from "./api";

export default function PanelPagamentos() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk(ev: React.FormEvent) {
    ev.preventDefault();
    const msg = message.trim() || "tenho risco de atrasar alguma conta?";

    try {
      setLoading(true);
      setError(null);
      const data = await fetchPagamentosAI(msg);
      setReply(data.reply);
    } catch (err: any) {
      console.error(err);
      setError("Não consegui falar com a IA de Pagamentos agora. Tente novamente em instantes.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-black text-zinc-100 flex justify-center px-4 py-6">
      <div className="w-full max-w-md border border-zinc-700 bg-zinc-950/95 rounded-2xl p-4 shadow-lg">
        <header className="mb-3">
          <h1 className="text-xl font-semibold tracking-wide text-[#f4d247]">
            Painel de Pagamentos
          </h1>
          <p className="text-[11px] text-zinc-300 mt-1">
            Visão centralizada das suas contas fixas, boletos e assinaturas.
          </p>
        </header>

        {/* Modo planejamento / dados exemplo */}
        <section className="text-[11px] leading-snug">
          <div className="uppercase text-[9px] tracking-wide text-zinc-400 mb-1">
            Modo planejamento <span className="text-[8px]">(versão inicial · dados de exemplo)</span>
          </div>

          <div className="border border-zinc-600 rounded-md overflow-hidden mb-2">
            <div className="bg-zinc-900/80 px-2 py-1 border-b border-zinc-700 text-[10px] font-semibold">
              Resumo de contas do mês
            </div>
            <div className="px-2 py-1 grid grid-cols-2 gap-y-[2px] text-[10px]">
              <div>Total de contas</div>
              <div className="text-right font-semibold">R$ 1.250,00</div>
              <div>Pagos no mês</div>
              <div className="text-right text-green-400">R$ 820,00</div>
              <div>Quantidade de contas</div>
              <div className="text-right">14 itens</div>
              <div>Restante a pagar</div>
              <div className="text-right text-amber-300">R$ 430,00</div>
              <div className="col-span-2 text-[9px] text-zinc-400 mt-1">
                Valor aproximado que ainda precisa sair da sua carteira.
              </div>
            </div>
          </div>

          {/* Vencimentos organizados */}
          <div className="border border-zinc-600 rounded-md overflow-hidden mb-2">
            <div className="bg-zinc-900/80 px-2 py-1 border-b border-zinc-700 text-[10px] font-semibold">
              Vencimentos organizados
            </div>
            <div className="px-2 py-1 text-[10px] space-y-[2px]">
              <div className="font-semibold text-zinc-200 mt-1">Hoje</div>
              <div className="flex justify-between">
                <span>Luz Copel · conta fixa</span>
                <span>R$ 220,90</span>
              </div>

              <div className="font-semibold text-zinc-200 mt-2">Próximos 7 dias</div>
              <div className="flex justify-between">
                <span>Aluguel · conta fixa</span>
                <span>R$ 950,00</span>
              </div>

              <div className="font-semibold text-zinc-200 mt-2">Este mês</div>
              <div className="flex justify-between">
                <span>Netflix · assinatura</span>
                <span>R$ 39,90</span>
              </div>
              <div className="flex justify-between">
                <span>Internet Fibra · assinatura</span>
                <span>R$ 119,90</span>
              </div>
            </div>
          </div>

          {/* Contas cadastradas */}
          <div className="border border-zinc-600 rounded-md overflow-hidden mb-3">
            <div className="bg-zinc-900/80 px-2 py-1 border-b border-zinc-700 text-[10px] font-semibold">
              Contas cadastradas
            </div>
            <div className="px-2 py-1 text-[10px] space-y-[2px]">
              <div>Luz Copel — todo dia 05 · R$ 220,90</div>
              <div>Aluguel — todo dia 10 · R$ 950,00</div>
              <div>Netflix — dia 18 · R$ 39,90</div>
              <div>Internet Fibra — dia 22 · R$ 119,90</div>
              <div className="text-[9px] text-zinc-400 mt-1">
                Nesta primeira versão, os dados são apenas demonstrativos. Em breve,
                este painel será alimentado pelas suas contas reais cadastradas no
                backend da Aurea Gold.
              </div>
            </div>
          </div>
        </section>

        {/* IA 3.0 – Consultor de contas */}
        <section className="border border-amber-500/70 rounded-md bg-black/70 px-2 py-2">
          <div className="flex items-center justify-between mb-1">
            <div className="text-[10px] font-semibold text-amber-300">
              IA 3.0 · Consultor de contas
            </div>
            <span className="text-[8px] px-2 py-[1px] rounded-full border border-amber-400/70 text-amber-200">
              LAB · explicativo
            </span>
          </div>

          <p className="text-[10px] text-zinc-200 mb-2">
            Aqui é onde a IA vai olhar para as suas contas, vencimentos e saldo da
            Carteira PIX para avisar se existe risco de atraso e qual a melhor ordem
            para pagamento antes de estourar a fatura.
          </p>

          <form onSubmit={handleAsk} className="space-y-1">
            <textarea
              rows={2}
              className="w-full text-[10px] rounded-md border border-zinc-700 bg-zinc-950/80 px-2 py-1 outline-none focus:border-amber-400 resize-none"
              placeholder="Ex.: 'tenho risco de atrasar alguma conta?' ou 'quais contas faz sentido pagar hoje?'"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <div className="flex justify-between items-center gap-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 text-[10px] font-semibold rounded-md bg-amber-400 text-black py-1 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? "Analisando..." : "Perguntar para a IA 3.0"}
              </button>
              <button
                type="button"
                className="px-2 py-1 text-[9px] rounded-md border border-zinc-600 text-zinc-300"
                onClick={() => {
                  setMessage("");
                  setReply(null);
                  setError(null);
                }}
              >
                Limpar
              </button>
            </div>
          </form>

          {error && (
            <div className="mt-2 text-[10px] text-red-400">
              {error}
            </div>
          )}

          {reply && !error && (
            <div className="mt-2 text-[10px] whitespace-pre-line bg-zinc-900/80 border border-zinc-700 rounded-md px-2 py-2">
              {reply}
            </div>
          )}

          {!reply && !error && (
            <div className="mt-2 text-[9px] text-zinc-400">
              Sugestões rápidas:{" "}
              <span className="italic">
                "tenho risco de atrasar alguma conta?", "quanto vou pagar de contas esta
                semana?", "quais contas faz sentido pagar hoje?".
              </span>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

import React, { useEffect, useMemo, useState } from "react";
import { fetchPixHistory, PixHistoryItem } from "./api";

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

// taxa padrão simulada do Aurea Gold sobre envios de PIX (0,8%)
const TAXA_ENVIO_PADRAO = 0.008;

function formatBRL(value: number): string {
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function AureaPixPanel() {
  const [activeAction, setActiveAction] = useState<PixAction>(null);

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
          arr =
            anyRaw.items ??
            anyRaw.history ??
            anyRaw.data ??
            [];
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

        // usa taxa_valor do backend quando disponível, senão simula
        const taxaValor =
          typeof item.taxa_valor === "number"
            ? item.taxa_valor
            : item.valor * TAXA_ENVIO_PADRAO;

        totalTaxas += taxaValor;
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

      {/* CARDS PRINCIPAIS (ainda estáticos por enquanto) */}
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
                Extrato PIX (modo real + LAB)
              </h3>
              <p className="text-zinc-300 mb-2">
                Aqui você acompanha os envios e recebimentos de PIX e já vê as
                taxas aplicadas e o resultado líquido de cada envio.
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
                <p className="mt-2 text-[10px] text-red-400">
                  {historyError}
                </p>
              )}

              {!historyLoading && !historyError && (
                <>
                  {(!history || history.length === 0) && (
                    <p className="mt-2 text-[10px] text-zinc-400">
                      Ainda não encontramos movimentações de PIX registradas
                      para este usuário. Assim que o backend começar a salvar as
                      transações, elas aparecerão aqui.
                    </p>
                  )}

                  {history && history.length > 0 && (
                    <div className="mt-3 space-y-1 max-h-52 overflow-y-auto pr-1">
                      {history.slice(0, 20).map((item) => {
                        const isEnvio = item.tipo === "envio";

                        // valores vindos do backend, com fallback para simulação
                        const taxaPercent =
                          item.taxa_percentual ?? (isEnvio ? TAXA_ENVIO_PADRAO * 100 : 0);

                        const taxaValor =
                          item.taxa_valor ?? (isEnvio ? item.valor * TAXA_ENVIO_PADRAO : 0);

                        const valorLiquido =
                          item.valor_liquido ?? (isEnvio ? item.valor - taxaValor : item.valor);

                        const created =
                          item.created_at &&
                          new Date(item.created_at).toLocaleString("pt-BR");

                        return (
                          <div
                            key={item.id}
                            className="flex items-start justify-between gap-2 rounded-md border border-zinc-700 bg-zinc-950/80 px-2 py-1"
                          >
                            <div className="flex-1">
                              <div className="text-[10px] text-zinc-300">
                                {isEnvio ? "Envio de PIX" : "PIX recebido"}
                              </div>
                              {item.descricao && (
                                <div className="text-[9px] text-zinc-500">
                                  {item.descricao}
                                </div>
                              )}
                              {created && (
                                <div className="text-[9px] text-zinc-500">
                                  {created}
                                </div>
                              )}
                            </div>
                            <div className="text-right text-[10px]">
                              <div
                                className={
                                  isEnvio
                                    ? "text-rose-300"
                                    : "text-emerald-300"
                                }
                              >
                                {formatBRL(item.valor)}
                              </div>
                              {isEnvio && (
                                <div className="text-[9px] text-amber-300">
                                  {`${taxaPercent.toLocaleString("pt-BR", {
                                    minimumFractionDigits: 1,
                                    maximumFractionDigits: 2,
                                  })}% • ${formatBRL(taxaValor)}`}
                                </div>
                              )}

                              {typeof valorLiquido === "number" && (
                                <div className="text-[9px] text-zinc-400">
                                  Líquido {formatBRL(valorLiquido)}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </>
              )}

              <p className="mt-2 text-[10px] text-zinc-500">
                As taxas mostradas aqui usam, sempre que possível, os valores reais
                salvos pelo backend. Quando alguma transação ainda não tiver taxa
                registrada, aplicamos o modelo padrão de
                {Math.round(TAXA_ENVIO_PADRAO * 1000) / 10}
                % por envio como referência visual. Esses valores podem ser ajustados
                conforme o plano comercial do Aurea Gold para cada cliente.
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
          Parte desta tela (extrato e taxas) já está ligada ao backend. Os
          demais cards ainda estão estáticos, servindo como guia visual. Na
          próxima fase vamos plugar saldo, entradas e saídas em tempo real.
        </p>
      </section>
    </div>
  );
}

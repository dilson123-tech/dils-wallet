import React, { useEffect, useState } from "react";
import { API_BASE, USER_EMAIL } from "./api";
import { IaHeadlineLab } from "./IaHeadlineLab";
import AureaAIChat from "./AureaAIChat";
import AureaPixChart from "./AureaPixChart";

type PixShortcutAction = "enviar" | "receber" | "extrato";

type SuperAureaHomeProps = {
  onPixShortcut?: (action: PixShortcutAction) => void;
};

function handlePixShortcutFallback(action: PixShortcutAction) {
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
  console.log(`[SuperAureaHome] Atalho de serviço clicado: ${service}`);
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
  const [entradasMes, setEntradasMes] = useState<number | null>(null);
  const [saidasMes, setSaidasMes] = useState<number | null>(null);
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
      try {
        // --- 1) Saldo + entradas/saídas via /api/v1/pix/balance ---
        const resp = await fetch(`${API_BASE}/api/v1/pix/balance`, {
          headers: {
            "Content-Type": "application/json",
            "X-User-Email": USER_EMAIL,
          },
        });

        if (resp.ok) {
          const data = await resp.json();

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

          const modoReal = data?.source === "real" ? "real" : "simulado";

          if (alive && saldo !== null) {
            setSaldoReal(saldo);
            setSaldoModo(modoReal);
            setEntradasMes(entradas);
            setSaidasMes(saidas);
          }
        } else {
          console.error(
            "[SuperAureaHome] Falha ao buscar /api/v1/pix/balance:",
            resp.status,
          );
        }

        // --- 2) Forecast PIX ---
        const forecastResp = await fetch(`${API_BASE}/api/v1/pix/forecast`, {
          headers: {
            "Content-Type": "application/json",
            "X-User-Email": USER_EMAIL,
          },
        });

        if (forecastResp.ok) {
          const forecastData = await forecastResp.json();

          if (alive) {
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
          }
        } else {
          console.warn(
            "[SuperAureaHome] Falha ao buscar /api/v1/pix/forecast:",
            forecastResp.status,
          );
        }
      } catch (e) {
        console.error("[SuperAureaHome] Erro geral no loadSaldo():", e);
      }
    }

    loadSaldo();

    return () => {
      alive = false;
    };
  }, []);

  const saldoDisplay =
    saldoModo === "real" ? formatBRL(saldoReal) : "R$ 12.345,67";

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

  return (
    <section className="w-full max-w-5xl mx-auto space-y-4 md:space-y-6">
      {/* Modo de dados (real vs simulado) */}
      <div className="mb-2 text-[10px] md:text-[11px] text-amber-200/80 uppercase tracking-[0.18em]">
        {saldoModo === "real"
          ? "Dados reais carregados do backend Aurea Gold"
          : "Modo simulado • aguardando conexão completa do PIX"}
      </div>

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
                <p className="text-[11px] md:text-xs text-zinc-100 font-semibold mt-1">
                  {forecastPrevisaoFimMes !== null
                    ? forecastPrevisaoFimMes.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
                    : "Carregando previsão do mês..."}
                </p>
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
        <div className="flex flex-col gap-2 text-[10px] md:text-[11px] min-w-[190px]">
          <p className="text-[10px] text-zinc-400 uppercase tracking-[0.16em]">
            Atalhos rápidos PIX
          </p>
          <button
            type="button"
            onClick={() =>
            onPixShortcut
              ? onPixShortcut("enviar")
              : handlePixShortcutFallback("enviar")
          }
            className="px-3 py-1.5 rounded-lg border border-emerald-500/70 bg-emerald-900/60 text-emerald-50 text-left text-[11px] hover:border-emerald-300/80 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            Enviar PIX
            <span className="block text-[9px] text-emerald-100/80">
              Atalho para envio rápido de PIX
            </span>
          </button>
          <button
            type="button"
            onClick={() =>
            onPixShortcut
              ? onPixShortcut("receber")
              : handlePixShortcutFallback("receber")
          }
            className="px-3 py-1.5 rounded-lg border border-amber-500/80 bg-black/60 text-amber-100 text-left text-[11px] hover:border-amber-300/90 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
          >
            Receber PIX
            <span className="block text-[9px] text-amber-100/80">
              Copiar chave ou gerar QR Code (em breve)
            </span>
          </button>
          <button
            type="button"
            onClick={() =>
            onPixShortcut
              ? onPixShortcut("extrato")
              : handlePixShortcutFallback("extrato")
          }
            className="px-3 py-1.5 rounded-lg border border-zinc-600/80 bg-zinc-900/80 text-zinc-100 text-left text-[11px] hover:border-amber-400/80 active:scale-[0.98] hover:shadow-[0_0_12px_rgba(251,191,36,0.45)] transition"
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
            Dados reais • fallback LAB se necessário
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
              Plano atual (LAB): Free
            </span>
            <span className="ml-1 text-zinc-400">
              {" "}
              — IA financeira completa e relatórios avançados ficam nos planos Pro, Gold e Empresarial.
            </span>
          </div>
          <button
            type="button"
            onClick={() => (window.location.href = "/planos-lab")}
            className="inline-flex items-center justify-center rounded-full border border-amber-400/80 px-3 py-1 text-[10px] text-amber-100 hover:bg-amber-400/10 active:scale-[0.97] transition"
          >
            Ver planos e benefícios
          </button>
        </div>
      </div>

      {/* PIX • Visão rápida (LAB) */}
      <div className="rounded-2xl border border-emerald-500/50 bg-gradient-to-br from-black via-zinc-950 to-black p-4 md:p-5 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <p className="text-[10px] md:text-[11px] text-emerald-200/80 uppercase tracking-[0.16em]">
              PIX • Visão rápida
            </p>
            <p className="text-[11px] md:text-sm text-zinc-200">
              Gráfico resumindo as movimentações recentes de PIX. Nesta versão, usamos seus
              dados reais dos últimos 7 dias, com fallback simulado se o servidor estiver indisponível.
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

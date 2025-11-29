import React from "react";

type BillStatus = "pendente" | "pago" | "atrasado";

type Bill = {
  id: number;
  nome: string;
  tipo: "conta fixa" | "assinatura" | "boleto avulso";
  valor: number;
  vencimento: string;
  status: BillStatus;
};

const fmtBRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const mockResumoMes = {
  totalMes: 1250.0,
  pagos: 820.0,
  restante: 430.0,
  risco: "moderado" as "baixo" | "moderado" | "alto",
  contasCriticas: 2,
};

const mockHoje: Bill[] = [
  {
    id: 1,
    nome: "Luz Copel",
    tipo: "conta fixa",
    valor: 220.9,
    vencimento: "Hoje",
    status: "pendente",
  },
];

const mockProximos7: Bill[] = [
  {
    id: 2,
    nome: "Aluguel",
    tipo: "conta fixa",
    valor: 950.0,
    vencimento: "em 3 dias",
    status: "pendente",
  },
];

const mockEsteMes: Bill[] = [
  {
    id: 3,
    nome: "Netflix",
    tipo: "assinatura",
    valor: 39.9,
    vencimento: "dia 18",
    status: "pago",
  },
  {
    id: 4,
    nome: "Internet Fibra",
    tipo: "conta fixa",
    valor: 119.9,
    vencimento: "dia 22",
    status: "pendente",
  },
];

const mockContasCadastradas: Bill[] = [
  {
    id: 1,
    nome: "Luz Copel",
    tipo: "conta fixa",
    valor: 220.9,
    vencimento: "Todo dia 05",
    status: "pendente",
  },
  {
    id: 2,
    nome: "Aluguel",
    tipo: "conta fixa",
    valor: 950.0,
    vencimento: "Todo dia 10",
    status: "pendente",
  },
  {
    id: 3,
    nome: "Netflix",
    tipo: "assinatura",
    valor: 39.9,
    vencimento: "Todo dia 18",
    status: "pago",
  },
  {
    id: 4,
    nome: "Internet Fibra",
    tipo: "conta fixa",
    valor: 119.9,
    vencimento: "Todo dia 22",
    status: "pendente",
  },
];

function statusLabel(status: BillStatus) {
  if (status === "pago") return "Pago";
  if (status === "atrasado") return "Atrasado";
  return "Pendente";
}

function statusClass(status: BillStatus) {
  if (status === "pago") return "text-emerald-300 bg-emerald-900/40 border-emerald-500/40";
  if (status === "atrasado") return "text-red-300 bg-red-900/40 border-red-500/40";
  return "text-amber-300 bg-amber-900/30 border-amber-500/40";
}

function riscoTexto() {
  const { risco, contasCriticas } = mockResumoMes;
  if (risco === "baixo") {
    return "Tudo em dia. Nenhuma conta crítica nos próximos dias.";
  }
  if (risco === "moderado") {
    return `Atenção: ${contasCriticas} conta(s) vencem nos próximos dias. Vale organizar o pagamento.`;
  }
  return "Alerta vermelho: há contas atrasadas. Revise os pagamentos com prioridade.";
}

export default function PanelPagamentos() {
  const { totalMes, pagos, restante } = mockResumoMes;

  return (
    <div className="w-full h-full px-3 py-3 md:px-6 md:py-4 space-y-4 text-xs md:text-sm text-zinc-100">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h1 className="text-lg md:text-xl font-semibold text-zinc-50">
            Painel de Pagamentos
          </h1>
          <p className="text-[11px] md:text-xs text-zinc-400">
            Visão centralizada das suas contas fixas, boletos e assinaturas.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 rounded-full border border-amber-500/50 bg-amber-500/10 text-[10px] uppercase tracking-wide text-amber-200">
            Modo planejamento
          </span>
          <span className="px-2 py-1 rounded-full border border-zinc-700 bg-zinc-900/60 text-[10px] text-zinc-300">
            Versão inicial · dados de exemplo
          </span>
        </div>
      </header>

      {/* Resumo do mês */}
      <section>
        <div className="super2-section-title mb-2">
          Resumo de contas do mês
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <div className="rounded-xl bg-zinc-900/70 border border-zinc-700/70 px-3 py-2 space-y-1">
            <div className="text-[10px] text-zinc-400">Total de contas</div>
            <div className="text-sm md:text-base font-semibold text-zinc-50">
              {fmtBRL(totalMes)}
            </div>
            <div className="text-[10px] text-zinc-500">
              Somatória de todas as contas cadastradas para este mês.
            </div>
          </div>

          <div className="rounded-xl bg-zinc-900/70 border border-emerald-600/60 px-3 py-2 space-y-1">
            <div className="text-[10px] text-zinc-400">Pagos no mês</div>
            <div className="text-sm md:text-base font-semibold text-emerald-300">
              {fmtBRL(pagos)}
            </div>
            <div className="text-[10px] text-zinc-500">
              Contas já quitadas, considerando pagamentos em qualquer forma.
            </div>
          </div>

          <div className="rounded-xl bg-zinc-900/70 border border-amber-500/60 px-3 py-2 space-y-1">
            <div className="text-[10px] text-zinc-400">Restante a pagar</div>
            <div className="text-sm md:text-base font-semibold text-amber-300">
              {fmtBRL(restante)}
            </div>
            <div className="text-[10px] text-zinc-500">
              Valor aproximado que ainda precisa sair da sua carteira.
            </div>
          </div>

          <div className="rounded-xl bg-zinc-900/70 border border-zinc-700 px-3 py-2 space-y-1">
            <div className="text-[10px] text-zinc-400">
              Leitura rápida da situação
            </div>
            <div className="text-[11px] leading-snug text-zinc-200">
              {riscoTexto()}
            </div>
          </div>
        </div>
      </section>

      {/* Linha do tempo de vencimentos */}
      <section>
        <div className="super2-section-title mb-2">
          Vencimentos organizados
        </div>
        <div className="grid md:grid-cols-3 gap-2">
          <div className="rounded-xl bg-zinc-950/80 border border-zinc-800 px-3 py-2 space-y-1">
            <div className="text-[11px] font-semibold text-zinc-100">
              Hoje
            </div>
            {mockHoje.length === 0 ? (
              <div className="text-[11px] text-zinc-500">
                Nenhuma conta para hoje.
              </div>
            ) : (
              mockHoje.map((bill) => (
                <div
                  key={bill.id}
                  className="mt-1 rounded-lg bg-zinc-900/80 border border-zinc-700 px-2 py-1 flex items-center justify-between gap-2"
                >
                  <div>
                    <div className="text-[11px] font-medium text-zinc-50">
                      {bill.nome}
                    </div>
                    <div className="text-[10px] text-zinc-500">
                      {bill.tipo} · {bill.vencimento}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[11px] font-semibold">
                      {fmtBRL(bill.valor)}
                    </div>
                    <span
                      className={
                        "inline-flex mt-0.5 px-1.5 py-0.5 rounded-full border text-[9px] " +
                        statusClass(bill.status)
                      }
                    >
                      {statusLabel(bill.status)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="rounded-xl bg-zinc-950/80 border border-zinc-800 px-3 py-2 space-y-1">
            <div className="text-[11px] font-semibold text-zinc-100">
              Próximos 7 dias
            </div>
            {mockProximos7.length === 0 ? (
              <div className="text-[11px] text-zinc-500">
                Nenhuma conta relevante nos próximos dias.
              </div>
            ) : (
              mockProximos7.map((bill) => (
                <div
                  key={bill.id}
                  className="mt-1 rounded-lg bg-zinc-900/80 border border-zinc-700 px-2 py-1 flex items-center justify-between gap-2"
                >
                  <div>
                    <div className="text-[11px] font-medium text-zinc-50">
                      {bill.nome}
                    </div>
                    <div className="text-[10px] text-zinc-500">
                      {bill.tipo} · {bill.vencimento}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[11px] font-semibold">
                      {fmtBRL(bill.valor)}
                    </div>
                    <span
                      className={
                        "inline-flex mt-0.5 px-1.5 py-0.5 rounded-full border text-[9px] " +
                        statusClass(bill.status)
                      }
                    >
                      {statusLabel(bill.status)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="rounded-xl bg-zinc-950/80 border border-zinc-800 px-3 py-2 space-y-1">
            <div className="text-[11px] font-semibold text-zinc-100">
              Este mês
            </div>
            {mockEsteMes.length === 0 ? (
              <div className="text-[11px] text-zinc-500">
                Nenhuma conta cadastrada para este mês.
              </div>
            ) : (
              mockEsteMes.map((bill) => (
                <div
                  key={bill.id}
                  className="mt-1 rounded-lg bg-zinc-900/80 border border-zinc-700 px-2 py-1 flex items-center justify-between gap-2"
                >
                  <div>
                    <div className="text-[11px] font-medium text-zinc-50">
                      {bill.nome}
                    </div>
                    <div className="text-[10px] text-zinc-500">
                      {bill.tipo} · {bill.vencimento}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[11px] font-semibold">
                      {fmtBRL(bill.valor)}
                    </div>
                    <span
                      className={
                        "inline-flex mt-0.5 px-1.5 py-0.5 rounded-full border text-[9px] " +
                        statusClass(bill.status)
                      }
                    >
                      {statusLabel(bill.status)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      {/* Contas cadastradas */}
      <section>
        <div className="super2-section-title mb-2">
          Contas cadastradas
        </div>
        <div className="rounded-xl bg-zinc-950/80 border border-zinc-800 overflow-hidden">
          <div className="hidden md:grid grid-cols-5 gap-2 px-3 py-2 text-[10px] text-zinc-400 border-b border-zinc-800">
            <div>Nome</div>
            <div>Tipo</div>
            <div>Vencimento típico</div>
            <div>Valor médio</div>
            <div>Status</div>
          </div>
          <div className="divide-y divide-zinc-800">
            {mockContasCadastradas.map((bill) => (
              <div
                key={bill.id}
                className="px-3 py-2 grid grid-cols-1 md:grid-cols-5 gap-1 md:gap-2 text-[11px]"
              >
                <div>
                  <div className="font-medium text-zinc-100">
                    {bill.nome}
                  </div>
                  <div className="md:hidden text-[10px] text-zinc-500">
                    {bill.tipo} · {bill.vencimento}
                  </div>
                </div>
                <div className="hidden md:block text-zinc-300">
                  {bill.tipo}
                </div>
                <div className="hidden md:block text-zinc-300">
                  {bill.vencimento}
                </div>
                <div className="text-zinc-200">
                  {fmtBRL(bill.valor)}
                </div>
                <div>
                  <span
                    className={
                      "inline-flex px-1.5 py-0.5 rounded-full border text-[9px] " +
                      statusClass(bill.status)
                    }
                  >
                    {statusLabel(bill.status)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <p className="mt-1 text-[10px] text-zinc-500">
          Nesta primeira versão, os dados são apenas demonstrativos. Em breve,
          este painel será alimentado pelas suas contas reais cadastradas no
          backend da Aurea Gold.
        </p>
      </section>

      {/* IA 3.0 Consultor de contas */}
      <section className="pb-4">
        <div className="super2-section-title mb-2">
          IA 3.0 · Consultor de contas
        </div>
        <div className="rounded-xl bg-zinc-950/90 border border-amber-500/40 px-3 py-3 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <div className="text-[11px] font-semibold text-amber-100">
              IA 3.0 da Aurea Gold
            </div>
            <span className="px-1.5 py-0.5 rounded-full border border-amber-500/60 text-[9px] text-amber-200">
              consultor de contas
            </span>
          </div>
          <p className="text-[11px] leading-snug text-zinc-100">
            Aqui é o módulo onde a IA vai olhar para as suas contas, vencimentos
            e saldo da Carteira PIX para te avisar se existe risco de atraso e
            qual é a melhor ordem para pagar sem estourar seu caixa.
          </p>
          <p className="text-[10px] text-zinc-400">
            Por enquanto, este painel está em modo demonstrativo. Nas próximas
            fases, vamos conectar os dados reais e ativar respostas dinâmicas
            usando a IA 3.0 da Aurea Gold.
          </p>
          <div className="flex flex-wrap gap-2 mt-1">
            <span className="px-2 py-1 rounded-full bg-zinc-900/80 border border-zinc-700 text-[10px] text-zinc-200">
              Tenho risco de atrasar alguma conta?
            </span>
            <span className="px-2 py-1 rounded-full bg-zinc-900/80 border border-zinc-700 text-[10px] text-zinc-200">
              Quanto vou pagar de contas esta semana?
            </span>
            <span className="px-2 py-1 rounded-full bg-zinc-900/80 border border-zinc-700 text-[10px] text-zinc-200">
              Quais contas faz sentido pagar hoje?
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}

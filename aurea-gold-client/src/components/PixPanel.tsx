import React, { useMemo } from "react";
import AureaAssistant from "@/app/customer/components/AureaAssistant";

// ATENÇÃO IMPORTANTE PRA NÃO QUEBRAR NADA
// Eu vou assumir que o PixPanel original recebia props tipo:
//   { saldoPix, transacoes }
// Se o teu PixPanel atual usa props, mantém as props no "function PixPanel(...)"
// e usa elas no lugar dos mocks abaixo. Mas por enquanto vou deixar com mock,
// pra não travar na IA. Depois a gente volta e cola as props reais de novo.

export default function PixPanel() {
  // mock local só pra layout inicial. Isso bate visualmente com teu print.
  const saldoPix = 1041.15;

  // histórico mock baseado no print que você mandou
  const transacoes = useMemo(
    () => [
      {
        tipo: "saida",
        valor: 50.0,
        descricao:
          "PIX para chave-teste@aurea.bank - pagamento de teste",
        ts: "2025-10-28T03:50:13",
      },
      {
        tipo: "saida",
        valor: 123.45,
        descricao: "teste interno insert",
        ts: "2025-10-28T03:48:06",
      },
      {
        tipo: "entrada",
        valor: 200.0,
        descricao: "PIX retorno de compra",
        ts: "2025-10-28T03:34:08",
      },
      {
        tipo: "saida",
        valor: 100.0,
        descricao: "PIX amigo",
        ts: "2025-10-28T03:34:08",
      },
      {
        tipo: "saida",
        valor: 85.9,
        descricao: "Transferência PIX mercado",
        ts: "2025-10-28T03:34:08",
      },
      {
        tipo: "entrada",
        valor: 1200.5,
        descricao: "PIX salário",
        ts: "2025-10-28T03:34:08",
      },
    ],
    []
  );

  return (
    <div className="min-h-screen bg-black text-white flex flex-col lg:flex-row lg:items-start lg:gap-6 p-4">
      {/* ===================== COLUNA ESQUERDA: PIX ===================== */}
      <div className="flex-1 max-w-full lg:max-w-[60%] bg-black border border-[#333] rounded-2xl shadow-xl p-4">
        <h1
          className="text-lg font-bold"
          style={{ color: "#ffd700" }}
        >
          PIX • Aurea Gold
        </h1>

        <div className="mt-2 text-sm">
          <strong>Saldo PIX:</strong>{" "}
          <span
            className="font-semibold"
            style={{ color: "#ffd700" }}
          >
            R${" "}
            {saldoPix.toLocaleString("pt-BR", {
              minimumFractionDigits: 2,
            })}
          </span>
        </div>

        <div
          className="mt-4 text-sm font-semibold border-b pb-2"
          style={{ color: "#ffd700", borderColor: "#444" }}
        >
          Histórico de Transações
        </div>

        <div className="divide-y divide-[#444] mt-2 text-sm">
          {transacoes.map((tx, idx) => (
            <div key={idx} className="py-3">
              <div className="flex justify-between">
                <div
                  className={
                    tx.tipo === "entrada"
                      ? "text-green-400 font-semibold"
                      : "text-red-400 font-semibold"
                  }
                >
                  {tx.tipo === "entrada"
                    ? "↑ Entrada"
                    : "↓ Saída"}
                </div>

                <div
                  className={
                    tx.tipo === "entrada"
                      ? "text-green-400 font-semibold"
                      : "text-red-400 font-semibold"
                  }
                >
                  R{"$ "}
                  {tx.valor.toLocaleString("pt-BR", {
                    minimumFractionDigits: 2,
                  })}
                </div>
              </div>

              <div className="text-gray-200 text-[13px]">
                {tx.descricao}
              </div>

              <div className="text-[11px] text-gray-400">
                {tx.ts}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ===================== COLUNA DIREITA: AUREA IA 3.0 ===================== */}
      <div className="w-full lg:w-[35%] mt-6 lg:mt-0">
        <AureaAssistant />
      </div>
    </div>
  );
}

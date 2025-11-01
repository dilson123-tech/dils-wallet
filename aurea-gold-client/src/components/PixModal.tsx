</div>
import React, { useState } from "react";
</div>

</div>
type PixModalProps = {
</div>
  onClose: () => void;
</div>
  onConfirm: (data: {
</div>
    chave: string;
</div>
    valor: number;
</div>
    descricao: string;
</div>
  }) => void;
</div>
};
</div>

</div>
export default function PixModal({ onClose, onConfirm }: PixModalProps) {
</div>
  const [chave, setChave] = useState("");
</div>
  const [valor, setValor] = useState("");
</div>
  const [descricao, setDescricao] = useState("");
</div>
  const [erroLocal, setErroLocal] = useState<string | null>(null);
</div>

</div>
  function tentarEnviar() {
</div>
    // validação básica antes de chamar backend
</div>
    const vNum = parseFloat(
</div>
      valor.replace(",", ".").trim()
</div>
    );
</div>

</div>
    if (!chave.trim()) {
</div>
      setErroLocal("Informe a chave PIX de destino.");
</div>
      return;
</div>
    }
</div>
    if (isNaN(vNum) || vNum <= 0) {
</div>
      setErroLocal("Informe um valor válido (> 0).");
</div>
      return;
</div>
    }
</div>
    if (!descricao.trim()) {
</div>
      setErroLocal("Descreva o motivo/pagamento.");
</div>
      return;
</div>
    }
</div>

</div>
    setErroLocal(null);
</div>

</div>
    onConfirm({
</div>
      chave: chave.trim(),
</div>
      valor: vNum,
</div>
      descricao: descricao.trim(),
</div>
    });
</div>
  }
</div>

</div>
  return (
</div>
    <div className="page">
</div>
      <div className="w-full max-w-sm rounded-xl border border-yellow-600/40 bg-black/90 p-4 shadow-[0_0_30px_rgba(212,175,55,0.4)] text-yellow-200">
</div>
        <div className="text-yellow-400 text-xs uppercase tracking-wide">
</div>
          Aurea Gold Premium
</div>
        </div>
</div>
        <div className="text-xl font-bold text-yellow-300">
</div>
          <div className="actions">Enviar PIX
        </div>
        <div className="text-[0.8rem] text-yellow-500/80 mb-4">
          Pagamento instantâneo entre contas
        </div>

        {erroLocal && (
          <div className="text-red-400 text-xs font-semibold mb-3">
            {erroLocal}
          </div>
        )}

        <div className="space-y-3 text-yellow-100 text-sm">
          <div className="flex flex-col">
            <label className="text-[0.75rem] text-yellow-500/80 mb-1">
              Chave PIX (CPF, e-mail, telefone...)
            </label>
            <input
              className="rounded-lg border border-yellow-600/40 bg-black/40 px-3 py-2 text-yellow-200 outline-none focus:ring-1 focus:ring-yellow-400"
              value={chave}
              onChange={(e) => setChave(e.target.value)}
              placeholder="ex: teste@aurea.bank"
            />
          </div>

          <div className="flex flex-col">
            <label className="text-[0.75rem] text-yellow-500/80 mb-1">
              Valor (R$)
            </label>
            <input
              className="rounded-lg border border-yellow-600/40 bg-black/40 px-3 py-2 text-yellow-200 outline-none focus:ring-1 focus:ring-yellow-400"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              placeholder="ex: 50,00"
            />
          </div>
          <div className="flex flex-col">
            <label className="text-[0.75rem] text-yellow-500/80 mb-1">
              Descrição / motivo
            </label>
            <input
              className="rounded-lg border border-yellow-600/40 bg-black/40 px-3 py-2 text-yellow-200 outline-none focus:ring-1 focus:ring-yellow-400"
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              placeholder="ex: Pagamento de teste"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 text-sm mt-6">
          <button
            onClick={onClose}
            className="px-3 py-2 rounded-lg border border-yellow-600/40 text-yellow-400 hover:bg-black/40 active:scale-95 transition"
          >
            Cancelar
          </button>

          <button
            onClick={tentarEnviar}
            className="px-3 py-2 rounded-lg bg-yellow-300 text-black font-bold border border-yellow-500/60 hover:bg-yellow-200 active:scale-95 transition"
          >
            Confirmar envio
          </button>
        </div>
      </div>
    </div>
  );
}

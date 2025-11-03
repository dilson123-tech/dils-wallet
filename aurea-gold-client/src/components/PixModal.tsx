import React, { useState } from "react";

type PixModalProps = {
  onClose: () => void;
  onConfirm: (data: { chave:string; valor:number; descricao:string }) => void;
};

export default function PixModal({ onClose, onConfirm }: PixModalProps) {
  const [chave, setChave] = useState("");
  const [valor, setValor] = useState("");
  const [descricao, setDescricao] = useState("");
  const [err, setErr] = useState<string|null>(null);

  function confirm() {
    const v = parseFloat((valor||"").replace(",", "."));
    if (!chave.trim())       return setErr("Informe a chave PIX.");
    if (!isFinite(v) || v<=0) return setErr("Valor inválido.");
    if (!descricao.trim())   return setErr("Descreva o PIX.");
    setErr(null);
    onConfirm({ chave: chave.trim(), valor: v, descricao: descricao.trim() });
  }

  return (
    <div className="fixed inset-0 bg-black/60 grid place-items-center z-50">
      <div className="w-[min(92vw,460px)] rounded-2xl bg-neutral-900 border border-neutral-700 p-4">
        <h3 className="text-yellow-300 text-lg font-semibold mb-2">PIX via Aurea Gold</h3>
        <div className="space-y-3 text-sm text-neutral-200">
          <input value={chave} onChange={e=>setChave(e.target.value)} placeholder="Chave (e-mail, tel, aleatória)"
                 className="w-full rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 outline-none" />
          <input value={valor} onChange={e=>setValor(e.target.value)} placeholder="Valor (ex: 125,50)"
                 className="w-full rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 outline-none" />
          <input value={descricao} onChange={e=>setDescricao(e.target.value)} placeholder="Descrição"
                 className="w-full rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 outline-none" />
          {err && <div className="text-red-300 text-xs">{err}</div>}
        </div>
        <div className="mt-4 flex gap-2 justify-end">
          <button onClick={onClose} className="px-3 py-2 text-xs rounded-lg bg-neutral-800 hover:bg-neutral-700">Cancelar</button>
          <button onClick={confirm} className="px-3 py-2 text-xs rounded-lg bg-yellow-600 hover:bg-yellow-500 text-black font-semibold">Enviar PIX</button>
        </div>
      </div>
    </div>
  );
}

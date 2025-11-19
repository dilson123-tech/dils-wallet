import React, { useState } from "react";

export type PixForm = { chave: string; valor: number; descricao: string };

export default function PixModal({
  onClose, onConfirm, loading
}: {
  onClose: () => void;
  onConfirm: (data: PixForm) => void;
  loading?: boolean;
}) {
  const [chave, setChave] = useState("");
  const [valor, setValor] = useState("");
  const [descricao, setDescricao] = useState("");

  const canSend = chave.trim().length >= 6 && !!parseFloat(valor);

  function submit() {
    const v = parseFloat(valor.replace(",", "."));
    if (!canSend || Number.isNaN(v) || v <= 0) return;
    onConfirm({ chave: chave.trim(), valor: v, descricao: descricao.trim() || "PIX via Aurea Gold" });
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>

        <label className="field">
          <span>Chave PIX</span>
          <input placeholder="e-mail, CPF/CNPJ, telefone..." value={chave} onChange={e=>setChave(e.target.value)} />
        </label>

        <label className="field">
          <span>Valor</span>
          <input placeholder="0,00" value={valor} onChange={e=>setValor(e.target.value)} />
        </label>

        <label className="field">
          <span>Descrição (opcional)</span>
          <input placeholder="motivo/observação" value={descricao} onChange={e=>setDescricao(e.target.value)} />
        </label>

        <div className="actions-row">
          <button className="btn-outline" onClick={onClose} disabled={loading}>Cancelar</button>
          <button className="btn" onClick={submit} disabled={!canSend || !!loading}>
          </button>
        </div>
      </div>
    </div>
  );
}

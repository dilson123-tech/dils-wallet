import React, { useState } from "react";
import { sendPix } from "./api";

type AureaPixSendModalProps = {
  open: boolean;
  onClose: () => void;
  onSent?: () => void;
};

const AureaPixSendModal: React.FC<AureaPixSendModalProps> = ({
  open,
  onClose,
  onSent,
}) => {
  const [dest, setDest] = useState("");
  const [valor, setValor] = useState("");
  const [mensagem, setMensagem] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  if (!open) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setOkMsg(null);

    const v = parseFloat(valor.replace(",", "."));
    if (!dest.trim()) {
      setErr("Informe o destinatário do PIX.");
      return;
    }
    if (Number.isNaN(v) || v <= 0) {
      setErr("Informe um valor válido maior que zero.");
      return;
    }

    try {
      setLoading(true);
      await sendPix(dest.trim(), v, mensagem.trim() || undefined);
      setOkMsg("PIX enviado com sucesso.");
      if (onSent) onSent();
      // limpa campos
      setValor("");
      setMensagem("");
    } catch (e: any) {
      setErr(e?.message ?? "Falha ao enviar PIX.");
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    setErr(null);
    setOkMsg(null);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="w-[340px] max-w-full rounded-2xl border border-[#d4af37]/60 bg-[#050505] shadow-[0_0_25px_#d4af3733] p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-[#d4af37]">
            Enviar PIX
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className="text-[11px] px-2 py-0.5 rounded-full border border-[#d4af37]/60 text-[#d4af37]/90 hover:bg-[#1a1405]"
          >
            Fechar
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-2 text-[11px]">
          <div>
            <label className="block mb-1 opacity-80">
              Destinatário (e-mail ou chave)
            </label>
            <input
              className="w-full rounded-md bg-black/60 border border-[#3a3a3a] px-2 py-1 text-[11px] focus:outline-none focus:border-[#d4af37]"
              value={dest}
              onChange={(e) => setDest(e.target.value)}
              placeholder="ex: usuario@banco.com"
            />
          </div>

          <div>
            <label className="block mb-1 opacity-80">Valor (R$)</label>
            <input
              className="w-full rounded-md bg-black/60 border border-[#3a3a3a] px-2 py-1 text-[11px] focus:outline-none focus:border-[#d4af37]"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              placeholder="ex: 150,00"
            />
          </div>

          <div>
            <label className="block mb-1 opacity-80">
              Mensagem (opcional)
            </label>
            <textarea
              className="w-full rounded-md bg-black/60 border border-[#3a3a3a] px-2 py-1 text-[11px] focus:outline-none focus:border-[#d4af37] min-h-[50px]"
              value={mensagem}
              onChange={(e) => setMensagem(e.target.value)}
              placeholder="Identificação do pagamento"
            />
          </div>

          {err && (
            <p className="text-[11px] text-red-400 mt-1">⚠ {err}</p>
          )}

          {okMsg && (
            <p className="text-[11px] text-emerald-400 mt-1">
              ✅ {okMsg}
            </p>
          )}

          <div className="mt-3 flex justify-end gap-2">
            <button
              type="button"
              onClick={handleClose}
              className="h-8 px-3 rounded-md border border-[#444] text-[11px] hover:bg-[#151515]"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="h-8 px-4 rounded-md border border-[#d4af37]/80 bg-gradient-to-r from-[#3b2b00] to-[#2a2100] text-[11px] font-semibold hover:from-[#4a3600] hover:to-[#332600] active:scale-[0.97] transition disabled:opacity-60"
              disabled={loading}
            >
              {loading ? "Enviando..." : "Confirmar PIX"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AureaPixSendModal;

import React, { useState } from "react";
import { sendPix } from "./api";

type AureaPixSendModalProps = {
  open: boolean;
  onClose: () => void;
  onSent?: () => void;
};

export default function AureaPixSendModal({
  open,
  onClose,
  onSent,
}: AureaPixSendModalProps) {
  const [dest, setDest] = useState("");
  const [valorStr, setValorStr] = useState("");
  const [mensagem, setMensagem] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!open) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setSuccess(null);

    const destTrim = dest.trim();
    if (!destTrim) {
      setErr("Informe o destinatário (e-mail ou chave).");
      return;
    }

    const valorNum = parseFloat(
      valorStr.replace(".", "").replace(",", ".")
    );

    if (!Number.isFinite(valorNum) || valorNum <= 0) {
      setErr("Informe um valor válido maior que zero.");
      return;
    }

    const payload = {
      dest: destTrim,
      valor: valorNum,
      descricao: mensagem || null,
    };

    try {
      setLoading(true);
      console.log("SUPER2 sendPix payload =>", payload);
      const resp = await sendPix(payload as any);
      console.log("SUPER2 sendPix resp =>", resp);

      setSuccess("PIX enviado com sucesso.");
      setDest("");
      setValorStr("");
      setMensagem("");

      if (onSent) {
        onSent();
      }
      // se quiser fechar automaticamente depois de enviar:
      // onClose();
    } catch (e: any) {
      console.error("SUPER2 sendPix erro =>", e);
      const msg =
        e?.message ||
        "Falha ao enviar PIX. Tente novamente em instantes.";
      setErr(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-[360px] max-w-full rounded-2xl border border-[#d4af37]/60 bg-black/90 px-4 py-3 text-[#f5f5f5]">
        <header className="flex items-center justify-between mb-2">
          <div className="text-sm font-semibold text-[#d4af37]">
            Enviar PIX
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[10px] px-2 py-0.5 rounded-full border border-[#d4af37]/60 hover:bg-[#d4af37]/10"
          >
            Fechar
          </button>
        </header>

        <form onSubmit={handleSubmit} className="space-y-2 text-[11px]">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] opacity-80">
              Destinatário (e-mail ou chave)
            </label>
            <input
              className="h-7 rounded-md border border-[#d4af37]/40 bg-black/60 px-2 text-[11px] outline-none focus:border-[#d4af37]"
              value={dest}
              onChange={(e) => setDest(e.target.value)}
              placeholder="ex: fulano@banco.com"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] opacity-80">Valor (R$)</label>
            <input
              className="h-7 rounded-md border border-[#d4af37]/40 bg-black/60 px-2 text-[11px] outline-none focus:border-[#d4af37]"
              value={valorStr}
              onChange={(e) => setValorStr(e.target.value)}
              placeholder="ex: 300,00"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] opacity-80">
              Mensagem (opcional)
            </label>
            <textarea
              className="min-h-[48px] rounded-md border border-[#d4af37]/40 bg-black/60 px-2 py-1 text-[11px] outline-none focus:border-[#d4af37]"
              value={mensagem}
              onChange={(e) => setMensagem(e.target.value)}
              placeholder="ex: Luz / Aluguel / Teste"
            />
          </div>

          {err && (
            <div className="text-[10px] text-red-400 whitespace-pre-wrap">
              {err}
            </div>
          )}

          {success && (
            <div className="text-[10px] text-emerald-400 whitespace-pre-wrap">
              {success}
            </div>
          )}

          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="h-7 px-3 rounded-md border border-[#d4af37]/50 bg-black/60 text-[11px] hover:bg-black/80 active:scale-[0.97]"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="h-7 px-3 rounded-md border border-[#228000] bg-gradient-to-r from-[#228000] to-[#21a020] text-[11px] font-semibold disabled:opacity-60 disabled:cursor-not-allowed active:scale-[0.97]"
            >
              {loading ? "Enviando..." : "Confirmar PIX"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

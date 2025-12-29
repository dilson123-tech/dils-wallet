import React, { useEffect, useState } from "react";
import { API_BASE } from "../../../lib/api";
import { getToken } from "../../../lib/auth";

const USER_EMAIL = (import.meta as any).env?.VITE_USER_EMAIL || "";

type PixTx = {
  id: number;
  tipo: "envio" | "recebimento";
  valor: number;
  descricao?: string | null;
  created_at?: string;
};

function AureaModal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 aurea-modal z-50 p-0 sm:p-6 grid">
      <div className="aurea-modal-card w-full max-w-lg p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="aurea-gold-text font-semibold">{title}</div>
          <button onClick={onClose} className="aurea-btn-ghost rounded-lg h-10 px-3">
            Fechar
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export default function QuickPixActions() {
  const [openSend, setOpenSend] = useState(false);
  const [openHist, setOpenHist] = useState(false);

  const [sending, setSending] = useState(false);
  const [dest, setDest] = useState(USER_EMAIL || "");
  const [valor, setValor] = useState<number>(0);
  const [msg, setMsg] = useState("");

  const [hist, setHist] = useState<PixTx[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  async function doSend() {
    setSending(true);
    setErr(null);
    setOk(null);
    try {
      const r = await fetch(`${API_BASE}/api/v1/pix/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(USER_EMAIL ? { "X-User-Email": USER_EMAIL } : {}),
        },
        body: JSON.stringify({ dest, valor: Number(valor), msg }),
      });
      if (!r.ok) {
        const t = await r.text().catch(() => "");
        throw new Error(`HTTP ${r.status} ${t}`.slice(0, 240));
      }
      setOk("PIX enviado com sucesso ✅");
      window.dispatchEvent(new CustomEvent("aurea:pix:sent"));
      setValor(0);
      setMsg("");
    } catch (e: any) {
      setErr(e?.message || "Falha no envio");
    } finally {
      setSending(false);
    }
  }

  async function loadHist() {
    setErr(null);
    setOk(null);
    setHist(null);
    try {
      const r = await fetch(`${API_BASE}/api/v1/pix/list`, {
        headers: { ...(USER_EMAIL ? { "X-User-Email": USER_EMAIL } : {}), ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}), },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      setHist(Array.isArray(j) ? (j as PixTx[]) : []);
    } catch (e: any) {
      setErr(e?.message || "Falha ao carregar histórico");
    }
  }

  useEffect(() => {
    if (openHist) loadHist();
  }, [openHist]);

  return (
    <>
      {/* Barra fixa */}
      <div className="fixed bottom-4 right-4 flex gap-2 z-40">
        <button onClick={() => setOpenSend(true)} className="aurea-btn rounded-xl h-11 px-4">
          + Enviar PIX
        </button>
        <button onClick={() => setOpenHist(true)} className="aurea-btn-ghost rounded-xl h-11 px-4">
          Histórico
        </button>
        <button
          onClick={() => {
            setDest(USER_EMAIL || "");
            setValor(0);
            setMsg("");
            setHist(null);
            setErr(null);
            setOk(null);
          }}
          className="aurea-btn-ghost rounded-xl h-11 px-4"
        >
          Limpar
        </button>
      </div>

      {/* Modal Enviar */}
      <AureaModal open={openSend} onClose={() => setOpenSend(false)} title="Enviar PIX">
        <div className="space-y-3">
          <label className="block text-sm text-neutral-300">Destinatário (e-mail/PIX)</label>
          <input
            value={dest}
            onChange={(e) => setDest(e.target.value)}
            className="aurea-input"
          />
          <label className="block text-sm text-neutral-300">Valor (R$)</label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={valor}
            onChange={(e) => setValor(+e.target.value)}
            className="aurea-input"
          />
          <label className="block text-sm text-neutral-300">Mensagem</label>
          <input
            value={msg}
            onChange={(e) => setMsg(e.target.value)}
            className="aurea-input"
          />
          {err && <div className="text-red-400 text-sm">{err}</div>}
          {ok && <div className="text-emerald-400 text-sm">{ok}</div>}
          <div className="flex justify-end gap-2 pt-1">
            <button onClick={() => setOpenSend(false)} className="aurea-btn-ghost rounded-xl h-10 px-4">
              Cancelar
            </button>
            <button onClick={doSend} disabled={sending} className="aurea-btn rounded-xl h-10 px-4">
              {sending ? "Enviando..." : "Confirmar envio"}
            </button>
          </div>
        </div>
      </AureaModal>

      {/* Modal Histórico */}
      <AureaModal open={openHist} onClose={() => setOpenHist(false)} title="Histórico PIX">
        <div className="space-y-3 max-h-[60vh] overflow-auto pr-1">
          {err && <div className="text-red-400 text-sm">{err}</div>}
          {!err && hist === null && <div className="text-neutral-400 text-sm">Carregando...</div>}
          {!err && hist && hist.length === 0 && (
            <div className="text-neutral-400 text-sm">Nenhuma transação.</div>
          )}
          {!err && hist && hist.length > 0 && (
            <ul className="space-y-2">
              {hist.slice(0, 30).map((tx) => (
                <li key={tx.id} className="aurea-card rounded-xl p-3 flex items-center justify-between">
                  <div className="text-sm">
                    {tx.descricao || (tx.tipo === "envio" ? "Envio PIX" : "Recebimento")}
                  </div>
                  <div
                    className={`font-semibold ${
                      tx.tipo === "envio" ? "text-red-300" : "text-emerald-300"
                    }`}
                  >
                    {(tx.tipo === "envio" ? "-" : "+") +
                      (tx.valor || 0).toLocaleString("pt-BR", {
                        style: "currency",
                        currency: "BRL",
                      })}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </AureaModal>
    </>
  );
}

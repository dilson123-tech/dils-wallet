import React, { useEffect, useState } from "react";
import PixModal, { PixForm } from "./PixModal";
import Toast from "./Toast";
import enterSound from "../../../assets/sounds/aurea-whoosh-enter.mp3";
import errorSound from "../../../assets/sounds/aurea-error.mp3";
import clickSound from "../../../assets/sounds/aurea-click-gold.mp3";

type PixTx = {
  id: number;
  tipo: "entrada" | "saida";
  valor: number;
  descricao: string;
  timestamp?: string | null;
};
type BalanceResp = { saldo_pix: number };
type HistoryResp = { history: PixTx[] };

const API_BASE =
  (import.meta as any)?.env?.VITE_API_BASE || "http://127.0.0.1:8080";
const API_SEND = `${API_BASE}/api/v1/pix/send`;

// --- helpers HTTP ---
async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status} em ${url}`);
  return (await r.json()) as T;
}
async function postJSON<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status} em ${url}`);
  return (await r.json()) as T;
}
function fmtBR(v: number, sinal?: "entrada" | "saida") {
  const n = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(v);
  return sinal ? (sinal === "saida" ? "- " : "+ ") + n : n;
}

// --- sons (idempotente) ---
function playOk(){ try{ new Audio(enterSound).play(); }catch{} }
function playFail(){ try{ new Audio(errorSound).play(); }catch{} }
function playClick(){ try{ new Audio(clickSound).play(); }catch{} }

function PixPanel() {
  const [saldo, setSaldo] = useState<number | null>(null);
  const [hist, setHist] = useState<PixTx[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [sending, setSending] = useState(false);
  const [toast, setToast] = useState<{ kind: "success" | "error"; msg: string } | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      setErr(null);
      const b = await getJSON<BalanceResp>(`${API_BASE}/api/v1/pix/balance`);
      setSaldo(b.saldo_pix);
      const h = await getJSON<HistoryResp>(`${API_BASE}/api/v1/pix/history`);
      setHist(h.history || []);
      setToast(null);
    } catch (e: any) {
      setErr(e?.message || "Falha ao carregar dados do PIX");
      setToast({ kind: "error", msg: e?.message || "Falha ao carregar dados do PIX" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
  load();
  const onVis = () => { if (document.visibilityState === "visible") load(); };
  document.addEventListener("visibilitychange", onVis);
  return () => document.removeEventListener("visibilitychange", onVis);
}, []);

  async function onConfirmPix(data: PixForm) {
    try {
      setSending(true);
      setErr(null);
      await postJSON(API_SEND, {
        chave: data.chave,
        valor: data.valor,
        descricao: data.descricao,
      });
      playOk();
      setToast({ kind: "success", msg: "PIX enviado!" });
      setShowModal(false);
      await load();
    } catch (e: any) {
      playFail();
      setToast({ kind: "error", msg: e?.message || "Falha ao enviar PIX" });
    } finally {
      setSending(false);
    }
  }

  // --- render ---
  return (
    <div className="pix-panel">
  <div className="pix-header">
    <h2>PIX</h2>
    <button className="btn" onClick={() => { playClick(); setShowModal(true); }} disabled={sending}>
      Novo PIX
    </button>
  </div>

  {loading && <p>Carregando...</p>}
  {err && <p role="alert">{err}</p>}

  <div className="pix-saldo">{saldo !== null ? fmtBR(saldo) : "--"}</div>

  <div className="pix-hist">
  {hist && hist.length > 0 ? (
    hist.map((it) => (
      <div key={it.id} className={"pix-item " + it.tipo}>
        <span className="tipo">{it.tipo}</span>
        <span className="valor">{fmtBR(it.valor, it.tipo)}</span>
        <span className="desc">{it.descricao}</span>
      </div>
    ))
  ) : (
    <div className="pix-empty">Nenhuma movimentação PIX ainda.</div>
  )}
</div>

{showModal && (
  <PixModal onClose={() => setShowModal(false)} onConfirm={onConfirmPix} />
)}

{toast && (
  <Toast kind={toast.kind} onClose={() => setToast(null)}>
    {toast.msg}
  </Toast>
)}
</div>
);
}



export default PixPanel;

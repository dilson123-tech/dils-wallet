import React, { useEffect, useState } from "react";
import clickSound from "../../../assets/sounds/aurea-click-gold.mp3";
import successSound from "../../../assets/sounds/aurea-success-chime.mp3";
import enterSound from "../../../assets/sounds/aurea-whoosh-enter.mp3";
import errorSound from "../../../assets/sounds/aurea-error.mp3";
import PixModal, { PixForm } from "./PixModal";
import Toast from "./Toast";

type PixTx = { id: number; tipo: "entrada" | "saida"; valor: number; descricao: string; timestamp?: string | null; };
type BalanceResp = { saldo_pix: number };
type HistoryResp = { history: PixTx[] };

const API_BASE = (import.meta as any)?.env?.VITE_API_BASE || "http://localhost:8080";
const API_SEND = `${API_BASE}/api/v1/pix/send`;

async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status} em ${url}`);
  return (await r.json()) as T;
}
async function postJSON<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`HTTP ${r.status} em ${url}`);
  return (await r.json()) as T;
}
function fmtBR(v: number, sinal?: "entrada" | "saida") {
  const n = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
  return sinal ? (sinal === "saida" ? "- " : "+ ") + n : n;
}

function getVol(){ const v=parseFloat(localStorage.getItem("aurea:vol")||"0.55"); return isNaN(v)?0.55:Math.min(1,Math.max(0,v)); }
function setVol(v){ const x=Math.min(1,Math.max(0,Number(v))); localStorage.setItem("aurea:vol", String(x)); return x; }

// === Aurea Sound Helper (idempotent) ===
function playSom(){
  if (localStorage.getItem("aurea:som")==="off") return;
  const audio=new Audio(clickSound);
  audio.volume=getVol();
  audio.play().catch(()=>{});
}


function playSomEnter(){
  if (localStorage.getItem("aurea:som")==="off") return;
  const audio=new Audio(enterSound);
  audio.volume=Math.min(1, getVol()*0.9);
  audio.play().catch(()=>{});
}

function playSomError(){
  if (localStorage.getItem("aurea:som")==="off") return;
  const audio=new Audio(errorSound);
  audio.volume=Math.min(1, getVol()*0.8);
  audio.play().catch(()=>{});
}

export default function PixPanel() {
  const [saldo, setSaldo] = useState<number | null>(null);
  const [hist, setHist] = useState<PixTx[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [sending, setSending] = useState(false);
  const [toast, setToast] = useState<{ kind: "success" | "error"; msg: string } | null>(null);
  const [vol, setVol] = useState<number>(Number(localStorage.getItem("aurea:vol") ?? "0.55"));

  const load = async () => {
    try {
      setLoading(true);
      setErr(null);
      const b = await getJSON<BalanceResp>(`${API_BASE}/api/v1/pix/balance`);
      setSaldo(b.saldo_pix);
      const h = await getJSON<HistoryResp>(`${API_BASE}/api/v1/pix/history`);
      setHist(h.history || []);
    } catch (e: any) {
      playSomError();
      setToast({kind:"error", msg: (e?.message||"Falha ao carregar dados do PIX")});
      setTimeout(()=>setToast(null), 2000);
      setErr(e?.message || "Falha ao carregar dados do PIX");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);
useEffect(() => { setTimeout(playSomEnter,120); }, []);
  useEffect(()=>{ setVol(v => setVol && (isNaN(Number(v))?0.55:v)); },[]);
  useEffect(()=>{ localStorage.setItem("aurea:vol", String(vol)); },[vol]);
useEffect(() => { playSom(); }, []);

  async function handleSend(data: PixForm) {
    try {
      setSending(true);
      const optimistic: PixTx = {
        id: Date.now(),
        tipo: "saida",
        valor: data.valor,
        descricao: data.descricao || `PIX para ${data.chave}`,
        timestamp: new Date().toISOString(),
      };
      setHist((h) => [optimistic, ...h]);
      setSaldo((s) => (s == null ? s : Math.max(0, s - data.valor)));

      await postJSON(API_SEND, { chave: data.chave, valor: data.valor, descricao: data.descricao });

      setShowModal(false);
      setToast({ kind: "success", msg: "PIX enviado com sucesso 💸" });

      await load();

      // brilho no último item
      setTimeout(() => {
        const el = document.querySelector(".pix-item");
        if (el) el.classList.add("flash");
        setTimeout(() => el?.classList.remove("flash"), 1500);
      }, 200);
    } catch (e: any) {
    playSomError();
    setToast({kind:"error", msg: (e?.message||"Falha no envio do PIX")});
    setTimeout(()=>setToast(null), 2000);
      setToast({ kind: "error", msg: e?.message || "Erro ao enviar PIX" });
    } finally {
      setSending(false);
    }
  }

  const totalEntradas = hist.filter(h => h.tipo === "entrada").reduce((a, b) => a + b.valor, 0);
  const totalSaidas = hist.filter(h => h.tipo === "saida").reduce((a, b) => a + b.valor, 0);

  return (
    <main className="page pix-panel">
      <h1>PIX · Aurea Gold</h1>

      <section className="card section">
        <h2>Saldo PIX</h2>
        <div className="balance" style={{ marginTop: 6 }}>
          <span className="amount">
            {saldo === null ? "—" : fmtBR(saldo)}
          </span>
          <span className="currency">{loading ? "atualizando..." : "atual"}</span>
        </div>

        <div className="actions" style={{ marginTop: 10, display: "flex", gap: 8 }}>
          <button className={`btn ${sending ? "sending" : ""}`} onClick={() => setShowModal(true)}>
            Enviar PIX
          </button>
          <button className="btn-outline" onClick={() => { playSom(); load(); }} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
        </div>

        <div style={{marginTop:6,display:"flex",alignItems:"center",gap:8}}>
          <span style={{opacity:.75,fontSize:12}}>🔊 Volume</span>
          <input type="range" min={0} max={1} step={0.05} value={vol} onChange={e => setVol(Number((e.target as HTMLInputElement).value))} style={{width:140}} />
          <span style={{opacity:.75,fontSize:12}}>{Math.round(vol*100)}%</span>
        </div>
        {toast && (
          <div className="ai-answer" style={{ marginTop: 10 }}>
            <div className="ai-title">{toast.kind === "error" ? "Erro" : "OK"}</div>
            <div>{toast.msg}</div>
          </div>
        )}
        {toast && (
          <div role="status" aria-live="polite" style={{position:"fixed",right:16,bottom:16,background:"rgba(20,20,20,.95)",border:"1px solid #FFD166",color:"#fff",padding:"10px 14px",borderRadius:12,boxShadow:"0 8px 28px rgba(0,0,0,.45)"}}>
            <div style={{fontWeight:700,color: toast.kind === "error" ? "#ff6b6b" : "#06d6a0"}}>{toast.kind === "error" ? "Erro" : "OK"}</div>
            <div>{toast.msg}</div>
          </div>
        )}
        {toast && (
          <div role="status" aria-live="polite"
               style={{position:"fixed",right:16,bottom:16,zIndex:9999,
                       background:"rgba(20,20,20,.96)",color:"#fff",
                       border:"1px solid #FFD166",padding:"10px 14px",
                       borderRadius:12,boxShadow:"0 8px 28px rgba(0,0,0,.45)"}}>
            <div style={{fontWeight:700,color: toast.kind === "error" ? "#ff6b6b" : "#06d6a0"}}>
              {toast.kind === "error" ? "Erro" : "OK"}
            </div>
            <div>{toast.msg}</div>
          </div>
        )}
        {toast && (
          <div role="status" aria-live="polite"
               style={{position:"fixed",right:16,bottom:16,zIndex:9999,
                       background:"rgba(20,20,20,.96)",color:"#fff",
                       border:"1px solid #FFD166",padding:"10px 14px",
                       borderRadius:12,boxShadow:"0 8px 28px rgba(0,0,0,.45)"}}>
            <div style={{fontWeight:700,color: toast.kind === "error" ? "#ff6b6b" : "#06d6a0"}}>
              {toast.kind === "error" ? "Erro" : "OK"}
            </div>
            <div>{toast.msg}</div>
          </div>
        )}
        {err && (
          <div className="ai-answer" style={{ marginTop: 10 }}>
            <div className="ai-title">Erro</div>
            <div>{err}</div>
          </div>
        )}
      </section>

      <section className="card section">
        <h2>Histórico</h2>
        <div className="pix-summary">
          <span>Total Entradas: <strong>{fmtBR(totalEntradas)}</strong></span>
          <span>Total Saídas: <strong>{fmtBR(totalSaidas)}</strong></span>
        </div>

        {hist.length === 0 ? (
          <p>Sem lançamentos.</p>
        ) : (
          <ul className="pix-list">
            {hist.map((t) => (
              <li key={t.id} className={`pix-item ${t.tipo}`}>
                <div className="pix-left">
                  <div className="pix-desc">{t.descricao}</div>
                  <small className="pix-meta">
                    {t.timestamp ?? ""}{t.timestamp ? " · " : ""}{t.tipo === "entrada" ? "Entrada" : "Saída"}
                  </small>
                </div>
                <div className="pix-amount">{fmtBR(t.valor, t.tipo)}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {showModal && (
        <PixModal
          onClose={() => !sending && setShowModal(false)}
          onConfirm={handleSend}
          loading={sending}
        />
      )}

      {toast && <Toast kind={toast.kind} msg={toast.msg} onDone={() => setToast(null)} />}
    </main>
  );
}

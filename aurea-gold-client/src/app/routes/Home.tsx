import { useEffect, useState } from "react";
import Shell from "../layout/Shell";
import { useApi } from "../../lib/api";

type BalanceResp = { balance:number }
type Activity = { id:string; when:string; type:"IN"|"OUT"; description:string; amount:number }

function normalizeHistory(resp:any): Activity[] {
  const arr = Array.isArray(resp) ? resp
    : (resp?.items || resp?.data || resp?.results || resp?.history || []);
  return (arr as any[]).map((x:any)=>({
    id: String(x.id ?? (globalThis.crypto?.randomUUID?.() ?? Math.random())),
    when: String(x.when ?? x.date ?? x.created_at ?? new Date().toISOString()),
    type: (x.type ?? x.kind ?? x.direction ?? "OUT") as "IN"|"OUT",
    description: String(x.description ?? x.title ?? x.note ?? "Transação"),
    amount: Number(x.amount ?? x.value ?? 0),
  }));
}

export default function Home(){
  const api = useApi();
  const [balance,setBalance]=useState<number>(0);
  const [history,setHistory]=useState<Activity[]>([]);
  const [totIn,setTotIn]=useState<number>(0);
  const [totOut,setTotOut]=useState<number>(0);

  useEffect(()=>{
    let alive = true;
    (async ()=>{
      try{
        const b = await api.get("/api/v1/pix/balance");
        if(!alive) return;
        setBalance((b as BalanceResp)?.balance ?? Number((b as any)?.value ?? 0));
      }catch(e){ console.warn("balance err:", e); }

      try{
        const raw = await api.get("/api/v1/pix/history?limit=10");
        if(!alive) return;
        const arr = normalizeHistory(raw);
        setHistory(arr);
        setTotIn(arr.filter(x=>x.type==="IN").reduce((a,b)=>a+(b.amount||0),0));
        setTotOut(arr.filter(x=>x.type==="OUT").reduce((a,b)=>a+(b.amount||0),0));
      }catch(e){ console.warn("history err:", e); }
    })();
    return ()=>{ alive=false; };
  },[api]);

  const fmt=(v:number)=>v.toLocaleString("pt-BR",{style:"currency",currency:"BRL"});
  const safeHist = Array.isArray(history) ? history : [];

  return (
    <Shell>
      <div className="aurea-grid">
        <section className="card">
          <h1 className="card-title">Saldo</h1>
          <p className="card-sub">Visão geral da sua conta Aurea.</p>

          <div style={{display:"flex", gap:24, alignItems:"center", marginTop:6}}>
            <div style={{fontSize:42,fontWeight:800,background:'var(--g-gold)',WebkitBackgroundClip:'text',color:'transparent'}}>
              {fmt(balance)}
            </div>
            <ul style={{listStyle:"none", padding:0, margin:0, display:"grid", gap:6}}>
              <li className="chip">🟢 Entradas: {fmt(totIn)}</li>
              <li className="chip">🟡 Saídas: {fmt(totOut)}</li>
              <li className="chip">⚖️ Resultado: {fmt(totIn - totOut)}</li>
            </ul>
          </div>

          <div style={{display:"flex", gap:12, marginTop:18}}>
            <button className="btn btn-primary glow-gold">PIX</button>
            <button className="btn">Transferir</button>
          </div>
        </section>

        <section className="card">
          <h2 className="card-title">Atividade</h2>
          <p className="card-sub">Últimos lançamentos</p>
          <table className="table">
            <thead>
              <tr className="th">
                <th className="th">Data</th>
                <th className="th">Tipo</th>
                <th className="th">Descrição</th>
                <th className="th" style={{textAlign:"right"}}>Valor</th>
              </tr>
            </thead>
            <tbody>
              {safeHist.length===0 ? (
                <tr className="tr row-pill">
                  <td className="td" colSpan={4}><div className="skel skel-line" /></td>
                </tr>
              ) : safeHist.map(a=>(
                <tr key={a.id} className="tr row-pill">
                  <td className="td">{new Date(a.when).toLocaleString("pt-BR")}</td>
                  <td className="td">
                    <span className="chip" style={{borderColor: a.type==="IN"?"#22c55e":"#ef4444"}}>
                      {a.type==="IN"?"Entrada":"Saída"}
                    </span>
                  </td>
                  <td className="td">{a.description}</td>
                  <td className="td" style={{textAlign:"right", fontWeight:700}}>
                    {a.type==="IN" ? `+ ${fmt(a.amount)}` : `- ${fmt(a.amount)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>

      <section className="card" style={{marginTop:24}}>
        <h2 className="card-title">Transações</h2>
        <p className="card-sub">Histórico detalhado</p>
        <div className="table">
          {safeHist.slice(0,10).map(a=>(
            <div key={a.id} className="tr row-pill" style={{display:"grid", gridTemplateColumns:"1fr 120px 1fr 140px", gap:12}}>
              <div className="td">{new Date(a.when).toLocaleString("pt-BR")}</div>
              <div className="td">{a.type==="IN"?"Entrada":"Saída"}</div>
              <div className="td">{a.description}</div>
              <div className="td" style={{textAlign:"right"}}>{fmt(a.amount)}</div>
            </div>
          ))}
        </div>
      </section>
    </Shell>
  );
}

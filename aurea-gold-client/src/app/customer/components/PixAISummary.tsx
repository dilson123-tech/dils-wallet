import React, { useEffect, useState } from "react";

type Summary = { saldo_atual:number; entradas_total:number; saidas_total:number };

export default function PixAISummary({ apiBase }:{ apiBase:string }){
  const [sum,setSum] = useState<Summary|null>(null);
  const [msg,setMsg] = useState("IA 3.0 analisando dados…");
  const [cls,setCls] = useState("glow-yellow");

  useEffect(() => {
    (async () => {
      try{
        const r = await fetch(`${apiBase}/api/v1/ai/summary`);
        if(!r.ok) throw new Error();
        const d = await r.json(); setSum(d);
        if (d.saldo_atual > 0){ setMsg(`Tudo sob controle 💰 • Saldo R$ ${d.saldo_atual.toFixed(2)}`); setCls("glow-green"); }
        else if (d.saldo_atual === 0){ setMsg("Saldo zerado — hora de movimentar 💳"); setCls("glow-yellow"); }
        else { setMsg(`Atenção ⚠️ • Saldo negativo R$ ${Math.abs(d.saldo_atual).toFixed(2)}`); setCls("glow-red"); }
      }catch{ setMsg("IA 3.0 indisponível 🤖"); setCls("glow-red"); }
    })();
  },[apiBase]);

  return (
    <div className={`ag-ai ${cls}`} style={{color:"#f5d26b"}}>
      {msg}
    </div>
  );
}

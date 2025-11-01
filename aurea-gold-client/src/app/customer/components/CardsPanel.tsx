import React, { useState } from "react";

export default function CardsPanel() { console.log("[AUREA] CardsPanel render");
  const [masked, setMasked] = useState(true);
  const [locked, setLocked] = useState(false);

  const number = masked ? "**** **** **** 1234" : "4111 2222 3333 1234";
  const holder = "DILSON PEREIRA";
  const exp = "12/29";
  const cvv = masked ? "***" : "742";

  return (
    <div className="ag-card glow" style={{ marginTop: 20 }}>
      <h3 className="ag-title">Cartões • Aurea Card</h3>
      <div className="ag-body">
        <div style={{ display:"grid", gridTemplateColumns:"1fr", gap:16 }}>
          <div style={{
            background: "linear-gradient(135deg, rgba(212,175,55,.18), rgba(177,141,40,.12))",
            border: "1px solid rgba(212,175,55,.25)",
            borderRadius: "18px",
            padding: "18px",
            boxShadow: "0 20px 40px rgba(0,0,0,.25), inset 0 0 0 1px rgba(255,255,255,.04)"
          }}>
            <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
              <div style={{fontWeight:800,color:"#d4af37",letterSpacing:".06em"}}>AUREA GOLD</div>
              <div style={{fontSize:12,opacity:.85}}>{locked ? "🔒 BLOQUEADO" : "🟢 ATIVO"}</div>
            </div>
            <div style={{margin:"16px 0", fontSize:22, letterSpacing:".12em"}}>{number}</div>
            <div style={{display:"flex", gap:18, fontSize:14}}>
              <div><div className="small">TITULAR</div><div style={{fontWeight:700}}>{holder}</div></div>
              <div><div className="small">VALIDADE</div><div style={{fontWeight:700}}>{exp}</div></div>
              <div><div className="small">CVV</div><div style={{fontWeight:700}}>{cvv}</div></div>
            </div>
          </div>

          <div style={{display:"flex", gap:12, flexWrap:"wrap"}}>
            <button className="ag-btn" onClick={()=>setMasked(!masked)}>
              {masked ? "Revelar dados" : "Mascarar dados"}
            </button>
            <button className="ag-btn" onClick={()=>setLocked(!locked)}>
              {locked ? "Desbloquear" : "Bloquear"}
            </button>
            <button className="ag-btn" onClick={()=>alert("Em breve: gerar cartão virtual tokenizado.")}>
              Gerar cartão virtual
            </button>
          </div>

          <hr className="ag" />

          <div className="small">
            Em breve: múltiplos cartões (físico + virtuais), limites, tokenização,
            <br/>integração NFC/Wallet, faturas e API <code>/api/v1/cards</code>.
          </div>
        </div>
      </div>
    </div>
  );
}

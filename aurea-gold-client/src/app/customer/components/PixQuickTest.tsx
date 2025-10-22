import React from "react";
import { pixTransfer } from "@/lib/api";
import { makeIdem } from "@/lib/idempotency";

export default function PixQuickTest() {
  async function handleClick(){
    try{
      const idem = makeIdem("ui");
      const resp = await pixTransfer({ to: "ui-demo", amount: 1.23, currency: "BRL", description: "teste ui" }, idem);
      // dispara um evento global pra telas ouvirem e atualizarem saldo/histórico
      window.dispatchEvent(new CustomEvent("pix:updated", { detail: resp }));
      alert(`PIX OK\n${resp.transfer_id}\nNovo saldo: R$ ${resp.new_balance}`);
    }catch(e:any){
      alert(`Falhou: ${e?.message ?? e}`);
    }
  }
  return (
    <button
      onClick={handleClick}
      style={{
        position:"fixed", right:"16px", bottom:"16px", zIndex:9999,
        padding:"10px 14px", borderRadius:12, border:"1px solid #444",
        background:"#111", color:"#ffd166", boxShadow:"0 6px 16px rgba(0,0,0,.3)"
      }}
      title="Enviar PIX de teste (R$1,23)"
    >
      ⚡ PIX Test
    </button>
  );
}

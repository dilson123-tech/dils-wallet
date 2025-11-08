import React from "react";

export default function StatCard({
  title, value, hint
}: { title:string; value:string|number; hint?:string }) {
  return (
    <div className="aurea-card" style={{padding:12,minWidth:130}}>
      <div style={{opacity:.8,fontSize:12}}>{title}</div>
      <div style={{fontWeight:900,fontSize:22,marginTop:6,color:"#ffcc33"}}>{value}</div>
      {hint && <div style={{opacity:.6,fontSize:11,marginTop:4}}>{hint}</div>}
    </div>
  );
}

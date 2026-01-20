import React from "react";
import { Link, useLocation } from "react-router-dom";
import AureaIAConcierge from "@/app/customer/components/AureaIAConcierge";

export default function Shell({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const active = (p: string) => pathname === p;

  return (
    <div className="aurea-shell">
      {/* Sidebar */}
      <aside style={{
        position:"sticky", top:0, height:"100vh",
        background: "linear-gradient(180deg,#14110b 0%, #17130b 40%, #0f0d08 100%)",
        borderRight:"1px solid #2c240f", boxShadow:"inset -1px 0 0 #2c240f",
        padding:"18px 14px", display:"flex", flexDirection:"column", gap:14
      }}>
        <div style={{ fontWeight:800, letterSpacing:1, color:"#f4cc59" }}>AUREA GOLD • CLIENTE</div>

        <nav style={{ display:"grid", gap:6 }}>
          <Link to="/" style={linkStyle(active("/"))}>🏠 Dashboard</Link>
          <Link to="/pix" style={linkStyle(active("/pix"))}>⚡ PIX</Link>
          {/* <Link to="/ia" style={linkStyle(active("/ia"))}>🤖 IA 3.0</Link> */}
        </nav>

        <div style={{ marginTop:"auto", opacity:.8, fontSize:12 }}>
          v1.0 • Série Ouro
        </div>
      </aside>

      {/* Área principal */}
      <div style={{ display:"grid", gridTemplateRows:"64px 1fr", minWidth: 0 }}>
        {/* Topbar */}
        <header style={{
          position:"sticky", top:0, zIndex:10,
          display:"flex", alignItems:"center", gap:12,
          padding:"10px 16px",
          background:"rgba(10,10,10,.65)", backdropFilter:"blur(6px)",
          borderBottom:"1px solid #2c240f"
        }}>
          <span style={{ fontWeight:700, color:"#f0c75e" }}>Bem-vindo, Dilson IA 👑</span>
          <span style={{ marginLeft:"auto", opacity:.8 }}>Experiência Premium</span>
        </header>

        {/* Conteúdo */}
        <main className="aurea-content">
          {children}
        </main>
      </div>

      {/* Concierge IA 3.0 (fixo no canto) */}
      <AureaIAConcierge />
    </div>
  );
}

function linkStyle(active:boolean): React.CSSProperties {
  return {
    textDecoration:"none",
    color: active ? "#0b0b0b" : "#e8e0c7",
    background: active ? "linear-gradient(90deg,#f5d46b,#d3a62c)" : "transparent",
    border: active ? "1px solid #b4871b" : "1px solid transparent",
    padding:"10px 12px",
    borderRadius:10,
    fontWeight:600
  };
}

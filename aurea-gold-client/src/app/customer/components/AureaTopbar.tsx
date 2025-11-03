import React from "react";
import { Link } from "react-router-dom";

export default function AureaTopbar() {
  return (
    <header
      className="aurea-topbar"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: "60px",
        background: "linear-gradient(90deg, #000 0%, #1a1200 40%, #b88900 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        boxShadow: "0 0 12px rgba(255, 204, 51, 0.4)",
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{ fontWeight: "bold", color: "#ffcc33" }}>AUREA GOLD</span>
        <span style={{ fontSize: "0.8rem", color: "#ccc" }}>• CLIENTE</span>
      </div>

      <nav style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <Link to="/" style={{ color: "#ffcc33", textDecoration: "none" }}>
          Início
        </Link>
        <Link to="/pix" style={{ color: "#ffcc33", textDecoration: "none" }}>
          PIX
        </Link>
        <Link to="/ia" style={{ color: "#ffcc33", textDecoration: "none" }}>
          IA 3.0
        </Link>
      </nav>
    </header>
  );
}

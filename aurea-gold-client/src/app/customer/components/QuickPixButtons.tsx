import React from "react";

export default function QuickPixButtons() {
  const wrap: React.CSSProperties = {
    position: "fixed",
    right: 18,
    bottom: 96,
    zIndex: 70,
    display: "flex",
    gap: 8,
  };
  const btn: React.CSSProperties = {
    padding: "10px 14px",
    borderRadius: 10,
    border: "1px solid rgba(255,204,51,.35)",
    background: "rgba(0,0,0,.35)",
    color: "#ffcc33",
    fontWeight: 700,
    cursor: "pointer",
    backdropFilter: "blur(6px)",
  };

  function openPix() {
    window.dispatchEvent(new CustomEvent("aurea:open-pix"));
    console.log("[Aurea] abrir PIX");
  }
  function clearForm() {
    window.dispatchEvent(new CustomEvent("aurea:clear-pix"));
    console.log("[Aurea] limpar PIX");
  }

  return (
    <div style={wrap}>
    </div>
  );
}

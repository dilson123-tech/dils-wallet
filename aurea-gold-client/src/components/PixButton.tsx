import React from "react";

export default function PixButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        marginTop: "1rem",
        backgroundColor: "#d4af37",
        color: "#000",
        border: "none",
        borderRadius: "6px",
        fontWeight: 600,
        padding: "0.8rem 1.2rem",
        cursor: "pointer",
        width: "100%",
      }}
    >
      ✈ Fazer PIX
    </button>
  );
}

import React from "react";

type Props = {
  kind: "success" | "error" | "info";
  onClose: () => void;
  children: React.ReactNode;
};

export default function Toast({ kind, onClose, children }: Props) {
  return (
    <div
      role="alert"
      className={`toast ${kind}`}
      style={{
        position: "fixed",
        right: 16,
        bottom: 16,
        padding: "12px 16px",
        borderRadius: 8,
        background: kind === "success" ? "#064e3b"
                  : kind === "error" ? "#7f1d1d"
                  : "#1e293b",
        color: "white",
        boxShadow: "0 8px 20px rgba(0,0,0,.35)",
        zIndex: 9999
      }}
      onClick={onClose}
      title="Fechar"
    >
      {children}
    </div>
  );
}

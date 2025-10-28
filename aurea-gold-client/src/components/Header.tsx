import React from "react";
import { clearToken } from "../services/auth";

type HeaderProps = {
  name: string;
  onLogout: () => void;
};

export default function Header({ name, onLogout }: HeaderProps) {
  function handleLogout() {
    clearToken();
    onLogout();
  }

  const now = new Date();
  const time = now.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <header
      style={{
        backgroundColor: "#0a0a0a",
        border: "1px solid #222",
        borderRadius: "10px",
        padding: "0.8rem 1rem",
        marginBottom: "1.2rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        rowGap: "0.5rem",
      }}
    >
      <div>
        <span
          style={{
            color: "#d4af37",
            fontWeight: 700,
            fontSize: "0.95rem",
            display: "block",
          }}
        >
          Aurea Gold Premium
        </span>
        <span style={{ color: "#fff", fontSize: "0.8rem" }}>{name}</span>
      </div>

      <div style={{ textAlign: "right" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "0.3rem",
          }}
        >
          <span
            style={{
              width: "10px",
              height: "10px",
              borderRadius: "50%",
              backgroundColor: "#2ecc71",
              display: "inline-block",
            }}
          ></span>
          <span style={{ color: "#2ecc71", fontSize: "0.75rem" }}>Online</span>
        </div>

        <span
          style={{
            color: "#777",
            fontSize: "0.7rem",
            display: "block",
            marginBottom: "0.4rem",
          }}
        >
          Atualizado às {time}
        </span>

        <button
          onClick={handleLogout}
          style={{
            backgroundColor: "#d4af37",
            color: "#000",
            border: "none",
            borderRadius: "6px",
            padding: "0.3rem 0.6rem",
            fontSize: "0.75rem",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          Sair
        </button>
      </div>
    </header>
  );
}

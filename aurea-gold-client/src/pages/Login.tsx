import React, { useState } from "react";
import { loginRequest } from "../services/auth";

type Props = {
  onLoggedIn: () => void;
};

export default function Login({ onLoggedIn }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");

    try {
      await loginRequest(username, password);
      onLoggedIn();
    } catch (e: any) {
      console.error("login error:", e);
      setErr("Login inválido");
    }
  }

  return (
    <main
      style={{
        padding: "1rem",
        backgroundColor: "#000",
        color: "#fff",
        minHeight: "100vh",
        fontFamily: "sans-serif",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          backgroundColor: "#1a1a1a",
          border: "1px solid #333",
          borderRadius: "8px",
          padding: "1rem",
          width: "100%",
          maxWidth: "320px",
          display: "grid",
          gap: "0.75rem",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "baseline",
          }}
        >
          <span
            style={{
              color: "#d4af37",
              fontWeight: 600,
              fontSize: "0.9rem",
            }}
          >
            Aurea Gold Premium
          </span>
          <span
            style={{
              backgroundColor: "#d4af37",
              color: "#000",
              fontWeight: 600,
              borderRadius: "4px",
              fontSize: "0.7rem",
              lineHeight: 1,
              padding: "0.25rem 0.5rem",
            }}
          >
            acesso
          </span>
        </div>
        <label style={{ fontSize: "0.8rem", color: "#fff" }}>
          Usuário
          <input
            value={username}
            onChange={e => setUsername(e.target.value)}
            style={{
              width: "100%",
              marginTop: "0.3rem",
              backgroundColor: "#000",
              color: "#fff",
              border: "1px solid #555",
              borderRadius: "4px",
              fontSize: "0.8rem",
              padding: "0.5rem",
            }}
            placeholder="cliente1"
          />
        </label>

        <label style={{ fontSize: "0.8rem", color: "#fff" }}>
          Senha
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={{
              width: "100%",
              marginTop: "0.3rem",
              backgroundColor: "#000",
              color: "#fff",
              border: "1px solid #555",
              borderRadius: "4px",
              fontSize: "0.8rem",
              padding: "0.5rem",
            }}
            placeholder="••••••••"
          />
        </label>

        {err && (
          <div style={{ color: "#f55", fontSize: "0.75rem" }}>
            {err}
          </div>
        )}

        <button
          type="submit"
          style={{
            backgroundColor: "#d4af37",
            color: "#000",
            fontWeight: 600,
            borderRadius: "4px",
            fontSize: "0.8rem",
            padding: "0.6rem",
            border: "none",
            cursor: "pointer",
          }}
        >
          Entrar
        </button>

        <p
          style={{
            color: "#777",
            fontSize: "0.7rem",
            textAlign: "center",
            marginTop: "0.5rem",
          }}
        >
          Área segura • PIX 24h
        </p>
      </form>
    </main>
  );
}

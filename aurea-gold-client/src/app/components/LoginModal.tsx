import React, { useState } from "react";

export default function LoginModal() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const apiBase = import.meta.env.VITE_API_URL;

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    console.log("[AUREA] tentando login em", apiBase);

    try {
      const res = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: "POST",
        mode: "cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        console.warn("[AUREA] falha ao autenticar", res.status, txt);
        setErr(res.status === 401 ? "Credenciais inválidas." : "Falha no login");
        setLoading(false);
        return;
      }

      const data = await res.json().catch(() => ({}));
      console.log("[AUREA] login OK", data);

      if (data.access_token || data.token) {
        localStorage.setItem("access_token", data.access_token || data.token);
      }

      alert("Login bem-sucedido 🚀");
      setErr(null);
    } catch (err) {
      console.error("[AUREA] erro de conexão", err);
      setErr("Erro de conexão com o servidor.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {err && (
        <div style={{ color: "red", marginBottom: "0.5rem" }}>
          {err}
        </div>
      )}

      <form onSubmit={handleLogin} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          placeholder="usuário"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}

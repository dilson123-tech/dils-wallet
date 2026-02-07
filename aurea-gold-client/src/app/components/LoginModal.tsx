import React, { useEffect, useState } from "react";
import { login } from "../lib/auth";

export default function LoginModal() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState<number>(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => {
      setCooldown((s) => (s > 0 ? s - 1 : 0));
    }, 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);

    if (cooldown > 0) {
      setErr(`Aguarde ${cooldown}s antes de tentar de novo.`);
      return;
    }

    setLoading(true);

    try {
      const r = await login(username, password);

      if (!r.ok) {
        if (typeof r.retryAfter === "number" && r.retryAfter > 0) {
          setCooldown(r.retryAfter);
        }
        setErr(r.message || "Falha no login");
        return;
      }

      if (r.token) {
        // chave oficial (CORE procura essa primeiro)
        localStorage.setItem("aurea.access_token", r.token);
        // compat legado
        localStorage.setItem("access_token", r.token);
      }

      alert("Login bem-sucedido 🚀");
      setErr(null);
    } catch (e) {
      console.error("[AUREA] erro de login", e);
      setErr("Erro de conexão com o servidor.");
    } finally {
      setLoading(false);
    }
  }

  const disabled = loading || cooldown > 0;

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
        <button type="submit" disabled={disabled}>
          {loading ? "Entrando..." : cooldown > 0 ? `Aguarde ${cooldown}s` : "Entrar"}
        </button>
      </form>
    </div>
  );
}

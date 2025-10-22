import React, { useState } from "react";

export default function LoginModal({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const apiBase = import.meta.env.VITE_API_BASE;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        let msg = "Falha ao autenticar. Verifique suas credenciais.";
        try {
          const err = await res.json();
          if (err?.detail) msg = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
        } catch {}
        setError(msg);
        setLoading(false);
        return;
      }

      const data = await res.json();
      if (data?.access_token) {
        localStorage.setItem("access_token", data.access_token);
      }
      setLoading(false);
      onSuccess();
    } catch {
      setError("Erro de conexão com o servidor.");
      setLoading(false);
    }
  };

  return (
    <div className="bg-neutral-900 text-white p-6 rounded-xl shadow-lg w-[380px]">
      <h2 className="text-xl font-semibold mb-4 text-center">
        Acesse sua conta Aurea Gold.
      </h2>
      {error && (
        <div className="bg-red-600/20 border border-red-400 text-red-300 p-2 rounded-md text-sm mb-3 text-center">
          {error}
        </div>
      )}
      <form onSubmit={handleLogin} className="flex flex-col gap-3">
        <input
          type="email"
          placeholder="E-mail"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="p-2 rounded-md bg-neutral-800 text-white border border-neutral-700 focus:outline-none"
          required
        />
        <input
          type="password"
          placeholder="Senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="p-2 rounded-md bg-neutral-800 text-white border border-neutral-700 focus:outline-none"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className={`mt-3 p-2 rounded-md bg-gradient-to-r from-yellow-600 to-yellow-400 text-black font-semibold hover:opacity-90 transition ${
            loading ? "opacity-70 cursor-wait" : ""
          }`}
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}

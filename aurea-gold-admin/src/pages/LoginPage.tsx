import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { errorMessage, isAdmin, login, logout, whoami } from "../lib/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      await login(username.trim(), password);
      const user = await whoami();
      if (!isAdmin(user)) {
        await logout();
        setError("Acesso negado: esta conta não é de administrador.");
        return;
      }
      navigate("/admin/users", { replace: true });
    } catch (err) {
      await logout();
      setError(errorMessage(err));
    } finally {
      setPassword("");
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-slate-950 text-white">
      <h1 className="text-3xl font-bold text-yellow-500 mb-2">Aurea Gold Admin</h1>
      <p className="mb-6">Acesso restrito a administradores</p>
      <form onSubmit={handleLogin} className="flex flex-col gap-3 w-72">
        <input
          type="text"
          autoComplete="username"
          placeholder="E-mail ou usuário"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          className="px-3 py-2 rounded bg-white/5 border border-white/10 focus:outline-none focus:border-yellow-500"
        />
        <input
          type="password"
          autoComplete="current-password"
          placeholder="Senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="px-3 py-2 rounded bg-white/5 border border-white/10 focus:outline-none focus:border-yellow-500"
        />
        {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold py-2 px-6 rounded shadow-lg transition disabled:opacity-60"
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}

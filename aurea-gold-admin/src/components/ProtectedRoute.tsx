import { useEffect, useState } from "react";
import { Link, Navigate, Outlet } from "react-router-dom";
import { getAccessToken } from "../lib/api";
import { errorMessage, httpStatus, isAdmin, logout, whoami } from "../lib/auth";

type Status = "loading" | "admin" | "denied" | "anon" | "error";

// Exige token e confirma no servidor (whoami) que o usuário é admin.
export default function ProtectedRoute() {
  const hasToken = !!getAccessToken();
  const [status, setStatus] = useState<Status>(hasToken ? "loading" : "anon");
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!hasToken) return;
    let active = true;
    setStatus("loading");
    whoami()
      .then(async (user) => {
        if (isAdmin(user)) {
          if (active) setStatus("admin");
          return;
        }
        await logout();
        if (active) setStatus("denied");
      })
      .catch((err) => {
        if (!active) return;
        if (httpStatus(err) === 401) {
          setStatus("anon");
          return;
        }
        setError(errorMessage(err));
        setStatus("error");
      });
    return () => { active = false; };
  }, [hasToken, attempt]);

  if (status === "anon") return <Navigate to="/login" replace />;
  if (status === "admin") return <Outlet />;

  return (
    <div className="carbon-bg min-h-screen pt-24 pb-10">
      <div className="max-w-md mx-auto px-4">
        <div className="glass-card p-6 text-center">
          {status === "loading" && <p className="text-slate-300">Verificando acesso...</p>}
          {status === "denied" && (
            <>
              <p className="text-red-400 font-semibold mb-4">Acesso negado: esta conta não é de administrador.</p>
              <Link to="/login" replace className="gold-button gold-shine">Voltar ao login</Link>
            </>
          )}
          {status === "error" && (
            <>
              <p role="alert" className="text-red-400 mb-4">{error}</p>
              <button onClick={() => setAttempt((n) => n + 1)} className="gold-button gold-shine">Tentar novamente</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

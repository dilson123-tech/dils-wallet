import React, { useState, useEffect } from "react";
import { AppShell, AppTab } from "./AppShell";
import SuperAureaHome from "./super2/SuperAureaHome";
import AureaPixPanel from "./super2/AureaPixPanel";
import AureaGestaoPanel from "./gestao/AureaGestaoPanel";
import AureaPagamentosPanel from "./pagamentos/AureaPagamentosPanel";
import AureaMaisPanel from "./mais/AureaMaisPanel";
import PlanosPremium from "./super2-lab/PlanosPremium";
import {
  saveTokens,
  clearTokens,
  logoutServer,
} from "./auth/authClient";
import { bootstrapSession } from "./auth/bootstrapSession";
import { login as loginCore } from "./app/lib/auth";

const isPlanosLab =
  typeof window !== "undefined" &&
  window.location.pathname.includes("planos");

function PlanosLabApp() {
  return <PlanosPremium />;
}

interface AureaAppShellProtectedProps {
  onLogout: () => void;
}

function AureaAppShellProtected({ onLogout }: AureaAppShellProtectedProps) {
  const [activeTab, setActiveTab] = useState<AppTab>("home");
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [pixInitialAction, setPixInitialAction] = useState<
    "send" | "charge" | "statement" | null
  >(null);

  const handleTabChange = (tab: AppTab) => {
    if (tab === activeTab) return;

    setIsTransitioning(true);

    setTimeout(() => {
      setActiveTab(tab);
      setIsTransitioning(false);
    }, 500);
  };

  const handleHomePixShortcut = (action: "enviar" | "receber" | "extrato") => {
    let next: "send" | "charge" | "statement" | null = null;

    if (action === "enviar") {
      next = "send";
    } else if (action === "extrato") {
      next = "statement";
    } else if (action === "receber") {
      next = "charge";
    }

    setPixInitialAction(next);
    handleTabChange("pix");
  };

  let content: React.ReactNode;

  switch (activeTab) {
    case "home":
      content = (
        <main className="w-full pb-4 md:pb-6">
          <SuperAureaHome onPixShortcut={handleHomePixShortcut} onLogout={onLogout} />
        </main>
      );
      break;

    case "pix":
      content = (
        <div className="w-full px-1 py-4 md:px-2 md:py-6 mx-auto">
          <AureaPixPanel initialAction={pixInitialAction} />
        </div>
      );
      break;

    case "gestao":
      content = (
        <div className="w-full px-1 py-4 md:px-2 md:py-6 mx-auto">
          <AureaGestaoPanel />
        </div>
      );
      break;

    case "pagamentos":
      content = (
        <div className="w-full px-1 py-4 md:px-2 md:py-6 mx-auto">
          <AureaPagamentosPanel />
        </div>
      );
      break;

    case "mais":
      content = (
        <div className="w-full px-1 py-4 md:px-2 md:py-6 mx-auto">
          <AureaMaisPanel />
        </div>
      );
      break;

    default:
      content = null;
  }

  return (
    <AppShell
      activeTab={activeTab}
      onTabChange={handleTabChange}
      isSplash={isTransitioning}
    >
      {content}

      {activeTab === "mais" && (
        <div className="mt-4 w-full flex justify-end px-1 md:px-2">
          <button
            type="button"
            onClick={onLogout}
            className="ag-btn-secondary px-4 py-2 text-[10px] uppercase tracking-[0.18em]"
          >
            Sair da Aurea Gold
          </button>
        </div>
      )}
    </AppShell>
  );
}

function AureaAppWithAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authChecking, setAuthChecking] = useState(true);

  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginCooldown, setLoginCooldown] = useState<number>(0);

  // 429 no refresh da abertura: sessão mantida, sem retry automático
  const [authTransient, setAuthTransient] = useState(false);

  async function checkSession(isCancelled: () => boolean = () => false) {
    setAuthChecking(true);
    const r = await bootstrapSession();
    if (isCancelled()) return;
    setIsAuthenticated(r === "authenticated");
    setAuthTransient(r === "transient");
    setAuthChecking(false);
  }

  useEffect(() => {
    let cancelled = false;
    void checkSession(() => cancelled);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (loginCooldown <= 0) return;
    const t = setInterval(() => {
      setLoginCooldown((s) => (s > 0 ? s - 1 : 0));
    }, 1000);
    return () => clearInterval(t);
  }, [loginCooldown]);

  async function handleLoginSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoginError(null);

    if (loginCooldown > 0) {
      setLoginError(`Aguarde ${loginCooldown}s antes de tentar de novo.`);
      return;
    }

    setLoginLoading(true);

    try {
      const r = await loginCore(loginUsername.trim(), loginPassword);

      if (!r.ok) {
        if (typeof (r as any).retryAfter === "number" && (r as any).retryAfter > 0) {
          setLoginCooldown((r as any).retryAfter);
        }
        setLoginError((r as any).message || "Falha ao autenticar. Tente novamente.");
        return;
      }

      if (!(r as any).token) {
        setLoginError("Login OK, mas token não veio.");
        return;
      }

      setLoginCooldown(0);
      // persiste o refresh_token da resposta do login (usado no refresh automático)
      let refreshToken: string | null = null;
      try {
        const rt = JSON.parse((r as any).raw || "{}")?.refresh_token;
        if (typeof rt === "string" && rt) refreshToken = rt;
      } catch {}
      saveTokens((r as any).token, refreshToken);
      setIsAuthenticated(true);
    } catch (err: any) {
      setLoginError(err?.message || "Falha ao autenticar. Tente novamente.");
    } finally {
      setLoginLoading(false);
    }
  }

  function handleLogout() {
    // lê o refresh token antes de clearTokens(); não espera a resposta
    void logoutServer();
    clearTokens();
    setIsAuthenticated(false);
    setLoginUsername("");
    setLoginPassword("");
  }

  if (authChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="ag-surface-elevated w-full max-w-md px-8 py-10 text-center">
          <div className="mx-auto mb-4 h-12 w-12 rounded-full border border-[rgba(212,175,55,0.34)] border-t-transparent animate-spin" />
          <div className="text-[10px] tracking-[0.32em] ag-gold-text uppercase">
            Aurea Gold
          </div>
          <div className="mt-3 text-sm ag-subtitle">
            Carregando ambiente seguro da carteira...
          </div>
        </div>
      </div>
    );
  }

  if (authTransient) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="ag-surface-elevated w-full max-w-md px-8 py-10 text-center">
          <div className="text-[10px] tracking-[0.32em] ag-gold-text uppercase">
            Aurea Gold
          </div>
          <div className="mt-3 text-sm ag-subtitle">
            Não foi possível confirmar sua sessão agora. Aguarde alguns instantes e tente novamente.
          </div>
          <div className="mt-6 flex flex-col gap-3">
            <button
              type="button"
              onClick={() => void checkSession()}
              className="ag-btn-primary w-full px-4 py-3 text-[11px] uppercase tracking-[0.22em]"
            >
              Tentar novamente
            </button>
            <button
              type="button"
              onClick={() => setAuthTransient(false)}
              className="ag-btn-secondary w-full px-4 py-2 text-[10px] uppercase tracking-[0.18em]"
            >
              Entrar com usuário e senha
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-8">
        <div className="ag-surface-elevated w-full max-w-[420px] px-6 py-6 md:px-8 md:py-8">
          <header className="space-y-2">
            <div className="pl-2 pt-1 text-[10px] tracking-[0.30em] uppercase ag-gold-text">
              Aurea Gold • Carteira Digital
            </div>

            <h1 className="text-2xl font-semibold ag-title">
              Acesso seguro à sua carteira
            </h1>

            <p className="text-xs leading-relaxed ag-subtitle">
              Entre com seu usuário e senha para acessar saldo, PIX, crédito IA 3.0
              e o painel completo da Aurea Gold.
            </p>
          </header>

          <form className="mt-6 space-y-4" onSubmit={handleLoginSubmit}>
            <div className="space-y-1.5">
              <label className="text-[11px] uppercase tracking-[0.16em] ag-muted">
                Usuário
              </label>
              <input
                type="text"
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                className="w-full rounded-xl border border-[rgba(212,175,55,0.16)] bg-[rgba(255,255,255,0.02)] px-3 py-3 text-[13px] text-white outline-none transition focus:border-[rgba(212,175,55,0.34)]"
                placeholder="Ex.: cliente.aurea"
                autoComplete="username"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] uppercase tracking-[0.16em] ag-muted">
                Senha
              </label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="w-full rounded-xl border border-[rgba(212,175,55,0.16)] bg-[rgba(255,255,255,0.02)] px-3 py-3 text-[13px] text-white outline-none transition focus:border-[rgba(212,175,55,0.34)]"
                placeholder="●●●●●●●●"
                autoComplete="current-password"
              />
            </div>

            {loginError && (
              <p className="text-[11px] text-rose-300">{loginError}</p>
            )}

            <button
              type="submit"
              disabled={loginLoading || loginCooldown > 0 || !loginUsername || !loginPassword}
              className="ag-btn-primary w-full px-4 py-3 text-[11px] uppercase tracking-[0.22em] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loginLoading
                ? "Entrando..."
                : loginCooldown > 0
                ? `Aguarde ${loginCooldown}s`
                : "Entrar na Aurea Gold"}
            </button>

            <p className="pt-1 text-[10px] leading-relaxed ag-soft">
              Este acesso é destinado ao ambiente interno da Aurea Gold. As operações
              exibidas podem estar em modo demonstração e têm caráter consultivo.
            </p>
          </form>
        </div>
      </div>
    );
  }

  return <AureaAppShellProtected onLogout={handleLogout} />;
}

export default function App() {
  if (isPlanosLab) {
    return <PlanosLabApp />;
  }

  return <AureaAppWithAuth />;
}

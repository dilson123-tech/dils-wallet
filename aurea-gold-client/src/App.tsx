import React, { useState, useEffect } from "react";
import { AppShell, AppTab } from "./AppShell";
import SuperAureaHome from "./super2/SuperAureaHome";
import AureaPixPanel from "./super2/AureaPixPanel";
import AureaIAPanel from "./super2/AureaIAPanel";
import AureaPagamentosPanel from "./pagamentos/AureaPagamentosPanel";
import AureaCreditoIAPanel from "./credito/AureaCreditoIAPanel";
import PlanosPremium from "./super2-lab/PlanosPremium";
import {
  saveTokens,
  getAccessToken,
  clearTokens,
} from "./auth/authClient";
import { login as loginCore } from "./app/lib/auth";

const isPlanosLab =
  typeof window !== "undefined" &&
  window.location.pathname.includes("planos");

function PlanosLabApp() {
  return (
    <div className="min-h-screen text-white">
      <main className="w-full px-4 py-6 mx-auto max-w-6xl">
        <PlanosPremium />
      </main>
    </div>
  );
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
        <>
          <header className="mb-6 md:mb-8">
            <div className="ag-hero px-4 py-5 md:px-6 md:py-6">
              <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                <div className="flex flex-col gap-2 max-w-2xl">
                  <span className="text-[10px] md:text-xs uppercase tracking-[0.30em] ag-gold-text">
                    Aurea Gold • Financial Interface
                  </span>

                  <h1 className="text-2xl md:text-3xl font-semibold ag-title leading-tight">
                    Seu centro premium de operações financeiras
                  </h1>

                  <p className="text-sm md:text-base ag-subtitle leading-relaxed">
                    Ambiente seguro para saldo, PIX, pagamentos e inteligência aplicada,
                    com percepção visual premium e operação orientada à confiança.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 min-w-[280px] md:min-w-[360px]">
                  <div className="ag-card px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.22em] ag-soft">
                      Status da conta
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-400" />
                      <span className="text-sm font-semibold text-white">
                        Operacional
                      </span>
                    </div>
                    <div className="mt-1 text-[11px] ag-subtitle">
                      Ambiente autenticado e pronto para movimentações.
                    </div>
                  </div>

                  <div className="ag-card px-4 py-3">
                    <div className="text-[10px] uppercase tracking-[0.22em] ag-soft">
                      Segurança
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="inline-block h-2.5 w-2.5 rounded-full bg-[var(--ag-gold-strong)]" />
                      <span className="text-sm font-semibold text-white">
                        Monitorada
                      </span>
                    </div>
                    <div className="mt-1 text-[11px] ag-subtitle">
                      Sessão protegida com fluxo controlado de autenticação.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </header>

          <main className="w-full pb-4 md:pb-6 overflow-x-auto">
            <SuperAureaHome onPixShortcut={handleHomePixShortcut} />
          </main>
        </>
      );
      break;

    case "pix":
      content = (
        <div className="w-full px-1 py-4 md:px-2 md:py-6 mx-auto">
          <AureaPixPanel initialAction={pixInitialAction} />
        </div>
      );
      break;

    case "ia":
      content = (
        <div className="w-full px-1 py-4 md:px-2 md:py-6 mx-auto">
          <AureaIAPanel />
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

    case "credito-ia":
      content = (
        <div className="w-full px-1 py-4 md:px-2 md:py-6 mx-auto">
          <AureaCreditoIAPanel />
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

      <div className="mt-4 w-full flex justify-end px-1 md:px-2">
        <button
          type="button"
          onClick={onLogout}
          className="ag-btn-secondary px-4 py-2 text-[10px] uppercase tracking-[0.18em]"
        >
          Sair da Aurea Gold
        </button>
      </div>
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

  useEffect(() => {
    const token = getAccessToken();
    setIsAuthenticated(!!token);
    setAuthChecking(false);
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
      saveTokens((r as any).token);
      setIsAuthenticated(true);
    } catch (err: any) {
      setLoginError(err?.message || "Falha ao autenticar. Tente novamente.");
    } finally {
      setLoginLoading(false);
    }
  }

  function handleLogout() {
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

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 py-8">
        <div className="ag-surface-elevated w-full max-w-md px-6 py-6 md:px-8 md:py-8">
          <header className="space-y-2">
            <div className="text-[10px] tracking-[0.30em] uppercase ag-gold-text">
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

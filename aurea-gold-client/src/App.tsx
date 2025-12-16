import React, { useState, useEffect } from "react";
import { AppShell, AppTab } from "./AppShell";
import SuperAureaHome from "./super2/SuperAureaHome";
import AureaPixPanel from "./super2/AureaPixPanel";
import AureaIAPanel from "./super2/AureaIAPanel";
import AureaPagamentosPanel from "./pagamentos/AureaPagamentosPanel";
import AureaCreditoIAPanel from "./credito/AureaCreditoIAPanel";
import PlanosPremium from "./super2-lab/PlanosPremium";
import {
  login as loginRequest,
  saveTokens,
  getAccessToken,
  clearTokens,
} from "./auth/authClient";
// import PanelReceitasReservasLab from "./pagamentos/PanelReceitasReservasLab";

const isPlanosLab =
  typeof window !== "undefined" &&
  window.location.pathname.includes("planos");

// ==============================
// Versão especial: Planos
// ==============================
function PlanosLabApp() {
  return (
    <div className="min-h-screen bg-black text-zinc-50">
      <main className="w-full px-4 py-6 mx-auto max-w-6xl">
        <PlanosPremium />
      </main>
    </div>
  );
}

// ==============================
// App protegido (tabs, PIX, IA, etc)
// ==============================
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
          {/* HEADER APP OFICIAL */}
          <header className="mb-6 md:mb-8">
            <div className="text-[10px] md:text-xs border-b border-zinc-800 pb-4 uppercase tracking-wide flex flex-col md:flex-row md:items-center md:justify-between gap-1">
              <span className="font-bold leading-tight">
                AUREA GOLD • CARTEIRA DIGITAL
              </span>
              <span className="text-[9px] md:text-[10px] text-amber-300">
                Versão IA 3.0 • Ambiente interno
              </span>
            </div>
            <div className="h-px w-40 md:w-64 bg-amber-500 mt-2" />
          </header>

          {/* MAIN CONTENT */}
          <main className="w-full pb-4 md:pb-6 overflow-x-auto">
            <SuperAureaHome onPixShortcut={handleHomePixShortcut} />
            {/* <PanelReceitasReservasLab /> */}
          </main>
        </>
      );
      break;

    case "pix":
      content = (
        <div className="w-full px-4 py-6 mx-auto">
          <AureaPixPanel initialAction={pixInitialAction} />
        </div>
      );
      break;

    case "ia":
      content = (
        <div className="w-full px-4 py-6 mx-auto">
          <AureaIAPanel />
        </div>
      );
      break;

    case "pagamentos":
      content = (
        <div className="w-full px-4 py-6 mx-auto">
        <AureaPagamentosPanel />
        </div>
      );
      break;

    case "credito-ia":
      content = (
        <div className="w-full px-4 py-6 mx-auto">
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

      <div className="mt-4 w-full flex justify-end px-4">
        <button
          type="button"
          onClick={onLogout}
          className="text-[10px] text-zinc-500 hover:text-zinc-300 underline underline-offset-4"
        >
          Sair da Aurea Gold
        </button>
      </div>
    </AppShell>
  );
}

// ==============================
// App com autenticação (login + tokens)
// ==============================
function AureaAppWithAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authChecking, setAuthChecking] = useState(true);

  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    setIsAuthenticated(!!token);
    setAuthChecking(false);
  }, []);

  async function handleLoginSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoginError(null);
    setLoginLoading(true);

    try {
      const tokens = await loginRequest({
        username: loginUsername.trim(),
        password: loginPassword,
      });

      saveTokens((tokens as any).access_token ?? (tokens as any).token ?? JSON.stringify(tokens));
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
      <div className="min-h-screen flex items-center justify-center bg-black text-zinc-200">
        <div className="text-center space-y-2">
          <div className="text-xs tracking-[0.28em] text-amber-400 uppercase">
            Aurea Gold
          </div>
          <div className="text-sm text-zinc-300">
            Carregando ambiente seguro da carteira...
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-zinc-950 via-black to-zinc-900 text-zinc-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-amber-500/30 bg-black/80 p-6 shadow-xl shadow-amber-950/30 space-y-5">
          <header className="space-y-1">
            <div className="text-[10px] tracking-[0.3em] uppercase text-amber-400">
              Aurea Gold • Carteira Digital
            </div>
            <h1 className="text-xl font-semibold">
              Acesso seguro à sua carteira
            </h1>
            <p className="text-[11px] text-zinc-400">
              Entre com seu usuário e senha para acessar saldo, PIX, crédito IA
              3.0 e painel completo da Aurea.
            </p>
          </header>

          <form className="space-y-4" onSubmit={handleLoginSubmit}>
            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-[0.16em] text-zinc-400">
                Usuário
              </label>
              <input
                type="text"
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                className="w-full rounded-md border border-zinc-700 bg-black/70 px-3 py-2 text-[12px] outline-none focus:border-amber-500"
                placeholder="Ex.: cliente.aurea"
                autoComplete="username"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] uppercase tracking-[0.16em] text-zinc-400">
                Senha
              </label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="w-full rounded-md border border-zinc-700 bg-black/70 px-3 py-2 text-[12px] outline-none focus:border-amber-500"
                placeholder="●●●●●●●●"
                autoComplete="current-password"
              />
            </div>

            {loginError && (
              <p className="text-[11px] text-rose-300">{loginError}</p>
            )}

            <button
              type="submit"
              disabled={loginLoading || !loginUsername || !loginPassword}
              className="w-full rounded-full border border-amber-500/80 bg-amber-500/20 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-200 hover:bg-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loginLoading ? "Entrando..." : "Entrar na Aurea Gold"}
            </button>

            <p className="text-[10px] text-zinc-500 leading-relaxed">
              Este acesso é destinado ao ambiente interno da Aurea Gold. As
              operações exibidas podem estar em modo demonstração e têm caráter
              consultivo.
            </p>
          </form>
        </div>
      </div>
    );
  }

  return <AureaAppShellProtected onLogout={handleLogout} />;
}

// ==============================
// Componente raiz: escolhe LAB x App oficial
// ==============================
export default function App() {
  if (isPlanosLab) {
    return <PlanosLabApp />;
  }

  return <AureaAppWithAuth />;
}

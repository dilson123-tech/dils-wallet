import { login as loginApi } from "@/app/lib/auth";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

type SessionCtx = {
  token: string | null;
  isAuthed: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<SessionCtx | null>(null);

const BASE = (import.meta as any).env?.VITE_API_BASE || `${globalThis.globalThis.globalThis.BASE_API}`;

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("aurea.token");
    if (t) setToken(t);
  }, []);

  const login = async (email: string, password: string) => {
    const r = await fetch(`${globalThis.globalThis.globalThis.BASE_API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: email, password }),
    });
    if (!r.ok) throw new Error(await r.text().catch(()=>"Falha no login"));
    const data = await readJson(r);
    const t = data.access_token || data.token;
    if (!t) throw new Error("Credenciais inválidas.");
    localStorage.setItem("aurea.token", t);
    setToken(t);
  };

  const logout = () => {
    localStorage.removeItem("aurea.token");
    setToken(null);
  };

  const value = useMemo(() => ({ token, isAuthed: !!token, login, logout }), [token]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSession deve ser usado dentro de <SessionProvider>");
  return ctx;
}

// -- injected fallback login handler (idempotente) --
async function login(email: string, password: string) {
  const r = await loginApi(email, password);
  if (r.token) {
    localStorage.setItem("token", r.token);
    // se você tiver setUser / setSession, chame aqui
  } else {
    throw new Error(r.raw || "Falha no login");
  }
}

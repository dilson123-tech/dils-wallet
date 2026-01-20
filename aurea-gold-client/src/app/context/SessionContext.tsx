import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { login as loginApi } from "@/app/lib/auth";

type SessionCtx = {
  token: string | null;
  isAuthed: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<SessionCtx | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("aurea.token");
    if (t) setToken(t);
  }, []);

  const login = async (username: string, password: string) => {
    const user = username.trim();
    const pass = password.trim();

    // usa a função de login já testada (apiPost -> /api/v1/auth/login)
    const res = await loginApi(user, pass);

    if (!res.ok || !res.token) {
      throw new Error("Credenciais inválidas.");
    }

    localStorage.setItem("aurea.token", res.token);
    setToken(res.token);
  };

  const logout = () => {
    localStorage.removeItem("aurea.token");
    setToken(null);
  };

  const value = useMemo(
    () => ({ token, isAuthed: !!token, login, logout }),
    [token],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession() {
  const ctx = useContext(Ctx);
  if (!ctx) {
    throw new Error("useSession deve ser usado dentro de <SessionProvider>");
  }
  return ctx;
}

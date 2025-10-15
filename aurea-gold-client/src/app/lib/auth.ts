import { apiPost } from "./api";

type AnyObj = Record<string, any>;
export type LoginResult = { token?: string; email?: string; user?: any; raw?: string };

function pickToken(r: AnyObj): string | undefined {
  if (!r || typeof r !== "object") return undefined;
  if (typeof r.token === "string") return r.token;
  if (typeof r.access_token === "string") return r.access_token;
  if (r.data && typeof r.data.token === "string") return r.data.token;
  if (r.data && typeof r.data.access_token === "string") return r.data.access_token;
  return undefined;
}

function pickEmail(r: AnyObj, fallback?: string): string | undefined {
  if (!r || typeof r !== "object") return fallback;
  if (typeof r.email === "string") return r.email;
  if (r.user && typeof r.user.email === "string") return r.user.email;
  if (r.data && typeof r.data.email === "string") return r.data.email;
  return fallback;
}

export async function login(email: string, password: string): Promise<LoginResult> {
  const res = await apiPost("/auth/login", { body: { email, password } });

  // se não for JSON, apiPost retorna { raw }
  if (res && typeof res === "object" && "raw" in res) {
    return res as LoginResult;
  }

  const token = pickToken(res as AnyObj);
  const mail  = pickEmail(res as AnyObj, email);

  if (token) {
    saveSession(token, mail);
    return { token, email: mail, user: (res as AnyObj).user };
  }
  // nada de token -> retorna bruto pra UI exibir erro amigável
  return { raw: JSON.stringify(res ?? null) };
}

export function saveSession(token: string, email?: string) {
  localStorage.setItem("token", token);
  if (email) localStorage.setItem("email", email);
}
export function getToken(): string | null { return localStorage.getItem("token"); }
export function getEmail(): string | null { return localStorage.getItem("email"); }
export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("email");
}

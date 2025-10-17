import { BASE_API } from "./api";

export type LoginOk = { ok: true; token: string };
export type LoginErr = { ok: false; message: string };

export async function login(email: string, password: string): Promise<LoginOk | LoginErr> {
  const res = await fetch(`${BASE_API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit",
    body: JSON.stringify({ email, password })
  });

  // tenta ler como JSON; se vier texto/HTML por erro, cai no catch
  let data: any = null;
  try { data = await res.json(); } catch { /* noop */ }

  if (res.ok) {
    const token = data?.access_token || data?.token;
    if (typeof token === "string" && token.length > 0) {
      return { ok: true, token };
    }
    return { ok: false, message: "Login OK mas sem token na resposta." };
  }

  // mensagens amigáveis
  const msg =
    data?.detail?.toString?.() ||
    (typeof data === "string" ? data : "") ||
    `HTTP ${res.status}`;
  return { ok: false, message: msg };
}

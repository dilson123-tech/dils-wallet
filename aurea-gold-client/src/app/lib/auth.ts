import { BASE_API } from "./api";

export type PromiseLogin = { ok: boolean; token?: string; message?: string };

export async function login(email: string, password: string): PromiseLogin {
  try {
    const r = await fetch(`${BASE_API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const txt = await r.text();
    const data = txt ? JSON.parse(txt) : {};
    if (!r.ok) throw new Error(data?.detail || "Falha no login");

    const token =
      data?.access_token || data?.token || data?.jwt || data?.accessToken || null;
    if (!token) throw new Error("Login OK mas sem token na resposta.");

    localStorage.setItem("aurea.token", String(token));
    return { ok: true, token: String(token) };
  } catch (err: any) {
    return { ok: false, message: err?.message || "Erro ao autenticar." };
  }
}

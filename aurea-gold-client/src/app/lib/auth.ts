import { apiPostJson } from "./api";

export type PromiseLogin = { ok: boolean; token?: string; message?: string };

export async function login(email: string, password: string): PromiseLogin {
  const data = await apiPostJson("/auth/login", { email, password });
  if (!data) return { ok: false, message: "Falha no login" };
  if (typeof data === "string") return { ok: false, message: data };
  if (!data.access_token) return { ok: false, message: "Sem token na resposta." };
  return { ok: true, token: data.access_token };
}

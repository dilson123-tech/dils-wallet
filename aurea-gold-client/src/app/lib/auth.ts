import { apiPost, readJsonSafe } from "./api";

export type PromiseLogin = { ok: boolean; token?: string; message?: string };

export async function login(email: string, password: string): Promise<PromiseLogin> {
  const res = await apiPost("/auth/login", { email, password });
  const data = await readJsonSafe(res);
  if (!res.ok) {
    const msg = (data && (data.message || data.detail)) || `Login falhou (${res.status})`;
    return { ok: false, message: msg };
  }
  const token = (data && (data.access_token || data.token)) as string | undefined;
  return token ? { ok: true, token } : { ok: false, message: "Token ausente na resposta." };
}

import { toApi } from "./api";

const KEY = "aurea.jwt";

export function setToken(tok: string) {
  localStorage.setItem(KEY, tok);
}
export function getToken(): string | null {
  return localStorage.getItem(KEY);
}
export function clearToken() {
  localStorage.removeItem(KEY);
}

export async function login(email: string, password: string) {
  const r = await fetch(toApi("/api/v1/api/v1/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) {
    const t = await r.text().catch(()=> "");
    throw new Error(`login failed (${r.status}): ${t}`);
  }
  const j = await r.json();
  if (j?.access_token) setToken(j.access_token);
  return j;
}

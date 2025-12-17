const __isJwt = (t: any) =>
  typeof t === "string" && t.length >= 120 && t.split(".").length === 3;

const __pickToken = (...cands: Array<string | null | undefined>) => {
  for (const c of cands) if (__isJwt(c)) return c as string;
  return "";
};

import { API_BASE } from "./api";
import { apiGet } from "./api";

const KEY = "aurea.jwt";

export function setToken(tok: string) {
  localStorage.setItem(KEY, tok);
}
export function getToken(): string {
  return __pickToken(
    localStorage.getItem("aurea.jwt"),
    localStorage.getItem("aurea_jwt"),
    localStorage.getItem("aurea.access_token"),
    localStorage.getItem("aurea_access_token"),
    localStorage.getItem("authToken"),
    localStorage.getItem("aurea_token"),
    localStorage.getItem("token"),
  );
}

export function clearToken() {
  localStorage.removeItem(KEY);
}

export async function login(email: string, password: string) {
  const r = await fetch(`${API_BASE}/api/v1/auth/login`, {
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

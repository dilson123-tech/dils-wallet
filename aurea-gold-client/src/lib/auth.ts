import { getAccessToken, saveAccessToken, clearAccessTokenForThisOrigin } from "./tokenVault";
const __isJwt = (t: any) =>
  typeof t === "string" && t.length >= 120 && t.split(".").length === 3;

const __pickToken = (...cands: Array<string | null | undefined>) => {
  for (const c of cands) if (__isJwt(c)) return c as string;
  return "";
};

import { API_BASE } from "./api";

// ✅ Fonte única oficial do token
const OFFICIAL = "aurea.access_token";

// ✅ lista de chaves legadas que a gente ainda aceita ler/limpar
const LEGACY_KEYS = [
  "aurea.jwt",
  "aurea_jwt",
  "aurea_access_token",
  "authToken",
  "aurea_token",
  "token",
  "USER_TOKEN",
  "aurea_token",
  "aurea.refresh_token",
  "aurea_refresh_token",
];

export function setToken(tok: string) {
  try { localStorage.setItem(OFFICIAL, tok); } catch {}

  // compat (temporário): grava também em alguns legados pra não quebrar telas antigas
  try { localStorage.setItem("aurea_access_token", tok); } catch {}
  try { localStorage.setItem("authToken", tok); } catch {}
  try { localStorage.setItem("aurea.jwt", tok); } catch {}
}

export function getToken() {
  return getAccessToken();
}

export function authHeaders(): Record<string, string> {
  const tok = getToken();
  if (tok && tok !== "null" && tok !== "undefined") {
    return { Authorization: `Bearer ${tok}` };
  }
  return {} as Record<string, string>;
}


export function clearToken() {
  // apaga oficial + todos os legados (mata token velho assombrando o app)
  try { localStorage.removeItem(OFFICIAL); } catch {}
  for (const k of LEGACY_KEYS) {
    try { localStorage.removeItem(k); } catch {}
  }
}

// ✅ login no contrato do backend: {username, password}
export async function login(emailOrUsername: string, password: string) {
  const r = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: emailOrUsername, password }),
  });

  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(`login failed (${r.status}): ${t}`);
  }

  const j = await r.json();
  if (j?.access_token) setToken(j.access_token);
  return j;
}

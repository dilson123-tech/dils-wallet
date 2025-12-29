import { getToken } from "./auth";
// ======================================================
// AUREA GOLD • CORE HTTP LIB
// Seguro, simples e com Authorization automático
// ======================================================

export const API_BASE: string = String(import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000").replace(/\/+$|\s+/g, "");
export const USER_EMAIL = import.meta.env.VITE_USER_EMAIL || "";

// Tenta pegar token de vários lugares (compat com versões antigas)
function clearTokenKeys() {
  try {
    ["aurea.access_token","aurea_access_token","aurea.jwt","aurea_jwt","authToken"].forEach(k => localStorage.removeItem(k));
  } catch {}
}

function base64UrlDecode(s: string): string {
  const pad = "=".repeat((4 - (s.length % 4)) % 4);
  const b64 = (s + pad).replace(/-/g, "+").replace(/_/g, "/");
  try { return atob(b64); } catch { return ""; }
}

function jwtExpMs(tok: string): number | null {
  const parts = tok.split(".");
  if (parts.length !== 3) return null;
  const payload = base64UrlDecode(parts[1]);
  if (!payload) return null;
  try {
    const j = JSON.parse(payload);
    if (typeof j?.exp === "number") return j.exp * 1000;
  } catch {}
  return null;
}

// Escolhe o MELHOR token válido (evita 401 intermitente quando há tokens velhos no storage)
function pickToken(): string | null {
  if (typeof window === "undefined") return null;

  const keys = [
    "aurea.access_token",
    "aurea_access_token",
    "aurea.jwt",
    "aurea_jwt",
    "authToken",
  ];

  const now = Date.now();
  const cands: { tok: string; expMs: number | null; key: string }[] = [];

  for (const k of keys) {
    const raw = localStorage.getItem(k);
    if (!raw) continue;
    if (raw === "[object Object]") continue;

    let v = raw.trim();
    if (!v) continue;

    // às vezes salvaram JSON inteiro do login
    if (v.startsWith("{")) {
      try {
        const j = JSON.parse(v);
        if (typeof j?.access_token === "string") v = j.access_token;
        else if (typeof j?.token === "string") v = j.token;
        else continue;
      } catch { continue; }
    }

    if (v.length < 40) continue;

    const exp = jwtExpMs(v);
    cands.push({ tok: v, expMs: exp, key: k });
  }

  if (cands.length === 0) return null;

  // preferir JWT não-expirado com maior exp
  const jwt = cands
    .filter(c => c.tok.split(".").length === 3)
    .filter(c => c.expMs === null || c.expMs > now + 15000)
    .sort((a,b) => (b.expMs || 0) - (a.expMs || 0));

  if (jwt.length > 0) return jwt[0].tok;

  // fallback: qualquer JWT
  const anyJwt = cands.filter(c => c.tok.split(".").length === 3);
  if (anyJwt.length > 0) return anyJwt[0].tok;

  return cands[0].tok;
}


// Aplica Authorization + X-User-Email (se existir)
export function withAuth(init: RequestInit = {}): RequestInit {
  const headers = new Headers(init.headers || {});
  const token = pickToken();

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (USER_EMAIL && USER_EMAIL.trim() !== "" && !headers.has("X-User-Email")) {
    headers.set("X-User-Email", USER_EMAIL);
  }

  return { ...init, headers };
}

// -----------------------------
// GET genérico
// -----------------------------
export async function apiGet<T>(path: string, init: RequestInit = {}): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, withAuth(init));
  if (!r.ok) { if (r.status === 401) clearTokenKeys(); throw new Error(`GET ${path} -> ${r.status}`); }
  return r.json() as Promise<T>;
}

// -----------------------------
// POST genérico
// -----------------------------
export async function apiPost<TReq, TRes>(
  path: string,
  body: TReq,
  init: RequestInit = {}
): Promise<TRes> {
  const headers = new Headers(init.headers || {});
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  const r = await fetch(`${API_BASE}${path}`, withAuth({
    ...init,
    method: "POST",
    headers,
    body: JSON.stringify(body),
  }));

  if (!r.ok) { if (r.status === 401) clearTokenKeys(); throw new Error(`POST ${path} -> ${r.status}`); }
  return r.json() as Promise<TRes>;
}

// -----------------------------
// GET • PIX BALANCE
// -----------------------------
export async function getPixBalance(): Promise<{ saldo?: number }> {
  return apiGet<{ saldo?: number }>("/api/v1/pix/balance");
}

import { getToken } from "./auth";
// ======================================================
// AUREA GOLD • CORE HTTP LIB
// Seguro, simples e com Authorization automático
// ======================================================

const FALLBACK_API_BASE: string =
  typeof window !== "undefined"
    ? `http://${window.location.hostname}:8000`
    : "http://127.0.0.1:8000";

export const API_BASE: string = String(import.meta.env.VITE_API_BASE || FALLBACK_API_BASE).replace(/\/+$|\s+/g, "");
export const USER_EMAIL = import.meta.env.VITE_USER_EMAIL || "";

export const DEV_TOKEN: string = String(import.meta.env.VITE_DEV_TOKEN || "").trim();
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

    const devTok = DEV_TOKEN;



  // DEV: força token do env (ótimo pra celular/rede) — ignora tokens velhos do storage
  if (DEV_TOKEN && DEV_TOKEN.length > 40) return DEV_TOKEN;

  // prioridade: chave oficial primeiro (evita 401 por token legado inválido)
  const keys = [
    "aurea.access_token", // oficial
    "aurea_access_token",
    "aurea.jwt",
    "aurea_jwt",
    "authToken",
  ];

  const now = Date.now();

  function normalize(raw: string | null): string | null {
    if (!raw) return null;
    if (raw === "[object Object]") return null;

    let v = raw.trim();
    if (!v) return null;

    // às vezes salvaram JSON inteiro do login
    if (v.startsWith("{")) {
      try {
        const j = JSON.parse(v);
        if (typeof j?.access_token === "string") v = j.access_token;
        else if (typeof j?.token === "string") v = j.token;
        else return null;
      } catch {
        return null;
      }
    }

    if (v.length < 40) return null;
    return v;
  }

  // escolhe o primeiro JWT não-expirado seguindo a ordem de prioridade
  for (const k of keys) {
    const v = normalize(localStorage.getItem(k));
    if (!v) continue;
    if (v.split(".").length !== 3) continue;

    const exp = jwtExpMs(v);
    if (exp !== null && exp <= now + 15000) continue; // expirado/expirando
    return v;
  }

  // fallback: qualquer JWT na ordem
  for (const k of keys) {
    const v = normalize(localStorage.getItem(k));
    if (!v) continue;
    if (v.split(".").length === 3) return v;
  }

  // último recurso: qualquer token "comprido" (legado)
  for (const k of keys) {
    const v = normalize(localStorage.getItem(k));
    if (v) return v;
  }

  return null;
}


// Aplica Authorization + X-User-Email (se existir)
export function withAuth(init: RequestInit = {}): RequestInit {
  const headers = new Headers(init.headers || {});
  const token = pickToken();

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const hasAuth = headers.has("Authorization") || headers.has("authorization");


  if (!hasAuth && USER_EMAIL && USER_EMAIL.trim() !== "" && !headers.has("X-User-Email")) {


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

// ======================================================
// AUREA GOLD • CORE HTTP LIB
// Seguro, simples e com Authorization automático
// ======================================================

export const API_BASE = import.meta.env.VITE_API_BASE || "";
export const USER_EMAIL = import.meta.env.VITE_USER_EMAIL || "";

// Tenta pegar token de vários lugares (compat com versões antigas)
function pickToken(): string | null {
  if (typeof window === "undefined") return null;

  const keys = [
    "aurea.access_token",   // (novo)
    "aurea_access_token",   // (alguns fluxos antigos)
    "aurea.jwt",
    "aurea_jwt",
  ];

  for (const k of keys) {
    const raw = localStorage.getItem(k);
    if (!raw) continue;

    // bug clássico: setItem com objeto vira "[object Object]"
    if (raw === "[object Object]") continue;

    const v = raw.trim();

    // às vezes salvaram JSON inteiro do login
    if (v.startsWith("{")) {
      try {
        const j = JSON.parse(v);
        if (typeof j?.access_token === "string") return j.access_token;
        if (typeof j?.token === "string") return j.token;
      } catch {}
      continue;
    }

    // JWT padrão
    if (v.includes(".") && v.split(".").length === 3) return v;

    // fallback: algum token não-JWT
    return v;
  }

  return null;
}

// Aplica Authorization + X-User-Email (se existir)
function withAuth(init: RequestInit = {}): RequestInit {
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
  if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
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

  if (!r.ok) throw new Error(`POST ${path} -> ${r.status}`);
  return r.json() as Promise<TRes>;
}

// -----------------------------
// GET • PIX BALANCE
// -----------------------------
export async function getPixBalance(): Promise<{ saldo?: number }> {
  return apiGet<{ saldo?: number }>("/api/v1/pix/balance");
}

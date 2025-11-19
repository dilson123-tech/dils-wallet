// ======================================================
// AUREA GOLD • CORE HTTP LIB
// Arquivo limpo, reconstruído, seguro e tipado
// ======================================================

export const API_BASE = import.meta.env.VITE_API_BASE || "";
export const USER_EMAIL = import.meta.env.VITE_USER_EMAIL || "";

// -----------------------------
// GET genérico
// -----------------------------
export async function apiGet<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    ...init,
  });

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
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(init.headers || {}),
  };

  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    ...init,
    headers,
    body: JSON.stringify(body),
  });

  if (!r.ok) throw new Error(`POST ${path} -> ${r.status}`);
  return r.json() as Promise<TRes>;
}

// -----------------------------
// GET • PIX BALANCE
// -----------------------------
export async function getPixBalance(): Promise<{ saldo?: number }> {
  const headers: HeadersInit =
    USER_EMAIL && USER_EMAIL.trim() !== ""
      ? { "X-User-Email": USER_EMAIL }
      : {};

  return apiGet<{ saldo?: number }>("/api/v1/pix/balance", { headers });
}

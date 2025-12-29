// ======================================================
// AUREA GOLD • APP API (LEGACY) — FONTE ÚNICA
// Mantém imports antigos, mas delega pro CORE (src/lib/api.ts)
// que injeta Authorization automaticamente.
// ======================================================

import { apiGet as coreGet, apiPost as corePost } from "../../lib/api";
import { getToken } from "../../lib/auth";

// Fallback local (evita API_BASE vazio derrubar calls)
export const API_BASE: string =
  (import.meta as any).env?.VITE_API_BASE ||
  "http://127.0.0.1:8000";

export function toApi(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const joined = `${API_BASE}${path}`.replace(/\/{2,}/g, "/");
  return joined.replace("https:/", "https://");
}

export async function apiGet(path: string, init: RequestInit = {}) {
  // URL absoluta: respeita (não força CORE)
  if (path.startsWith("http://") || path.startsWith("https://")) {
    const tok = getToken();
      const headers = new Headers((init as any).headers || {});
      if (tok && !headers.has("Authorization")) headers.set("Authorization", `Bearer ${tok}`);
      const res = await fetch(path, { ...init, method: "GET", mode: "cors", headers });
    if (!res.ok) {
      const txt = await res.text().catch(() => "");
      throw new Error(`[GET ${path}] ${res.status} ${txt.slice(0, 200)}`);
    }
    return res.json();
  }
  return coreGet<any>(path, init);
}

export async function apiPost(path: string, body: any, init: RequestInit = {}) {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    const res = await fetch(path, {
      ...init,
      method: "POST",
      mode: "cors",
      headers: {
        "Content-Type": "application/json",
        ...(init.headers || {}),
      },
      body: JSON.stringify(body),
    });

    const raw = await res.text().catch(() => "");
    if (!res.ok) throw new Error(`[POST ${path}] ${res.status} ${raw.slice(0, 200)}`);

    try { return JSON.parse(raw); } catch { return {}; }
  }

  return corePost<any, any>(path, body, init);
}

// Compat default export (evita quebrar imports antigos)
const api_default = {} as any;
export default api_default;

export const API_BASE = import.meta.env.VITE_API_BASE || "";
export const USER_EMAIL = import.meta.env.VITE_USER_EMAIL || "";

export async function apiGet<T>(path: string, init: RequestInit = {}): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "X-User-Email": USER_EMAIL,
      ...(init.headers || {}),
    },
  });
  if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
  return r.json() as Promise<T>;
}

// Shim p/ componentes legados que importam getPixSummary de "@/lib/api"
export async function getPixSummary() {
  return apiGet("/api/v1/ai/summary");
}

export const API_BASE = ((import.meta || {}).env && (import.meta as any).env.VITE_API_BASE) || "http://127.0.0.1:8080";

export async function apiGet(path, email) {
  const headers = {}; if (email) headers["X-User-Email"] = email;
  const r = await fetch(`${API_BASE}${path}`, { method: "GET", headers });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r;
}

export async function getPixSummary(hours = 24) {
  const r = await fetch(`${API_BASE}/api/v1/ai/summary?hours=${hours}`, { method: "GET" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

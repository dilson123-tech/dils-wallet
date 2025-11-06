const env = (import.meta as any).env;
export const API_BASE = env.VITE_API_BASE || "http://127.0.0.1:8080";

export async function getPixSummary(hours = 24) {
  const r = await fetch(`${API_BASE}/api/v1/ai/summary?hours=${hours}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

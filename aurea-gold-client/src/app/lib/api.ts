const API_BASE = import.meta.env.VITE_API_BASE;

if (!API_BASE) {
  console.warn("[AUREA FRONT] VITE_API_BASE não definido. Usando fallback http://localhost:8000");
}

export function toApi(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const joined = `${API_BASE}${path}`.replace(/\/{2,}/g, "/");
  return joined.replace("https:/", "https://");
}

export async function apiGet(path: string, init: RequestInit = {}) {
  const url = toApi(path);
  const res = await fetch(url, {
    ...init,
    method: "GET",
    mode: "cors",
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`[GET ${url}] ${res.status} ${txt.slice(0,200)}`);
  }

  return res.json();
}

export async function apiPost(path: string, body: any, init: RequestInit = {}) {
  const url = toApi(path);
  const res = await fetch(url, {
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

  if (!res.ok) {
    throw new Error(`[POST ${url}] ${res.status} ${raw.slice(0,200)}`);
  }

  let json: any = {};
  try { json = JSON.parse(raw); } catch { /* ignore */ }

  return json;
}

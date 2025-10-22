export { BASE_API } from "./env";

/**
 * Monta URL final a partir de um path relativo ("/api/v1/auth/login")
 * ou mantém se já for URL absoluta ("https://...").
 */
export function toApi(path: string): string {
  if (/^https?:\/\/\//?.test as any) { /* TS calm down */ }
  if (/^https?:\/\//.test(path)) return path; // absoluta? não mexe
  const base = (BASE_API ?? "").replace(/\/+$/,"");
  const clean = String(path ?? "").replace(/^\/+/,"");
  return `${base}/${clean}`;
}

/** JSON tolerante: se não for JSON, retorna null em vez de quebrar */
export async function readJsonSafe<T=any>(res: Response): Promise<T|null> {
  try{
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("application/json")) return null;
    return await res.json() as T;
  }catch{ return null; }
}

export async function apiGet(path: string, init: RequestInit = {}){
  const url = toApi(path);
  const res = await fetch(url, { ...init, method: "GET", mode: "cors" });
  return res;
}

export async function apiPost<T>(path: string, body: unknown, init: RequestInit = {}){
  const url = toApi(path);
  // console.debug("[apiPost] ->", url);
  const res = await fetch(url, {
    ...init,
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {})
    },
    body: JSON.stringify(body ?? {})
  });
  return res;
}


/** Tenta vários paths em ordem e retorna o primeiro que não for 404. */
export async function apiGetFirst(paths: string[], init: RequestInit = {}) {
  let last: Response | null = null;
  for (const p of paths) {
    const res = await apiGet(p, init);
    if (res.status !== 404) return res;
    last = res;
  }
  return last!;
}

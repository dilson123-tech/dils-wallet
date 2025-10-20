export { BASE_API } from "./env";

/**
 * Monta URL final a partir de um path relativo ("/auth/login")
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

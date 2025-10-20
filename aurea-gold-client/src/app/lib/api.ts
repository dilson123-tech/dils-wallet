export { BASE_API } from "./env";

/** junta base + path removendo/ajustando barras duplicadas */
export function joinUrl(base: string, p: string): string {
  const b = (base || "").replace(/\/+$/, "");
  const s = String(p || "").replace(/^\/+/, "");
  return `${b}/${s}`;
}

/** aceita path relativo ("*/auth/login*") ou URL absoluta ("https://…") */
export function toApi(path: string): string {
  const s = String(path || "");
  return /^https?:\/\//i.test(s) ? s : joinUrl(BASE_API, s);
}

/** lê JSON com tolerância: se não for JSON, retorna texto ou null */
export async function readJsonSafe(res: Response): Promise<any> {
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  const txt = await res.text();
  if (!/application\/json/i.test(ct)) return txt || null;
  try { return txt ? JSON.parse(txt) : null; } catch { return null; }
}

export async function apiGet(path: string, init: RequestInit = {}) {
  const url = toApi(path);
  const res = await fetch(url, { ...init, method: "GET", mode: "cors" });
  return res;
}

export async function apiPost(path: string, body: any, init: RequestInit = {}) {
  const url = toApi(path);
  const res = await fetch(url, {
    method: "POST",
    mode: "cors",
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    body: JSON.stringify(body ?? {}),
    ...init,
  });
  return res;
}

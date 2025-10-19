import { BASE_API } from "./env";

export function joinApi(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;           // já é absoluta
  const p = path.startsWith("/") ? path : `/${path}`;    // garante uma barra
  return `${BASE_API}${p}`;
}

// lê JSON com tolerância (string/204/HTML => null)
export async function readJsonSafe(res: Response): Promise<any> {
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  const txt = await res.text();
  if (!ct.includes("application/json")) return txt ? null : null;
  try { return txt ? JSON.parse(txt) : null; } catch { return null; }
}

export async function apiGet(path: string) {
  const url = joinApi(path);
  const r = await fetch(url, { mode: "cors" });
  return readJsonSafe(r);
}

export async function apiPostJson(path: string, body: any) {
  const url = joinApi(path);
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    mode: "cors",
  });
  return readJsonSafe(r);
}

export { BASE_API }; // re-export para quem precisar

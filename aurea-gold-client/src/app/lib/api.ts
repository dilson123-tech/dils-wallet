import { BASE_API } from "./env";

/** Junta BASE_API + path sem duplicar ou quebrar barras */
function joinUrl(base: string, path: string) {
  const b = base.endsWith("/") ? base : base + "/";
  const p = path.startsWith("/") ? path.slice(1) : path;
  return new URL(p, b).toString();
}

/** Lê JSON com tolerância (se vier HTML/texto, devolve string) */
export async function readJsonSafe(res: Response) {
  const ct = res.headers.get("content-type") || "";
  const txt = await res.text();
  if (!ct.toLowerCase().includes("application/json")) {
    return txt; // não é JSON — devolve texto bruto (ex.: HTML de erro)
  }
  try { return txt ? JSON.parse(txt) : null; } catch { return txt; }
}

export async function login(email: string, password: string) {
  const url = joinUrl(BASE_API, "/auth/login");
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    credentials: "omit",
    mode: "cors",
  });

  const data = await readJsonSafe(r);
  if (!r.ok) {
    const msg =
      typeof data === "string"
        ? data.slice(0, 200)
        : (data as any)?.detail || `Login falhou (${r.status})`;
    throw new Error(msg);
  }

  const token =
    (data as any)?.access_token ||
    (data as any)?.token ||
    (data as any)?.accessToken;

  if (!token) throw new Error("Login OK, mas sem token na resposta.");
  try { localStorage.setItem("aurea.token", String(token)); } catch {}
  return token as string;
}

/** GET simples usando a mesma base (útil para saldo/histórico) */
export async function apiGet(path: string) {
  const url = joinUrl(BASE_API, path);
  const r = await fetch(url, { credentials: "omit", mode: "cors" });
  if (r.status === 204) return null;
  const data = await readJsonSafe(r);
  if (!r.ok) {
    const msg = typeof data === "string" ? data.slice(0, 200) : `GET ${r.status}`;
    throw new Error(msg);
  }
  return data;
}

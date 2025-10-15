import { readJson } from "@/app/lib/http";
const BASE_API = String(import.meta.env.VITE_API_BASE);

type Opts = {
  token?: string;
  body?: any;
  headers?: Record<string, string>;
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
};

function headers(token?: string, extra?: Record<string, string>) {
  return {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(extra || {}),
  };
}

/**
 * Fetch resiliente: trata 204, só parseia JSON quando Content-Type é JSON
 * e inclui snippet do corpo em erros HTTP.
 */
async function apiFetch(path: string, opts: Opts = {}) {
  const method = opts.method ?? 'GET';
  const res = await fetch(`${BASE_API}${path}`, {
    method,
    headers: headers(opts.token, opts.headers),
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: 'omit',
    mode: 'cors',
  });

  // 204 No Content
  if (res.status === 204) return null;

  const ct = res.headers.get('content-type') || '';
  const text = await res.text();

  if (!res.ok) {
    const snippet = text?.slice(0, 300);
    throw new Error(`${method} ${path} -> ${res.status} ${res.statusText} :: ${snippet}`);
  }

  if (ct.includes('application/json')) {
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (e) {
      throw new Error(
        `JSON parse fail em ${method} ${path}: ${(e as Error).message} :: body="${text.slice(0, 200)}"`
      );
    }
  }

  // Não-JSON: retorna bruto sem quebrar a UI
  return { raw: text };
}

export const apiGet  = (path: string, opts?: Omit<Opts, 'method'>) =>
  apiFetch(path, { ...(opts || {}), method: 'GET' });

export const apiPost = (path: string, opts?: Omit<Opts, 'method'>) =>
  apiFetch(path, { ...(opts || {}), method: 'POST' });

export { BASE_API };

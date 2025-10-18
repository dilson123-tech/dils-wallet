import { readJson } from "./json";

export const BASE_API = String(import.meta.env.VITE_API_BASE || window.BASE_API || "");

type Opts = { token?: string; body?: any; headers?: Record<string,string> };

function jsonHeaders(extra?: Record<string,string>) {
  return { 'Content-Type': 'application/json', ...(extra||{}) };
}

export async function apiGet(path: string, opts: Opts = {}) {
  const url = path.startsWith('http') ? path : `${BASE_API}${path}`;
  const r = await fetch(url, { headers: opts.headers });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return readJson(r);
}

export async function apiPost(path: string, opts: Opts = {}) {
  const url = path.startsWith('http') ? path : `${BASE_API}${path}`;
  const r = await fetch(url, {
    method: 'POST',
    headers: jsonHeaders(opts.headers),
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: 'omit',
    mode: 'cors',
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return readJson(r);
}

export async function login(email: string, password: string) {
  const data = await apiPost('/auth/login', { body: { email, password }});
  const token = (data as any)?.token ?? (data as any)?.access_token ?? (data as any)?.accessToken ?? null;
  if (!token) throw new Error('Login OK mas sem token na resposta.');
  localStorage.setItem('aurea.token', String(token));
  return token;
}

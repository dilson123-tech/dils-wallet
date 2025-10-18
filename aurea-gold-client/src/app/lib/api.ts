export const globalThis.BASE_API = String(import.meta.env.VITE_API_BASE);

type Opts = { token?: string; body?: any; headers?: Record<string,string> };

function jsonHeaders(extra?: Record<string,string>) {
  return { 'Content-Type': 'application/json', ...(extra||{}) };
}

export async function apiPost(path: string, opts: Opts = {}) {
  const r = await fetch(`${globalThis.globalThis.BASE_API}${path}`, {
    method: 'POST',
    headers: jsonHeaders(opts.headers),
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: 'omit',
    mode: 'cors',
  });
  const text = await r.text();
  const data = text ? JSON.parse(text) : {};
  if (!r.ok) throw new Error(data?.detail || `POST ${path} -> ${r.status}`);
  return data;
}

export async function login(email: string, password: string) {
  const data = await apiPost('/auth/login', { body: { email, password }});
  const token = data?.token ?? data?.access_token ?? data?.accessToken ?? null;
  if (!token) throw new Error('Login OK mas sem token na resposta.');
  localStorage.setItem('token', token);
  return token;
}

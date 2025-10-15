const BASE_API = String(import.meta.env.VITE_API_BASE);

type Opts = { token?: string; body?: any; headers?: Record<string,string> };

function h(token?: string, extra?: Record<string,string>) {
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(extra || {})
  };
}

export async function apiGet(path: string, opts: Opts = {}) {
  const r = await fetch(`${BASE_API}${path}`, {
    method: 'GET',
    headers: h(opts.token),
    credentials: 'omit',
    mode: 'cors'
  });
  if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
  return r.json();
}

export async function apiPost(path: string, opts: Opts = {}) {
  const r = await fetch(`${BASE_API}${path}`, {
    method: 'POST',
    headers: h(opts.token),
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: 'omit',
    mode: 'cors'
  });
  if (!r.ok) throw new Error(`POST ${path} -> ${r.status}`);
  return r.json();
}

export { BASE_API };

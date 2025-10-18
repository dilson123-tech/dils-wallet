import { BASE_API } from './env';

export async function apiGet(path: string) {
  const url = path.startsWith('http') ? path : `${BASE_API}${path}`;
  const res = await fetch(url);
  if (res.status === 204) return null;
  const ct = res.headers.get('content-type') || '';
  const txt = await res.text();
  if (!ct.includes('application/json')) return txt || null;
  try { return txt ? JSON.parse(txt) : null; } catch { return null; }
}

import { BASE_API } from './env';

export async function apiGet(path: string) {
  const url = path.startsWith('http') ? path : `${BASE_API}${path}`;
  const res = await fetch(url);
  if (res.status === 204) return null;
  const ct = res.headers.get('content-type') || '';
  const body = await res.text();
  if (!ct.includes('application/json')) return body || null;
  try { return body ? JSON.parse(body) : null; } catch { return null; }
}

// Centraliza a base de API vinda do Railway
const RAW = (import.meta as any).env?.VITE_API_BASE || '';
export const API_BASE = RAW.replace(/\/+$/,''); // sem barra final

export function toApi(path: string) {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${p}`;
}

// (Opcional) fetch wrapper com headers padrão
export async function apiGet(path: string, token?: string) {
  const r = await fetch(toApi(path), {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return r;
}

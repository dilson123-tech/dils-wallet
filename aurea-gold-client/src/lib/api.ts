// Centraliza a base da API via env de build (Vite)
const RAW = (import.meta as any).env?.VITE_API_BASE || '';
export const API_BASE: string = (RAW ?? '').replace(/\/+$/,''); // sem barra final

export function toApi(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${p}`;
}

// Helpers diretos (opcional)
export async function apiGet(path: string, token?: string) {
  const r = await fetch(toApi(path), {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  return r;
}

export async function apiPost(path: string, body?: any, token?: string) {
  const r = await fetch(toApi(path), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body != null ? JSON.stringify(body) : undefined
  });
  return r;
}

// Hook compatível com imports existentes (Home.tsx usa { useApi })
export function useApi() {
  return {
    base: API_BASE,
    toApi,
    get: apiGet,
    post: apiPost,
  };
}

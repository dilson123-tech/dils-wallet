import { API_BASE } from "./config";

export function toApi(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;

  // 1) Se já vier absoluto (/api/...), respeita
  if (p.startsWith('/api/')) return `${API_BASE}${p}`;

  // 2) Compat: rotas antigas de PIX sem prefixo
  if (p === '/balance' || p.startsWith('/balance?')) {
    return `${API_BASE}/api/v1/pix/balance${p.includes('?') ? `?${p.split('?')[1]}` : ''}`;
  }
  if (p === '/history' || p.startsWith('/history?')) {
    return `${API_BASE}/api/v1/pix/history${p.includes('?') ? `?${p.split('?')[1]}` : ''}`;
  }

  // 3) Compat: se vier "/pix/..." sem /api/v1
  if (p.startsWith('/pix/')) return `${API_BASE}${p.replace(/^\/pix\//, '/api/v1/pix/')}`;

  // 4) Fallback geral: prefixa /api/v1
  return `${API_BASE}/api/v1${p}`;
}

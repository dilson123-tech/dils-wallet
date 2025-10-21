const RAW = (import.meta as any).env?.VITE_API_BASE || '';
const API_BASE = (RAW ?? '').replace(/\/+$/,'');

function rewrite(u: string): string {
  if (/^https?:\/\//i.test(u)) return u;
  const p = u.startsWith('/') ? u : `/${u}`;

  if (p.startsWith('/api/')) return `${API_BASE}${p}`;

  if (p === '/balance' || p.startsWith('/balance?')) {
    const qs = p.includes('?') ? p.slice(p.indexOf('?')) : '';
    return `${API_BASE}/api/v1/pix/balance${qs}`;
  }
  if (p === '/history' || p.startsWith('/history?')) {
    const qs = p.includes('?') ? p.slice(p.indexOf('?')) : '';
    return `${API_BASE}/api/v1/pix/history${qs}`;
  }

  if (p.startsWith('/pix/')) return `${API_BASE}${p.replace(/^\/pix\//, '/api/v1/pix/')}`;
  return `${API_BASE}/api/v1${p}`;
}

const _fetch = window.fetch.bind(window);
window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof input === 'string' ? rewrite(input) : rewrite(input.url);
  return _fetch(url, init);
};

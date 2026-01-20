const RAW = (import.meta as any).env?.VITE_API_BASE || '';
const API_BASE = (RAW ?? '').replace(/\/+$/,'');

function rewriteRelative(p: string): string {
  if (p.startsWith('/api/')) return `${API_BASE}${p}`;

  if (p === '/balance' || p.startsWith('/balance?')) {
    const qs = p.includes('?') ? p.slice(p.indexOf('?')) : '';
    return `${API_BASE}/balance${qs}`;
  }
  if (p === '/history' || p.startsWith('/history?')) {
    const qs = p.includes('?') ? p.slice(p.indexOf('?')) : '';
    return `${API_BASE}/api/v1/pix/list${qs}`;
  }
  if (p.startsWith('/pix/')) return `${API_BASE}${p.replace(/^\/pix\//, '/api/v1/pix/')}`;

  // fallback conservador
  return `${API_BASE}${p}`;
}

function rewrite(input: string): string {
  // Absoluta?
  if (/^https?:\/\//i.test(input)) {
    const u = new URL(input);

    // já é /api/... → mantém
    if (u.pathname.startsWith('/api/')) return input;

    // normaliza balance/history absolutos
    if (u.pathname === '/balance' || u.pathname.startsWith('/balance')) {
      u.pathname = '/balance';
      return u.toString();
    }
    if (u.pathname === '/history' || u.pathname.startsWith('/history')) {
      u.pathname = '/api/v1/pix/list';
      return u.toString();
    }

    // /pix/... → /api/v1/pix/...
    if (u.pathname.startsWith('/pix/')) {
      u.pathname = u.pathname.replace(/^\/pix\//, '/api/v1/pix/');
      return u.toString();
    }

    // caso contrário, deixa como está (evita reescrever coisas que não são PIX)
    return input;
  }

  // Relativa
  const p = input.startsWith('/') ? input : `/${input}`;
  return rewriteRelative(p);
}

// Monkeypatch global de fetch
const _fetch = window.fetch.bind(window);
window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof input === 'string' ? rewrite(input) : rewrite((input as Request).url);
  return _fetch(url, init);
};

import { BASE_API } from './env';

/** Faz GET no backend (tolerante a texto e JSON). */
export async function apiGet(path: string) {
  const url = path.startsWith('http') ? path : `${BASE_API}${path}`;
  const res = await fetch(url);
  return readJson(res);
}

/** Lê um Response como JSON, com tolerância e mensagens úteis. */
export async function readJson(res: Response): Promise<any> {
  if (res.status === 204) return null;

  const ct = res.headers.get('content-type') || '';
  const txt = await res.text();

  if (!res.ok) {
    const snippet = txt == null ? '' : txt.slice(0, 300);
    throw new Error(`${res.status} ${res.statusText} :: ${snippet}`);
  }

  if (ct.includes('application/json')) {
    if (!txt) return null;
    try {
      return JSON.parse(txt);
    } catch (err: any) {
      throw new Error(`JSON parse fail: ${err?.message || err} :: body="${txt.slice(0,200)}"`);
    }
  }

  // Se não for JSON, retorna o texto cru (ou null).
  return txt || null;
}

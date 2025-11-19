import { API_BASE, USER_EMAIL } from "../lib/api";

export interface PixBalancePayload {
  saldo_atual?: number;
  entradas_mes?: number;
  saidas_mes?: number;
}

function buildHeaders(): HeadersInit {
  const headers: Record<string, string> = {};
  if (USER_EMAIL) {
    headers["X-User-Email"] = USER_EMAIL;
  }
  return headers;
}

/**
 * Busca dados agregados do PIX no backend.
 * - Usa GET /api/v1/pix/balance
 * - Envia X-User-Email se estiver definido
 */
export async function fetchPixBalance(): Promise<PixBalancePayload> {
  const url = `${API_BASE}/api/v1/pix/balance`;
  const headers = buildHeaders();

  const r = await fetch(url, { method: "GET", headers });

  if (!r.ok) {
    throw new Error(`pix/balance HTTP ${r.status}`);
  }

  const j = (await r.json()) as PixBalancePayload | null;
  return j ?? {};
}

export async function fetchPix7d(): Promise<any> {
  const r = await fetch("/api/v1/pix/7d");
  if (!r.ok) throw new Error("Erro ao carregar /pix/7d");
  return r.json();
}

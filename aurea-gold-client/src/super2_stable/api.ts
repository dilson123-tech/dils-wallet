import { apiGet, USER_EMAIL } from "../lib/api";
import { getToken } from "../lib/auth";

export interface PixBalancePayload {
  saldo_atual?: number;
  entradas_mes?: number;
  saidas_mes?: number;
}

function buildHeaders(): HeadersInit {
  const headers: Record<string, string> = {};
  if (USER_EMAIL) headers["X-User-Email"] = USER_EMAIL;
  const tok = getToken();
  if (tok) headers["Authorization"] = `Bearer ${tok}`;
  return headers;
}

/**
 * Busca dados agregados do PIX no backend.
 * - Usa GET /api/v1/pix/balance?days=7
 * - Envia X-User-Email se estiver definido
 */
export async function fetchPixBalance(): Promise<PixBalancePayload> {
  // CORE injeta Authorization automaticamente (Bearer)
  // Mantém X-User-Email via buildHeaders()
  return apiGet<PixBalancePayload>("/api/v1/pix/balance?days=7", {
    headers: buildHeaders(),
  });
}

// ======================================================
// AUREA GOLD • LEGACY HTTP WRAPPER
// Mantém apiGet/readJson, mas o GET agora delega pro CORE
// (src/lib/api.ts) para garantir Authorization consistente.
// ======================================================

import { apiGet as coreGet } from "../../lib/api";

/** Faz GET no backend (JSON). Usa CORE com Authorization automático. */
export async function apiGet(path: string) {
  // CORE espera path relativo (ex: /api/v1/...)
  return coreGet<any>(path);
}

/** Lê response como JSON (se possível) ou texto cru. (mantido por compat) */
export async function readJson(res: Response): Promise<any> {
  if (res.status === 204) return null;

  const ct = res.headers.get("content-type") || "";
  const txt = await res.text();

  if (!res.ok) {
    const snippet = txt ? txt.slice(0, 300) : "";
    throw new Error(`${res.status} ${res.statusText} : ${snippet}`);
  }

  if (ct.includes("application/json")) {
    if (!txt) return null;
    try {
      return JSON.parse(txt);
    } catch (err: any) {
      throw new Error(`JSON parse fail: ${err?.message || err} :: body=${txt.slice(0, 200)}`);
    }
  }

  return txt || null;
}

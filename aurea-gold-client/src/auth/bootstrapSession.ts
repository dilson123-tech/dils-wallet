import { getAccessToken, refreshAccessToken } from "./authClient";

// Decisão de sessão na abertura do app. AT ausente/expirado não derruba a
// sessão direto: tenta o refresh existente (single-flight) antes.
//   authenticated → entra no app
//   transient     → refresh recusado só por enquanto (429); tokens mantidos
//   anonymous     → tela de login (doRefresh já limpou em falha definitiva)
export type BootstrapResult = "authenticated" | "transient" | "anonymous";

function parseJwtPayload(token: string): Record<string, any> | null {
  try {
    const base64Url = token.split(".")[1];
    if (!base64Url) return null;

    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

export function isJwtUsable(token: string | null | undefined): boolean {
  if (!token || typeof token !== "string") return false;

  const payload = parseJwtPayload(token);
  if (!payload) return false;
  if (typeof payload.exp !== "number") return true;

  const now = Math.floor(Date.now() / 1000);
  return payload.exp > now + 5;
}

export async function bootstrapSession(): Promise<BootstrapResult> {
  if (isJwtUsable(getAccessToken())) return "authenticated";

  const r = await refreshAccessToken();
  if (r.ok) return "authenticated";
  return r.transient ? "transient" : "anonymous";
}

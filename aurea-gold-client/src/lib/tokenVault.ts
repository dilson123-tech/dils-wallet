/**
 * TokenVault: guarda access_token por origem (host:port) para não misturar
 * localhost:5173 com 192.168.1.20:5173.
 *
 * Chave oficial global (compat): aurea.access_token
 * Chave oficial por origem: aurea.access_token@<origin>
 */
const OFFICIAL = "aurea.access_token";

function originKey(origin?: string) {
  const o =
    origin ||
    (typeof window !== "undefined" ? window.location.origin : "unknown");
  return `${OFFICIAL}@${o}`;
}

export function getAccessToken(): string | null {
  try {
    const ok = localStorage.getItem(originKey());
    if (ok) return ok;
  } catch {}

  // fallback compat (legado)
  try {
    const legacy =
      localStorage.getItem(OFFICIAL) ||
      localStorage.getItem("aurea_access_token") ||
      localStorage.getItem("authToken") ||
      localStorage.getItem("aurea.jwt");
    if (legacy) return legacy;
  } catch {}

  return null;
}

export function saveAccessToken(tok: string) {
  if (!tok || tok === "null" || tok === "undefined") return;
  try {
    localStorage.setItem(originKey(), tok);
  } catch {}

  // opcional: mantém um compat global (mas NÃO depende dele)
  try {
    localStorage.setItem(OFFICIAL, tok);
    localStorage.setItem("aurea_access_token", tok);
    localStorage.setItem("authToken", tok);
    localStorage.setItem("aurea.jwt", tok);
  } catch {}
}

export function clearAccessTokenForThisOrigin() {
  try {
    localStorage.removeItem(originKey());
  } catch {}
}

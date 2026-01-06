/**
 * LAN Auth Bootstrap (DEV)
 * Lê access token via URL hash (#at=TOKEN), salva no localStorage e limpa a URL.
 * - Não roda em produção (só em dev)
 * - Não quebra o app se token estiver ruim
 * - Evita deixar token exposto na barra (limpa hash)
 */

const AT_KEYS = ["aurea.access_token", "aurea_access_token", "aurea.jwt", "authToken"];
const RT_KEYS = ["aurea.refresh_token", "aurea_refresh_token"];

function isDev() {
  try {
    return !!(import.meta as any).env?.DEV;
  } catch {
    return false;
  }
}

function looksLikeJwt(t: string) {
  return typeof t === "string" && t.split(".").length === 3 && t.length > 40;
}

function getHashParam(name: string) {
  const h = (window.location.hash || "").replace(/^#/, "");
  if (!h) return null;
  // suporta "#at=..." e "#/rota?at=..." (se alguém inventar)
  const q = h.includes("?") ? h.split("?").slice(1).join("?") : h;
  const sp = new URLSearchParams(q);
  return sp.get(name);
}

function clearHashSafely() {
  // remove hash sem recarregar (não quebra router)
  try {
    const url = window.location.pathname + window.location.search;
    window.history.replaceState(null, "", url);
  } catch {}
}

export function devLanAuthBootstrap() {
  if (!isDev()) return;

  try {
    const at = getHashParam("at");
    const rt = getHashParam("rt");

    // nada pra fazer
    if (!at && !rt) return;

    // access token é obrigatório pra funcionar
    if (!at || !looksLikeJwt(at)) {
      console.warn("⚠️ LAN bootstrap: token ausente/ inválido. Ignorando.");
      clearHashSafely();
      return;
    }

    for (const k of AT_KEYS) {
      try { localStorage.setItem(k, at); } catch {}
    }

    if (rt && looksLikeJwt(rt)) {
      for (const k of RT_KEYS) {
        try { localStorage.setItem(k, rt); } catch {}
      }
    }

    console.log("✅ LAN bootstrap: token salvo (DEV). Limpando URL…");
    clearHashSafely();

    // força re-render de fetches que dependem do token (sem hard reload)
    // (se você preferir reload total, troque para location.reload())
    try { window.dispatchEvent(new Event("storage")); } catch {}
  } catch (e) {
    console.warn("⚠️ LAN bootstrap falhou sem derrubar o app:", e);
  }
}

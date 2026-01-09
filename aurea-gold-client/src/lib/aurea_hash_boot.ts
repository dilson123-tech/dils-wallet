/**
 * Aurea Gold - Hash Token Boot
 * Objetivo: ler #at=... (link/QR), salvar no localStorage oficial + compat,
 * e limpar o hash (sem reload) pra evitar loop.
 *
 * Suporta:
 * - #at=<JWT>
 * - #at=<JWT>&rt=<token>
 * - #/rota?at=<JWT> (HashRouter)
 */

const OFFICIAL_AT = "aurea.access_token";
const COMPAT_AT_KEYS = ["aurea_access_token", "authToken", "aurea.jwt", "access_token"];

const OFFICIAL_RT = "aurea.refresh_token";
const COMPAT_RT_KEYS = ["aurea_refresh_token", "refreshToken", "aurea.rt", "refresh_token"];

const BOOT_FLAG = "__AUREA_HASH_BOOT_DONE__";

function looksLikeJwt(tok: string) {
  const parts = tok.split(".");
  return parts.length === 3 && tok.length >= 80;
}

function safeSet(key: string, val: string) {
  try { localStorage.setItem(key, val); } catch {}
}

function bootFromHash(): boolean {
  try {
    const w = window as any;
    if (w[BOOT_FLAG]) return false;
    w[BOOT_FLAG] = true;

    const fullHash = window.location.hash || "";
    if (!fullHash) return false;

    const raw = fullHash.startsWith("#") ? fullHash.slice(1) : fullHash;

    // Caso HashRouter: "#/rota?at=..."
    let route = "";
    let qs = raw;

    if (raw.startsWith("/")) {
      const q = raw.indexOf("?");
      if (q === -1) return false; // tem rota mas não tem query no hash
      route = raw.slice(0, q);
      qs = raw.slice(q + 1);
    }

    // Se ainda veio algo com "?" (casos estranhos), pega só o final
    if (qs.includes("?")) qs = qs.split("?").pop() || "";

    const params = new URLSearchParams(qs);

    const at =
      params.get("at") ||
      params.get("access_token") ||
      params.get("token") ||
      "";

    if (!at || !looksLikeJwt(at)) return false;

    // Salva AT no oficial + compat
    safeSet(OFFICIAL_AT, at);
    for (const k of COMPAT_AT_KEYS) safeSet(k, at);

    // Opcional RT
    const rt =
      params.get("rt") ||
      params.get("refresh_token") ||
      "";

    if (rt && rt.length >= 20) {
      safeSet(OFFICIAL_RT, rt);
      for (const k of COMPAT_RT_KEYS) safeSet(k, rt);
    }

    // Limpa só os params sensíveis (mantém rota/outros params se existirem)
    params.delete("at");
    params.delete("access_token");
    params.delete("token");
    params.delete("rt");
    params.delete("refresh_token");

    const base = window.location.pathname + window.location.search;

    if (route) {
      const rest = params.toString();
      const newHash = rest ? `${route}?${rest}` : route;
      window.history.replaceState(null, "", `${base}#${newHash}`);
    } else {
      // Se não tem rota no hash, a gente limpa o hash inteiro (padrão do teu QR)
      window.history.replaceState(null, "", base);
    }

    return true;
  } catch {
    return false;
  }
}

// roda no boot do bundle
bootFromHash();

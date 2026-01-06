// Aurea Gold: interceptor global (401 -> refresh -> retry 1x)
// Instalar cedo no main.tsx (primeiro import)
(() => {
  const W: any = window as any;
  if (W.__AUREA_FETCH_REFRESH__) return;
  W.__AUREA_FETCH_REFRESH__ = "v2";

  const API_BASE: string =
    String(((import.meta as any)?.env?.VITE_API_BASE as string) || "").trim() ||
    "http://127.0.0.1:8000";

  const LOGIN_PATH = "/api/v1/auth/login";
  const REFRESH_PATH = "/api/v1/auth/refresh";
  const LOGIN_URL = `${API_BASE}${LOGIN_PATH}`;
  const REFRESH_URL = `${API_BASE}${REFRESH_PATH}`;

  const AT_KEY = "aurea.access_token";
  const RT_KEY = "aurea.refresh_token";

  // compat (legados)
  const COMPAT_AT_KEYS = ["aurea_access_token", "authToken", "aurea.jwt", "aurea_jwt"];
  const COMPAT_RT_KEYS = ["aurea_refresh_token"];

  function looksLikeJwt(tok: string): boolean {
    const t = String(tok || "").trim();
    if (t.length < 80) return false;
    const parts = t.split(".");
    return parts.length === 3 && !!parts[0] && !!parts[1] && !!parts[2];
  }

  function looksLikeRt(tok: string): boolean {
    const t = String(tok || "").trim();
    return /^[a-f0-9]{64}$/i.test(t);
  }

  function getAccess(): string {
    try {
      const main = String(localStorage.getItem(AT_KEY) || "").trim();
      if (looksLikeJwt(main)) return main;
      for (const k of COMPAT_AT_KEYS) {
        const v = String(localStorage.getItem(k) || "").trim();
        if (looksLikeJwt(v)) return v;
      }
    } catch {}
    return "";
  }

  function getRefresh(): string {
    try {
      const main = String(localStorage.getItem(RT_KEY) || "").trim();
      if (looksLikeRt(main)) return main;
      for (const k of COMPAT_RT_KEYS) {
        const v = String(localStorage.getItem(k) || "").trim();
        if (looksLikeRt(v)) return v;
      }
    } catch {}
    return "";
  }

  function setTokens(at: string, rt?: string) {
    const at2 = String(at || "").trim();
    const rt2 = String(rt || "").trim();

    // nunca gravar lixo
    if (!looksLikeJwt(at2)) return;

    try {
      localStorage.setItem(AT_KEY, at2);
      for (const k of COMPAT_AT_KEYS) localStorage.setItem(k, at2);

      if (rt2 && looksLikeRt(rt2)) {
        localStorage.setItem(RT_KEY, rt2);
        for (const k of COMPAT_RT_KEYS) localStorage.setItem(k, rt2);
      }
    } catch {}
  }

  function clearTokens() {
    try {
      localStorage.removeItem(AT_KEY);
      localStorage.removeItem(RT_KEY);
      for (const k of COMPAT_AT_KEYS) localStorage.removeItem(k);
      for (const k of COMPAT_RT_KEYS) localStorage.removeItem(k);
    } catch {}
  }

  // normaliza compat sem inventar valor novo
  (() => {
    const at = getAccess();
    const rt = getRefresh();
    try {
      if (looksLikeJwt(at)) {
        localStorage.setItem(AT_KEY, at);
        for (const k of COMPAT_AT_KEYS) localStorage.setItem(k, at);
      }
      if (looksLikeRt(rt)) {
        localStorage.setItem(RT_KEY, rt);
        for (const k of COMPAT_RT_KEYS) localStorage.setItem(k, rt);
      }
    } catch {}
  })();

  const origFetch = window.fetch.bind(window);
  let refreshing: Promise<string | null> | null = null;

  async function refreshAccess(): Promise<string | null> {
    const rt = getRefresh();
    if (!rt) return null;

    if (!refreshing) {
      refreshing = (async () => {
        try {
          const r = await origFetch(REFRESH_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: rt }),
          });
          if (!r.ok) return null;

          const j: any = await r.json().catch(() => null);
          const at = String(j?.access_token || "").trim();
          const nrt = String(j?.refresh_token || "").trim();

          if (!looksLikeJwt(at)) return null;
          setTokens(at, nrt || undefined);
          return at;
        } catch {
          return null;
        } finally {
          refreshing = null;
        }
      })();
    }
    return refreshing;
  }

  function isAuthUrl(url: string): boolean {
    return (
      url === LOGIN_URL ||
      url === REFRESH_URL ||
      url.includes(LOGIN_PATH) ||
      url.includes(REFRESH_PATH)
    );
  }

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const req0 = input instanceof Request ? input : new Request(String(input), init);
    const url = req0.url || String(input);

    // não intercepta login/refresh
    const retryable = !isAuthUrl(url) && req0.method !== "OPTIONS";

    // injeta Authorization automaticamente (quando faltar) em calls pro backend
    let req1: Request = req0;
    try {
      const isBackend = url.startsWith(API_BASE);
      const h0 = new Headers(req0.headers);
      const hasAuth = h0.has("Authorization");
      const at = getAccess();

      if (isBackend && !isAuthUrl(url) && !hasAuth && looksLikeJwt(at)) {
        h0.set("Authorization", `Bearer ${at}`);
        req1 = new Request(req0, { headers: h0 });
      }
    } catch {
      req1 = req0;
    }

    // clone ANTES do fetch (pra retry funcionar até com body)
    const retryReq = retryable ? req1.clone() : null;

    const r1 = await origFetch(req1);
    if (r1.status !== 401 || !retryable || !retryReq) return r1;

    const newTok = await refreshAccess();
    if (!newTok) {
      clearTokens();
      return r1;
    }

    const h = new Headers(retryReq.headers);
    h.set("Authorization", `Bearer ${newTok}`);
    h.set("X-Aurea-Retry", "1");
    return origFetch(new Request(retryReq, { headers: h }));
  };
})();

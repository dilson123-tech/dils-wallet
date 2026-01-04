// Aurea Gold: interceptor global (401 -> refresh -> retry 1x)
// Instalar cedo no main.tsx (primeiro import)
(() => {
  const W: any = window as any;
  if (W.__AUREA_FETCH_REFRESH__) return;
  W.__AUREA_FETCH_REFRESH__ = true;

  const API_BASE: string =
    String(((import.meta as any)?.env?.VITE_API_BASE as string) || "").trim() || "http://127.0.0.1:8000";

  const LOGIN_URL = `${API_BASE}/api/v1/auth/login`;
  const REFRESH_URL = `${API_BASE}/api/v1/auth/refresh`;

  const AT_KEY = "aurea.access_token";
  const RT_KEY = "aurea.refresh_token";
  const COMPAT_AT_KEYS = ["aurea_access_token", "authToken", "aurea.jwt"];

  function getRefresh(): string {
    try { return String(localStorage.getItem(RT_KEY) || "").trim(); } catch { return ""; }
  }

  function setTokens(at: string, rt?: string) {
    try {
      localStorage.setItem(AT_KEY, at);
      for (const k of COMPAT_AT_KEYS) localStorage.setItem(k, at);
      if (rt) localStorage.setItem(RT_KEY, rt);
    } catch {}
  }

  function clearTokens() {
    try {
      localStorage.removeItem(AT_KEY);
      localStorage.removeItem(RT_KEY);
      for (const k of COMPAT_AT_KEYS) localStorage.removeItem(k);
    } catch {}
  }

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
          const at = String(j?.access_token || "");
          const nrt = String(j?.refresh_token || "");
          if (at) setTokens(at, nrt || undefined);
          return at || null;
        } catch {
          return null;
        } finally {
          refreshing = null;
        }
      })();
    }
    return refreshing;
  }

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const req = input instanceof Request ? input : new Request(String(input), init);
    const url = req.url || String(input);

    // não intercepta login/refresh
    const retryable = !url.includes(LOGIN_URL) && !url.includes(REFRESH_URL);

    const r1 = await origFetch(req);

    if (r1.status !== 401 || !retryable) return r1;

    // tenta refresh se existir refresh_token (não depende do access_token estar “válido”)
    const newTok = await refreshAccess();
    if (!newTok) {
      clearTokens();
      return r1;
    }

    // retry 1x com token novo
    const req2 = req.clone();
    const h = new Headers(req2.headers);
    h.set("Authorization", `Bearer ${newTok}`);
    return origFetch(new Request(req2, { headers: h }));
  };
})();

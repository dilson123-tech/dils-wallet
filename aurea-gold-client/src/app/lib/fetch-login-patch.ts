// Patch global para garantir login via /api/v1/auth/login
(() => {
  const origFetch = window.fetch.bind(window);

  function isLoginUrl(u: string) {
    try { const url = new URL(u, import.meta.env.VITE_API_BASE); return /\/auth\/login$/.test(url.pathname); }
    catch { return /\/auth\/login$/.test(String(u)); }
  }

  function toJSONBody(body: any) {
    try {
      if (typeof body === "string" && /(?:email|username|password)=/.test(body)) {
        const p = new URLSearchParams(body);
        return JSON.stringify({
          email: p.get("email") ?? p.get("username") ?? "",
          password: p.get("password") ?? "",
        });
      }
      if (body instanceof URLSearchParams) {
        return JSON.stringify({
          email: body.get("email") ?? body.get("username") ?? "",
          password: body.get("password") ?? "",
        });
      }
      if (typeof FormData !== "undefined" && body instanceof FormData) {
        return JSON.stringify({
          email: String(body.get("email") ?? body.get("username") ?? ""),
          password: String(body.get("password") ?? ""),
        });
      }
    } catch {}
    return null;
  }

  async function normalizeLoginResponse(res: Response): Promise<Response> {
    try {
      // clona pra poder ler sem consumir o stream original
      const clone = res.clone();
      const ct = clone.headers.get("content-type") || "";
      if (!res.ok || !/json/i.test(ct)) return res;

      const data = await clone.json().catch(() => ({} as any));
      const token =
        data?.access_token ||
        data?.token ||
        data?.jwt ||
        data?.accessToken ||
        null;

      if (token) {
        try {
          localStorage.setItem("token", String(token));
          // opcional: quem usa “Bearer <token>” vai ler daqui depois
          sessionStorage.setItem("token_type", data?.token_type || "bearer");
        } catch {}

        // Se a app não tratar, garantimos navegação
        try {
          const here = location.pathname;
          if (/^\/$/.test(here)) {
            // home -> manda p/ dashboard
            location.replace("/dashboard");
          } else {
            // senão, só recarrega
            location.reload();
          }
        } catch {}
      }
    } catch {}
    return res;
  }

  window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
    try {
      const url = typeof input === "string" ? input : (input as Request).url ?? String(input);
      const isLogin = isLoginUrl(url);

      if (init && isLogin && String(init.method ?? "GET").toUpperCase() === "POST") {
        const json = toJSONBody(init.body as any);
        if (json) {
          init.body = json;
          const h = new Headers(init.headers as any);
          h.set("Content-Type", "application/json");
          init.headers = h;
          init.credentials = "omit";
        }
      }

      const p = origFetch(input as any, init as any);
      if (isLogin) {
        return p.then(normalizeLoginResponse);
      }
      return p;
    } catch {
      return origFetch(input as any, init as any);
    }
  };
})();

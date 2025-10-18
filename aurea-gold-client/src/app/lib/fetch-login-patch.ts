// Patch global de fetch para /auth/login: garante JSON {email,password}
(() => {
  const origFetch = window.fetch.bind(window);

  function isLoginUrl(u: string) {
    try { const url = new URL(u, window.location.origin); return /\/auth\/login$/.test(url.pathname); }
    catch { return /\/auth\/login$/.test(String(u)); }
  }

  function toJSONBody(body: any) {
    try {
      if (typeof body === "string" && /(?:email|username|password)=/.test(body)) {
        const p = new URLSearchParams(body);
        return JSON.stringify({ email: p.get("email") ?? p.get("username") ?? "", password: p.get("password") ?? "" });
      }
      if (body instanceof URLSearchParams) {
        return JSON.stringify({ email: body.get("email") ?? body.get("username") ?? "", password: body.get("password") ?? "" });
      }
      if (typeof FormData !== "undefined" && body instanceof FormData) {
        return JSON.stringify({ email: String(body.get("email") ?? body.get("username") ?? ""), password: String(body.get("password") ?? "") });
      }
    } catch {}
    return null;
  }

  window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
    try {
      const url = typeof input === "string" ? input : (input as Request).url ?? String(input);
      if (init && isLoginUrl(url) && String(init.method ?? "GET").toUpperCase() === "POST") {
        const json = toJSONBody(init.body as any);
        if (json) {
          init.body = json;
          const h = new Headers(init.headers as any);
          h.set("Content-Type", "application/json");
          init.headers = h;
          init.credentials = "omit";
        }
      }
    } catch {}
    return origFetch(input as any, init as any);
  };
})();

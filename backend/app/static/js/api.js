(function () {
  const { BASE, API_PREFIX } = window.ENV;
  const store = {
    get access() { return localStorage.getItem("access_token") || ""; },
    set access(v) { v ? localStorage.setItem("access_token", v) : localStorage.removeItem("access_token"); }
  };

  async function refreshToken() {
    const rtoken = localStorage.getItem("refresh_token") || "";
    if (!rtoken) throw new Error("Sem refresh_token salvo");
    const url = `${BASE}${API_PREFIX}/auth/refresh`;
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rtoken }),
      credentials: "include"
    });
    if (!r.ok) throw new Error(`Refresh falhou: ${r.status}`);
    const data = await r.json().catch(() => ({}));
    const newAccess = data.access_token || data?.access?.token || "";
    if (!newAccess) throw new Error("Sem access_token no refresh");
    store.access = newAccess;
    return newAccess;
  }

  async function fetchWithAuth(input, init = {}, retry = true) {
    const url = typeof input === "string" ? input : input.url;
    const headers = new Headers(init.headers || {});
    if (store.access) headers.set("Authorization", `Bearer ${store.access}`);

    const resp = await fetch(url, { ...init, headers, credentials: "include" });
    if (resp.status !== 401) return resp;

    if (retry) {
      try {
        await refreshToken();
        const headers2 = new Headers(init.headers || {});
        if (store.access) headers2.set("Authorization", `Bearer ${store.access}`);
        return fetch(url, { ...init, headers: headers2, credentials: "include" });
      } catch (e) {
        store.access = "";
        throw e;
      }
    }
    return resp;
  }

  async function apiGet(path) {
    const u = `${BASE}${API_PREFIX}${path}`;
    const r = await fetchWithAuth(u, { method: "GET" });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  }

  async function apiPost(path, body, contentType = "application/json") {
    const u = `${BASE}${API_PREFIX}${path}`;
    const init = {
      method: "POST",
      headers: { "Content-Type": contentType },
      body: contentType === "application/json" ? JSON.stringify(body) : body
    };
    const r = await fetchWithAuth(u, init);
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  }

  window.API = { apiGet, apiPost, store };
})();

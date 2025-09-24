(function(){
  const { BASE, API_PREFIX } = window.ENV;

  async function login(email, password) {
    const url = `${BASE}${API_PREFIX}/auth/login`;
    const body = new URLSearchParams({ username: email, password });

    let resp, raw;
    try {
      resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
        credentials: "include"
      });
      raw = await resp.text();
    } catch (e) {
      throw new Error("Falha de rede (verifique internet/CORS).");
    }

    let data;
    try { data = raw ? JSON.parse(raw) : {}; } catch { data = {}; }

    if (!resp.ok) {
      const msg = data.detail || data.message || `${resp.status} ${resp.statusText}`;
      throw new Error(msg);
    }

    const access = data.access_token || "";
    if (!access) throw new Error("Sem access_token no login");
    API.store.access = access;

    const rtoken = data.refresh_token || "";
    if (rtoken) localStorage.setItem("refresh_token", rtoken);

    return data;
  }

  window.AUTH = { login };
})();

(() => {
  const API_BASE = localStorage.getItem("API_BASE") || "http://127.0.0.1:8787";
  const origFetch = window.fetch.bind(window);

  function rewrite(u) {
    if (typeof u !== "string") return u;
    if (u.startsWith("/api/")) return API_BASE + u;
    if (u.startsWith("api/"))  return API_BASE + "/" + u;
    return u;
  }

  window.fetch = (input, init = {}) => {
    const url = (typeof input === "string") ? input : input.url;
    const newUrl = rewrite(url);
    if (url !== newUrl) console.debug("[UI] boot_api_base:", url, "→", newUrl);
    return origFetch(newUrl, init);
  };

  window.authHdr = () => {
    const t = localStorage.getItem("access_token");
    return t ? { Authorization: "Bearer " + t } : {};
  };

  console.log("[UI] boot_api_base ativo. API_BASE =", API_BASE);
})();

/**
 * Dev-only: redireciona TODAS as chamadas para o backend local.
 * - Troca domínios de prod por VITE_API_BASE
 * - Prefixa URLs relativas que começam com /api/
 * - Injeta X-User-Email se não vier
 */
(function () {
  var env = (import.meta && import.meta.env) ? import.meta.env : {};
  var API_BASE = env.VITE_API_BASE || "http://127.0.0.1:8000";
  var USER_EMAIL = env.VITE_USER_EMAIL;

  var PROD_BASES = [
    "https://dils-wallet-production.up.railway.app",
    "http://dils-wallet-production.up.railway.app"
  ];

  function absolutize(url) {
    try { new URL(url); return url; }
    catch (e) {
      var base = API_BASE.replace(/\/+$/,"");
      var path = String(url).replace(/^\/+/,"");
      return base + "/" + path;
    }
  }

  var nativeFetch = window.fetch.bind(window);

  window.fetch = function(input, init) {
  if (!env || !env.DEV) { return nativeFetch(input, init); }
    try {
      var urlStr;
      if (typeof input === "string") urlStr = input;
      else if (input instanceof URL) urlStr = input.toString();
      else urlStr = (input && input.url) ? input.url : String(input);

      // troca base de produção por local
      for (var i=0;i<PROD_BASES.length;i++) {
        var base = PROD_BASES[i];
        if (urlStr.indexOf(base) === 0) {
          urlStr = API_BASE + urlStr.slice(base.length);
          break;
        }
      }

      // prefixa /api/ relativo
      if (/^\/api\//.test(urlStr)) urlStr = absolutize(urlStr);

      // headers preservados + X-User-Email
      var headers = new Headers(
        (init && init.headers) ||
        (typeof input !== "string" && input && input.headers) ||
        undefined
      );
      var hasAuth = headers.has("Authorization") || headers.has("authorization");
      if (!hasAuth && !headers.has("X-User-Email") && USER_EMAIL) {
        headers.set("X-User-Email", USER_EMAIL);
      }

      var nextInit = Object.assign({}, (init || {}), { headers });
      return nativeFetch(urlStr, nextInit);
    } catch (e) {
      return nativeFetch(input, init);
    }
  };

  if (env && env.DEV) {
    console.log("[AureaClient DEV] Forçando API para", API_BASE);
  }
})();
export {};

/* DEV ONLY: bootstrap de auth para abrir o painel via LAN/telefone.
   Uso:
   - http://IP:5174/#at=<JWT>      -> salva token e recarrega (hash é client-side)
   - http://IP:5174/#cleartokens   -> limpa tokens e recarrega
*/
export function devLanAuthBootstrap() {
  try {
    const env: any = (import.meta as any).env || {};
    if (!env.DEV) return;

    const hash = (location.hash || "").replace(/^#/, "");
    if (!hash) return;

    const ALL_KEYS = [
      "aurea.access_token",
      "aurea_access_token",
      "aurea.jwt",
      "aurea_jwt",
      "authToken",
      "aurea.refresh_token",
      "aurea_refresh_token",
    ];

    const clearTokens = () => {
      for (const k of ALL_KEYS) {
        try { localStorage.removeItem(k); } catch {}
      }
      console.log("🧹 [DEV AUTH] tokens limpos neste origin:", location.origin);
    };

    const sanitizeJwt = (raw: string) => {
      let s = (raw || "").trim();

      // se colaram JSON inteiro, tenta extrair
      if (s.startsWith("{")) {
        try {
          const j = JSON.parse(s);
          if (typeof j?.access_token === "string") s = j.access_token;
        } catch {}
      }

      // remove Bearer, aspas, espaços, chars invisíveis e qualquer coisa fora do base64url
      s = s.replace(/^Bearer\s+/i, "");
      s = s.replace(/^"+|"+$/g, "");
      s = s.replace(/\s+/g, "");
      s = s.replace(/[^A-Za-z0-9._-]/g, ""); // mata NBSP/zero-width/etc

      // tenta achar um JWT “eyJ...x.y.z” dentro do que sobrou
      const m = s.match(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/);
      return (m?.[0] || "");
    };

    // modo limpar
    if (hash === "cleartokens" || hash.includes("cleartokens")) {
      clearTokens();
      location.hash = "";
      location.reload();
      return;
    }

    // pega token do hash no formato #at=<jwt>
    let at = "";
    try {
      const params = new URLSearchParams(hash);
      at = params.get("at") || params.get("token") || "";
    } catch {
      // fallback: se alguém colar “at=...”
      const m = hash.match(/(?:^|&)at=([^&]+)/);
      at = m ? m[1] : "";
    }

    const jwt = sanitizeJwt(at);
    if (!jwt || jwt.split(".").length !== 3 || jwt.length < 80) {
      console.warn("⚠️ [DEV AUTH] hash não tem JWT válido. Use #at=<JWT>.");
      return;
    }

    // salva em TODAS as chaves que o front pode ler
    try {
      localStorage.setItem("aurea.access_token", jwt);
      localStorage.setItem("aurea_access_token", jwt);
      localStorage.setItem("aurea.jwt", jwt);
      localStorage.setItem("aurea_jwt", jwt);
      localStorage.setItem("authToken", jwt);
    } catch {}

    console.log("✅ [DEV AUTH] token salvo neste origin:", location.origin, "len=", jwt.length);

    // limpa hash e recarrega
    location.hash = "";
    location.reload();
  } catch (e) {
    console.warn("⚠️ [DEV AUTH] falhou:", e);
  }
}

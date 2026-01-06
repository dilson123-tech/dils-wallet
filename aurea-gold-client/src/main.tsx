import "./lib/fetch-refresh";
import "./styles/aurea-mobile.css";
import "./app/customer/components/QuickPixMount";
import "./styles/aurea.css";
import "./index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ErrorBoundary from "./shared/ErrorBoundary";

// AUREA_RESET_HARD: limpa cache/service worker/storage quando abrir com ?reset=1


(async () => {
  try {
    if (typeof window === "undefined") return;
    const sp = new URLSearchParams(window.location.search);
    if (sp.get("reset") !== "1") return;

    // mata service workers
    if ("serviceWorker" in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map(r => r.unregister()));
    }

    // limpa caches
    if ("caches" in window) {
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
    }

    try { localStorage.clear(); } catch {}
    try { sessionStorage.clear(); } catch {}

    // tenta limpar indexedDB
    try {
      const anyIDB = indexedDB;
      const dbs = (anyIDB as any).databases ? await (anyIDB as any).databases() : [];
      if (Array.isArray(dbs)) {
        await Promise.all(dbs.map((d: any) => d?.name
          ? new Promise(res => {
              const req = indexedDB.deleteDatabase(d.name);
              req.onsuccess = req.onerror = req.onblocked = () => res(null);
            })
          : null
        ));
      }
    } catch {}

    sp.delete("reset");
    sp.set("v", String(Date.now())); // cache-bust
    const clean = window.location.pathname + "?" + sp.toString() + window.location.hash;
    window.location.replace(clean);
  } catch {}
})();


// ⚠️ Desativado para evitar crash durante o debug
// import "@/dev/force-local-api";

// Nas rotas /super e /super2 usamos a entrada especial do painel SUPER,
// sem montar o app React legado.

// --- Entrada especial do laboratório SUPER2 ---

// 🔥 Entradas especiais: SUPER2-LAB e SUPER2 normal
const path = location.pathname;

// LAB primeiro (senão /super2-lab cai no /super2)
if (path.startsWith("/pagamentos-lab")) {
  import("./pagamentos/PanelPagamentos").then(({ default: PanelPagamentos }) => {

// AUREA_BOOTSTRAP_TOKENS: garante tokens DEV no localStorage (LAN) sem depender de login
try {
  const dt = String(import.meta.env.VITE_DEV_TOKEN || "").trim();
  const drt = String((import.meta.env as any).VITE_DEV_REFRESH_TOKEN || "").trim();

  // logs só de tamanho (segurança)
  if (dt || drt) console.log("[AUREA] DEV token len=", dt.length, "DEV refresh len=", drt.length);

  if (dt) {
    const keys = ["aurea.access_token", "aurea_access_token", "aurea.jwt", "aurea_jwt"];
    for (const k of keys) if (!localStorage.getItem(k)) localStorage.setItem(k, dt);
  }
  if (drt) {
    const rkeys = ["aurea.refresh_token", "aurea_refresh_token"];
    for (const k of rkeys) if (!localStorage.getItem(k)) localStorage.setItem(k, drt);
  }
} catch {}

    ReactDOM.createRoot(document.getElementById("root")!).render(
      <React.StrictMode>
        <ErrorBoundary>
          <PanelPagamentos />
        </ErrorBoundary>
      </React.StrictMode>
    );
  });
} else if (path === "/super2lab") {
  import("./super2-lab/Super2Lab").then(({ default: Super2Lab }) => {
    ReactDOM.createRoot(document.getElementById("root")!).render(
      <React.StrictMode>
        <ErrorBoundary>
          <Super2Lab />
        </ErrorBoundary>
      </React.StrictMode>
    );
  });
} else if (path.startsWith("/super2") || path.startsWith("/super")) {
  import("./super2/mainSuper2").then(({ default: MainSuper2 }) => {
    ReactDOM.createRoot(document.getElementById("root")!).render(
      <React.StrictMode>
        <ErrorBoundary>
          <MainSuper2 />
        </ErrorBoundary>
      </React.StrictMode>
    );
  });
} else {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>
  );
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.error('[Aurea PWA] Falha ao registrar service worker:', err);
    });
  });
}


// AUREA_FETCH_REFRESH_INTERCEPTOR
(() => {
  if (typeof window === "undefined" || typeof fetch === "undefined") return;

  const ACCESS_KEY = "aurea.access_token";
  const REFRESH_KEY = "aurea.refresh_token";

  const API_BASE = String((import.meta as any).env?.VITE_API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");
  const REFRESH_URL = `${API_BASE}/api/v1/auth/refresh`;
  const LOGIN_URL = `${API_BASE}/api/v1/auth/login`;

  const origFetch = window.fetch.bind(window);

  const getAccess = () => localStorage.getItem(ACCESS_KEY) || localStorage.getItem("aurea.jwt") || "";
  const getRefresh = () => localStorage.getItem(REFRESH_KEY) || "";

  const setTokens = (access: string, refresh?: string) => {
    try { if (access) { localStorage.setItem(ACCESS_KEY, access); localStorage.setItem("aurea.jwt", access); } } catch {}
    try { if (refresh) localStorage.setItem(REFRESH_KEY, refresh); } catch {}
  };

  const clearTokens = () => {
    try { localStorage.removeItem(ACCESS_KEY); } catch {}
    try { localStorage.removeItem("aurea.jwt"); } catch {}
    try { localStorage.removeItem(REFRESH_KEY); } catch {}
  };

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
          const j = await r.json().catch(() => null);
          const at = j?.access_token || "";
          const nrt = j?.refresh_token || "";
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

    const retryable = !url.includes(LOGIN_URL) && !url.includes(REFRESH_URL);

    const r1 = await origFetch(req);

    if (r1.status !== 401 || !retryable) return r1;
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


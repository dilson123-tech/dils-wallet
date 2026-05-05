import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/aurea.css";
import "./index.css";
import { devLanAuthBootstrap } from "./dev/devLanAuthBootstrap";
import "./lib/aurea_hash_boot";

console.log("[main] start", location.href);

function stripLegacyAureaMobile() {
  try {
    document.body?.classList.remove("aurea-mobile");
    document.documentElement?.classList.remove("aurea-mobile");
  } catch {}
}

stripLegacyAureaMobile();

try {
  const observerConfig: MutationObserverInit = { attributes: true, attributeFilter: ["class"] };

  if (document.body) {
    new MutationObserver(() => stripLegacyAureaMobile()).observe(document.body, observerConfig);
  }

  if (document.documentElement) {
    new MutationObserver(() => stripLegacyAureaMobile()).observe(document.documentElement, observerConfig);
  }
} catch (e) {
  console.warn("[main] legacy mobile observer failed", e);
}

const el = document.getElementById("root");
if (!el) {
  document.body.innerHTML = "<div style=\"color:#f00;padding:16px;font:14px monospace\">❌ #root não encontrado</div>";
} else {
  ReactDOM.createRoot(el).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

// lan boot (não bloqueia o render)
if (typeof devLanAuthBootstrap === "function") {
  setTimeout(() => {
    try {
      Promise.resolve(devLanAuthBootstrap()).catch((e: any) => console.warn("[lanboot] failed", e));
    } catch (e) {
      console.warn("[lanboot] crash", e);
    }
  }, 0);
}


import "./styles/aurea-mobile.css";
import "./app/customer/components/QuickPixMount";
import "./styles/aurea.css";
import "./index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ErrorBoundary from "./shared/ErrorBoundary";

// ⚠️ Desativado para evitar crash durante o debug
// import "@/dev/force-local-api";

// Nas rotas /super e /super2 usamos a entrada especial do painel SUPER,
// sem montar o app React legado.
if (location.pathname.startsWith("/super") || location.pathname.startsWith("/super2")) {
  import("./super2/mainSuper2");
} else {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>
  );
}

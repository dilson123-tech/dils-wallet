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

// --- Entrada especial do laboratório SUPER2 ---

// 🔥 Entradas especiais: SUPER2-LAB e SUPER2 normal
const path = location.pathname;

// LAB primeiro (senão /super2-lab cai no /super2)
if (path.startsWith("/super2-lab") || path.startsWith("/super2lab")) {
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

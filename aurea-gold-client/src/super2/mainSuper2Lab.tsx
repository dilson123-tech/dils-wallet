import React from "react";
import ReactDOM from "react-dom/client";
import PanelSuper2 from "./PanelSuper2";
import "../styles/aurea-super.css";

/**
 * Entrada exclusiva do SUPER2 LAB.
 * O HTML super2-lab.html importa este módulo e aqui já montamos o painel.
 */
const rootEl = document.getElementById("root");

if (rootEl) {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <PanelSuper2 />
    </React.StrictMode>
  );
} else {
  console.error("SUPER2 LAB: elemento #root não encontrado");
}

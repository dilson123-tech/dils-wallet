import React from "react";
import ReactDOM from "react-dom/client";
import SuperHistoryLab from "./SuperHistoryLab";
import "../styles/aurea-super.css";

const root = document.getElementById("root");

if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <SuperHistoryLab />
    </React.StrictMode>
  );
}

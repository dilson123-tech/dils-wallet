import "./fixTopTabs";
import "./nukeTopDupActions";
import "./stripTopDupActions";
import "./ensureMobileClass";
import "./removeTopDupActions";
import "./ensureTopToolbar";
if (!document.body.classList.contains("aurea-mobile")) { document.body.classList.add("aurea-mobile"); }
import React from "react";
import ReactDOM from "react-dom/client";
import SuperApp from "./SuperApp";

const el = document.getElementById("root")!;
ReactDOM.createRoot(el).render(
  <React.StrictMode>
    <SuperApp />
  </React.StrictMode>
);

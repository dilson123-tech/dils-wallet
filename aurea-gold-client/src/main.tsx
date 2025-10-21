import "./lib/fetch-shim";
import "@/shims/global-readjson";
import "./app/lib/env";
import "./app/lib/bootstrap-base";
import "@/app/lib/fetch-login-patch";
import React from "react";
import ReactDOM from "react-dom/client";
import { SessionProvider } from "./app/context/SessionContext";
import Home from "./app/routes/Home";
import "./styles/aurea-gold.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <SessionProvider>
      <Home />
    </SessionProvider>
  </React.StrictMode>
);

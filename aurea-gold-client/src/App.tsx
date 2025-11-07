import "./styles/aurea.css";
import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

import AureaTopbar from "@/app/customer/components/AureaTopbar";
import Dashboard from "./app/customer/pages/Dashboard";
import Pix from "./app/customer/pages/Pix";

export default function App() {
  return (
    <BrowserRouter>
      <AureaTopbar />
      {/* espaçamento para não sobrepor o conteúdo */}
      <div style={{ paddingTop: 72 }} />

      <main className="aurea-main" style={{ padding: 12 }}>
        <nav style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <Link to="/">Home</Link>
          <Link to="/pix">PIX</Link>
        </nav>

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/pix" element={<Pix />} />
        </Routes>
      </main>

      <footer className="aurea-footer" style={{ opacity: 0.7, padding: "6px 12px" }}>
        v1.0 beta
      </footer>
    </BrowserRouter>
  );
}

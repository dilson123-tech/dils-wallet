import "./styles/aurea.css";
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Shell from "@/app/layout/Shell";
import Home from "./app/customer/pages/Dashboard"; // painel principal
import Pix from "./app/customer/pages/Pix";

export default function App() {
  return (
    <BrowserRouter>
      <Shell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/pix" element={<Pix />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  );
}

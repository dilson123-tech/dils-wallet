import React from "react";
import { Link } from "react-router-dom";
export default function Home() {
  return (
    <div>
      <h1>Dashboard Aurea Gold</h1>
      <p><Link to="/pix">Ir para PIX</Link></p>
    </div>
  );
}

import React, { useState } from "react";
import "../../../styles/aurea.css";
import AIChatModal from "../components/AIChatModal";

export default function Dashboard() {
  const [openAI, setOpenAI] = useState(false);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="gold-title">Aurea Gold Premium</h1>
        <span className="user-welcome">Bem-vindo(a), Cliente!</span>
      </header>

      <section className="dashboard-balance">
        <h2>Saldo Atual</h2>
        <div className="balance-card">R$ 10.432,00</div>
      </section>

      <section className="dashboard-actions">
        <button className="gold-btn">Enviar PIX</button>
        <button className="gold-btn">Extrato</button>
        <button className="gold-btn" onClick={() => setOpenAI(true)}>IA Financeira</button>
      </section>

      <footer className="dashboard-footer">
        <small>© 2025 Aurea Gold Bank • IA 3.0</small>
      </footer>

      {/* Botão flutuante IA */}
      <button className="ia-float" onClick={() => setOpenAI(true)} aria-label="Abrir IA">🤖</button>

      {/* Modal IA */}
      <AIChatModal open={openAI} onClose={() => setOpenAI(false)} />
    </div>
  );
}

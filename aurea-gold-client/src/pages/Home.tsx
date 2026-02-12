import React from "react";
import { Link } from "react-router-dom";

const Home: React.FC = () => {
  return (
    <div className="home">
      <header className="home__header">
        <h1>Dashboard Aurea Gold</h1>
        <nav className="home__nav">
          <Link to="/pix">Ir para PIX</Link>
          {/* futuros atalhos: /pagamentos, /credito, /ia, etc */}
        </nav>
      </header>

      <main className="home__main">
        <section className="home__section">
        </section>
      </main>
    </div>
  );
};

export default Home;

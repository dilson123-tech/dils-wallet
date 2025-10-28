    {movimentacoes.map((nov, i) => (
      <div key={i} className="mb-3 border-b border-zinc-700 pb-2">
        <div
          style={{
            fontSize: "1rem",
            fontWeight: 700,
            lineHeight: 1.2,
            color: isEntrada(nov.tipo) ? "#4ade80" : "#f87171",
            textShadow: isEntrada(nov.tipo)
              ? "0 0 6px rgba(16,185,129,0.6)"
              : "0 0 6px rgba(248,113,113,0.6)",
            whiteSpace: "nowrap",
          }}
        >
          {isEntrada(nov.tipo) ? "+" : "-"} {formatValor(nov.valor)}
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "0.75rem",
            lineHeight: 1.2,
            color: "#a1a1aa",
            gap: "0.5rem",
            marginTop: "0.5rem",
            fontFamily: "monospace",
          }}
        >
          <span
            style={{
              color: isEntrada(nov.tipo) ? "#4ade80" : "#f87171",
            }}
          >
            {isEntrada(nov.tipo) ? "✓ crédito" : "↘ débito"}
          </span>
          <span>{isEntrada(nov.tipo) ? "crédito" : "débito"}</span>
        </div>
      </div>
    ))}

    {/* rodapé do painel PIX */}
    <footer className="text-xs text-zinc-500 text-center mt-6 opacity-70">
      <div>Aurea Gold • PIX interno de teste</div>
      <div>Ambiente simulado — não é banco comercial</div>
    </footer>
  </main>
);
}

export default PixPanel;

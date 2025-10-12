import React from "react";

type Props = {
  items?: any[];
  title?: string;
};

export default function Transactions({ items = [], title = "Transações" }: Props) {
  return (
    <div style={{ padding: 16, background: "#0e0e0e", borderRadius: 12, border: "1px solid #333", color: "#ddd" }}>
      <h2 style={{ marginTop: 0, color: "#ffd700" }}>{title}</h2>
      {items.length === 0 ? (
        <p style={{ opacity: 0.8 }}>Sem transações para exibir.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {items.map((it, idx) => (
            <li key={idx} style={{ padding: "8px 0", borderBottom: "1px solid #222" }}>
              <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: 12 }}>{JSON.stringify(it, null, 2)}</pre>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

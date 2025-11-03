import React from "react";

function toggleAssistant() {
  try {
    window.dispatchEvent(new CustomEvent("aurea-assistant:toggle"));
  } catch {}
}

export default function AureaFAB() {
  return (
    <button
      className="aurea-fab"
      aria-label="Abrir Aurea IA 3.0"
      onClick={toggleAssistant}
      title="Aurea IA 3.0"
    >
      <span className="aurea-fab-glow" />
      IA
    </button>
  );
}

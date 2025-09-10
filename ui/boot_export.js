// boot_export.js — handler isolado do botão "Exportar CSV"
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-export");
  if (!btn) return;

  // BASE da API (porta 8787)
  const BASE = (typeof window.BASE === "string" && window.BASE) || `${location.protocol}//${location.hostname}:8787`;
  console.log("[UI] boot_export pronto", { BASE });

  btn.addEventListener("click", async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        alert("Faça login primeiro para exportar o CSV.");
        return;
      }
      const resp = await fetch(`${BASE}/api/v1/transactions/export.csv`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "transactions_export.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      console.log("[UI] export OK");
    } catch (err) {
      console.error("[UI] export erro", err);
      alert("Falha ao exportar CSV. Veja o console para detalhes.");
    }
  });
});

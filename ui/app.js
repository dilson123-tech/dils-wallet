(() => {
  const $ = (s) => document.querySelector(s);
  const elAuth  = $("#authState");
  const elSaldo = $("#saldo");

  function setAuth() {
    const t = localStorage.getItem("access_token");
    elAuth.textContent = t ? "Autenticado" : "Não autenticado";
    elAuth.className   = t ? "ok" : "muted";
  }

  setAuth();
  // próximas partes virão aqui

  async function updateBalance() {
    try {
      const r = await fetch("/api/v1/transactions/balance", { headers: { ...authHdr() }});
      if (!r.ok) throw new Error("HTTP " + r.status);
      const j = await r.json();
      elSaldo.textContent = (j?.saldo ?? j?.balance ?? "--");
    } catch (e) { console.warn("[UI] updateBalance:", e); }
  }

  document.querySelector("#btn-balance")?.addEventListener("click", updateBalance);

  async function loadHistorico() {
    try {
      const r = await fetch("/api/v1/transactions", { headers: { ...authHdr() }});
      if (!r.ok) throw new Error("HTTP " + r.status);
      const arr = await r.json();
      const tbody = document.querySelector("#tx-body"); if (!tbody) return;
      tbody.innerHTML = "";
      arr.forEach(tx => {
        const tr = document.createElement("tr");
        const fmtDate = (s) => (s ? s.toString().replace("T"," ").slice(0,16) : "");
        const badge = (tipo) =>
          tipo === "deposito" ? '<span class="badge in">Depósito ✅</span>' :
          tipo === "saque" ? '<span class="badge out">Saque ❌</span>' :
          '<span class="badge out">Transferência ❌</span>';
        tr.innerHTML = `
          <td>${tx.id}</td>
          <td>${badge(tx.tipo)}</td>
          <td>${Number(tx.valor).toFixed(2)}</td>
          <td>${tx.descricao || ""}</td>
          <td>${fmtDate(tx.criado_em || tx.created_at)}</td>`;
        tbody.appendChild(tr);
      });
    } catch (e) { console.error("[UI] loadHistorico:", e); }
  }

  // LOGIN
  document.querySelector("#btn-login")?.addEventListener("click", async () => {
    try {
      const email = document.querySelector("#email").value.trim();
      const pass  = document.querySelector("#pass").value;
      const body  = new URLSearchParams({ username: email, password: pass });

      const r = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });

      const txt = await r.text();
      if (!r.ok) { console.error("[UI] login", r.status, txt); alert("Falha no login: "+r.status); return; }

      let j={}; try { j = JSON.parse(txt); } catch {}
      const token = j.access_token || j.token || j.accessToken;
      if (!token) { alert("Login OK, mas sem token."); return; }

      localStorage.setItem("access_token", token);
      setAuth(); await updateBalance(); await loadHistorico();
      alert("Login OK ✅");
    } catch (e) { console.error("[UI] login erro:", e); alert("Erro no login."); }
  });

  // LOGOUT
  document.querySelector("#btn-logout")?.addEventListener("click", () => {
    localStorage.removeItem("access_token");
    setAuth();
    const tb = document.querySelector("#tx-body"); if (tb) tb.innerHTML = "";
    elSaldo.textContent = "--";
    alert("Sessão encerrada.");
  });

  // EXPORT CSV
  document.querySelector("#btn-export")?.addEventListener("click", async () => {
    try {
      const r = await fetch("/api/v1/transactions/export", { headers: { ...authHdr() }});
      if (!r.ok) throw new Error("HTTP " + r.status);
      const blob = await r.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href = url; a.download = "transacoes.csv";
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
      alert("CSV exportado ✅");
    } catch (e) { console.error("[UI] export erro", e); alert("Erro ao exportar CSV."); }
  });

  // SALVAR transação
  document.querySelector("#btn-save")?.addEventListener("click", async () => {
    const tipo = document.querySelector("#tipo").value;
    const valor = parseFloat(document.querySelector("#valor").value);
    const descricao = document.querySelector("#descricao").value.trim();
    if (!valor || valor <= 0) { alert("Informe um valor válido."); return; }

    try {
      const r = await fetch("/api/v1/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHdr() },
        body: JSON.stringify({ tipo, valor, descricao }),
      });
      if (!r.ok) { const t = await r.text(); console.error("[UI] salvar", r.status, t); alert("Falha ao salvar: "+r.status); return; }
      alert("Transação salva ✅");
      await updateBalance(); setTimeout(loadHistorico, 300);
    } catch (e) { console.error("[UI] salvar erro:", e); alert("Erro ao salvar transação."); }
  });

  // TRANSFERÊNCIA
  document.querySelector("#btn-transferir")?.addEventListener("click", async () => {
    const destinatario = document.querySelector("#destinatario").value.trim();
    const valor = parseFloat(document.querySelector("#valor_transfer").value);
    const descricao = document.querySelector("#descricao_transfer").value.trim();
    if (!destinatario || !valor || valor <= 0) { alert("Informe destinatário e valor válido."); return; }

    try {
      const r = await fetch("/api/v1/transactions/transfer", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHdr() },
        body: JSON.stringify({ destino_email: destinatario, valor, descricao }),
      });
      if (!r.ok) { const t = await r.text(); console.error("[UI] transfer", r.status, t); alert("Falha na transferência: "+r.status); return; }
      alert("Transferência realizada ✅");
      await updateBalance(); setTimeout(loadHistorico, 500);
    } catch (e) { console.error("[UI] transfer erro:", e); alert("Erro na transferência."); }
  });

})(); // fim IIFE

  // Boot: ao abrir a página, se já tiver token, carrega tudo
  if (localStorage.getItem("access_token")) {
    updateBalance();
    loadHistorico();
  }

// === paginação simples ===
let txPage = 1, txPageSize = 10, txData = [];

async function loadHistorico() {
  try {
    const r = await fetch("/api/v1/transactions", { headers: { ...authHdr() }});
    if (!r.ok) throw new Error("HTTP " + r.status);
    txData = await r.json();
    renderPage();
  } catch (e) { console.error("[UI] loadHistorico:", e); }
}

function renderPage() {
  const tbody = document.querySelector("#tx-body"); if (!tbody) return;
  tbody.innerHTML = "";
  const start = (txPage-1)*txPageSize;
  const slice = txData.slice(start, start+txPageSize);
  slice.forEach(tx => {
    const tr = document.createElement("tr");
    const fmtDate = (s) => (s ? s.toString().replace("T"," ").slice(0,16) : "");
    const badge = (tipo) =>
      tipo === "deposito" ? '<span class="badge in">Depósito ✅</span>' :
      tipo === "saque" ? '<span class="badge out">Saque ❌</span>' :
      '<span class="badge out">Transferência ❌</span>';
    tr.innerHTML = `
      <td>${tx.id}</td>
      <td>${badge(tx.tipo)}</td>
      <td>${Number(tx.valor).toFixed(2)}</td>
      <td>${tx.descricao || ""}</td>
      <td>${fmtDate(tx.criado_em || tx.created_at)}</td>`;
    tbody.appendChild(tr);
  });
  document.querySelector("#tx-info").textContent =
    `Página ${txPage} de ${Math.max(1, Math.ceil(txData.length/txPageSize))}`;
}

document.querySelector("#tx-prev")?.addEventListener("click", () => {
  if (txPage > 1) { txPage--; renderPage(); }
});
document.querySelector("#tx-next")?.addEventListener("click", () => {
  if (txPage*txPageSize < txData.length) { txPage++; renderPage(); }
});

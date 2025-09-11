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
      const r = await api("/api/v1/transactions/balance", { headers: { ...authHdr() }});
      if (!r.ok) throw new Error("HTTP " + r.status);
      const j = await r.json();
      elSaldo.textContent = (j?.saldo ?? j?.balance ?? "--");
    } catch (e) { console.warn("[UI] updateBalance:", e); }
  }

  document.querySelector("#btn-balance")?.addEventListener("click", updateBalance);

  async function loadHistorico() {
    try {
      const r = await api("/api/v1/transactions", { headers: { ...authHdr() }});
      if (!r.ok) throw new Error("HTTP " + r.status);
      const arr = await r.json();
      const tbody = document.querySelector("#tx-body"); if (!tbody) return;
      tbody.innerHTML = "";
      arr.forEach(tx => {
        const tr = document.createElement("tr");
        const fmtDate = (s) => (s ? s.toString().replace("T"," ").slice(0,16) : "");
        const badge = (tipo) =>
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

      const r = await api("/api/v1/auth/login", {
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
      const r = await api("/api/v1/transactions/export", { headers: { ...authHdr() }});
      if (!r.ok) throw new Error("HTTP " + r.status);
      const blob = await r.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href = url; a.download = "transacoes.csv";
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    } catch (e) { console.error("[UI] export erro", e); alert("Erro ao exportar CSV."); }
  });

  // SALVAR transação
  document.querySelector("#btn-save")?.addEventListener("click", async () => {
    const tipo = document.querySelector("#tipo").value;
    const valor = parseFloat(document.querySelector("#valor").value);
    const descricao = document.querySelector("#descricao").value.trim();
    if (!valor || valor <= 0) { alert("Informe um valor válido."); return; }

    try {
      const r = await api("/api/v1/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHdr() },
        body: JSON.stringify({ tipo, valor, descricao }),
      });
      if (!r.ok) { const t = await r.text(); console.error("[UI] salvar", r.status, t); alert("Falha ao salvar: "+r.status); return; }
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
      const r = await api("/api/v1/transactions/transfer", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHdr() },
        body: JSON.stringify({ destino_email: destinatario, valor, descricao }),
      });
      if (!r.ok) { const t = await r.text(); console.error("[UI] transfer", r.status, t); alert("Falha na transferência: "+r.status); return; }
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
    const r = await api("/api/v1/transactions", { headers: { ...authHdr() }});
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
// --- safe 401 auto-register wrapper (appended) ---
(function(){
  const API = (window.API_BASE || "");
  const _fetch = window.fetch;

  async function tryLoginThenRegister(url, opts){
    // Only handle the login route
    if (!/\/api\/v1\/auth\/login\b/.test(url)) return _fetch(url, opts);

    // 1st try: normal login
    let r = await _fetch(API + "/api/v1/auth/login", opts);
    if (r.status !== 401) return r;

    // If 401, try to read credentials from body and register
    try {
      const body = opts && opts.body ? String(opts.body) : "";
      const mUser = body.match(/username=([^&]+)/);
      const mPass = body.match(/password=([^&]+)/);
      const email = mUser ? decodeURIComponent(mUser[1]) : null;
      const pass  = mPass ? decodeURIComponent(mPass[1]) : null;

      if (!email || !pass) return r; // no creds to register

      await _fetch(API + "/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: pass })
      });

      // retry login
      const r2 = await _fetch(API + "/api/v1/auth/login", opts);
      if (r2.ok) {
        // best-effort: update badge if your page has it
        const s = document.querySelector('#authState');
        if (s) s.textContent = "Autenticado (novo)";
      }
      return r2;
    } catch (e) {
      console.warn("[UI] auto-register wrapper falhou:", e);
      return r; // fall back to original 401
    }
  }

  window.fetch = function(url, opts){
    try { return tryLoginThenRegister(url, opts); }
    catch { return _fetch(url, opts); }
  };
})();
 // --- end safe wrapper ---

// --- saldo: atualizar via API ---
async function updateBalance() {
  const $btn = document.querySelector('#btn-balance');
  const $out = document.querySelector('#saldo-valor') || document.querySelector('#saldo') || document.querySelector('.saldo, .big');

  try {
    if ($btn) { $btn.disabled = true; $btn.dataset._txt ??= $btn.textContent; $btn.textContent = 'Atualizando…'; }

    const r = await api('/api/v1/transactions/balance', { headers: { ...authHdr() }});
    if (!r.ok) {
      if (r.status === 401) {
        localStorage.removeItem('access_token');
        alert('Sessão expirada. Entre novamente.');
        return;
      }
      throw new Error('HTTP ' + r.status);
    }
    const data = await r.json();            // { saldo: number }
    const valor = Number(data.saldo ?? 0);

    if ($out) $out.textContent = valor.toFixed(0); // ou toFixed(2) se preferir cents
    console.log('[UI] saldo =', valor);
  } catch (e) {
    console.error('[UI] erro saldo:', e);
    alert('Erro ao atualizar saldo.');
  } finally {
    if ($btn) { $btn.disabled = false; $btn.textContent = $btn.dataset._txt || 'Atualizar saldo'; }
  }
}

// botão "Atualizar saldo"
document.querySelector('#btn-balance')?.addEventListener('click', updateBalance);

// se já tiver token salvo, atualiza saldo quando a página carregar
if (localStorage.getItem('access_token')) {
  updateBalance();
}
if (localStorage.getItem("access_token")) { updateBalance(); }
// --- harden: transferência com logs detalhados ---
(function () {
  const btn = document.querySelector('#btn-transferir');
  if (!btn) return;

  // remove listeners duplicados
  const clone = btn.cloneNode(true);
  btn.parentNode.replaceChild(clone, btn);

  clone.addEventListener('click', async () => {
    const token = localStorage.getItem('access_token');
    if (!token) { alert('Entre primeiro.'); return; }

    const email = document.querySelector('#destinatario')?.value?.trim();
    const valorStr = document.querySelector('#valor_transfer')?.value?.trim();
    const desc  = document.querySelector('#descricao_transfer')?.value?.trim() || '';

    const valor = Number(parseFloat(valorStr));
    if (!email || !Number.isFinite(valor) || valor <= 0) {
      alert('Informe destinatário e valor válido.'); return;
    }

    const url = '/api/v1/transactions/transfer';
    clone.disabled = true;

    try {
      const r = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({ destino_email: email, valor, descricao: desc })
      });

      if (!r.ok) {
        const txt = await r.text().catch(()=>'');
        console.error('[UI] transfer fail', r.status, url, txt);
        alert('Falha na transferência: ' + r.status);
        return;
      }

      alert('Transferência realizada ✅');
      try { window.updateBalance?.(); } catch {}
      try { window.loadHistorico?.(); } catch {}
    } catch (e) {
      console.error('[UI] erro na transferência', e);
      alert('Erro na transferência.');
    } finally {
      clone.disabled = false;
    }
  });
})();

// ===== fallback robusto para transferência =====
async function postJSON(url, token, payload) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type':'application/json', 'Authorization':'Bearer '+token },
    body: JSON.stringify(payload),
  });
  return r;
}

async function tentaTransferencia(token, email, valor, desc) {
  const urls = [
    '/api/v1/transactions/transfer',
    '/api/v1/transfer',
    '/api/v1/transactions/transferir'
  ];
  const corpos = [
    { destino_email: email, valor, descricao: desc },
    { destinatario_email: email, valor, descricao: desc },
    { destinatario: email, valor, descricao: desc },
    { destino: email, valor, descricao: desc }
  ];

  const erros = [];
  for (const url of urls) {
    for (const body of corpos) {
      try {
        const r = await postJSON(url, token, body);
        if (r.ok) return { ok:true, url, body, r };
        const txt = await r.text().catch(()=> '');
        erros.push({ url, body, status:r.status, txt });
        // 404/405/501/500 -> tenta próximo combo
        if (![400,401,403].includes(r.status)) continue;
      } catch (e) {
        erros.push({ url, body, status:'fetch_err', txt:String(e) });
      }
    }
  }
  return { ok:false, erros };
}
// --- handler de transferência com fallback e mensagens claras ---
(function () {
  const btnOld = document.querySelector('#btn-transferir');
  if (!btnOld) return;

  // substitui o botão por um clone pra garantir que só exista 1 listener
  const btn = btnOld.cloneNode(true);
  btnOld.replaceWith(btn);

  btn.addEventListener('click', async () => {
    const token = localStorage.getItem('access_token');
    if (!token) { alert('Entre primeiro.'); return; }

    const email = document.querySelector('#destinatario')?.value?.trim();
    const valorStr = document.querySelector('#valor_transfer')?.value?.trim();
    const desc = document.querySelector('#descricao_transfer')?.value?.trim() || '';
    const valor = Number(parseFloat(valorStr));

    if (!email || !Number.isFinite(valor) || valor <= 0) {
      alert('Informe destinatário e valor válido.');
      return;
    }

    btn.disabled = true;
    try {
      // usa o fallback que testará várias rotas/corpos
      const res = await tentaTransferencia(token, email, valor, desc);
      if (res.ok) {
        alert('Transferência realizada ✅');
        try { window.updateBalance?.(); } catch {}
        try { window.loadHistorico?.(); } catch {}
      } else {
        console.error('[UI] transfer falhou - tentativas:', res.erros);
        const ultimo = res.erros?.[res.erros.length-1] || {};
        const msg = (ultimo.txt && ultimo.txt.length < 300) ? ` ${ultimo.txt}` : '';
        alert(`Falha na transferência. Último status: ${ultimo.status ?? 'desconhecido'}.${msg}`);
      }
    } catch (e) {
      console.error('[UI] erro na transferência', e);
      alert('Erro na transferência.');
    } finally {
      btn.disabled = false;
    }
  });
})();

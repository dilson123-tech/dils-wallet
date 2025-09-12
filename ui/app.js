document.addEventListener('DOMContentLoaded', () => {
  const BASE = window.DILS_BASE || localStorage.getItem('BASE') || 'http://127.0.0.1:8686';
  const authHdr = () => {
    const t = localStorage.getItem('token');
    return t ? { 'Authorization': 'Bearer ' + t } : {};
  };

  // LOGIN
  const btnLogin = document.getElementById('btn-login');
  btnLogin?.addEventListener('click', async () => {
    try {
      const email = document.getElementById('email').value;
      const pass  = document.getElementById('pass').value;
      const r = await fetch(`${BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type':'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password: pass })
      });
      const j = await r.json();
      if (j.access_token) {
        localStorage.setItem('token', j.access_token);
        document.getElementById('authState').textContent = 'Autenticado';
        alert('Login OK!');
      } else { alert('Falha no login'); }
    } catch(e){ console.error(e); alert('Erro no login'); }
  });

  // LOGOUT
  document.getElementById('btn-logout')
    ?.addEventListener('click', () => {
      localStorage.removeItem('token');
      document.getElementById('authState').textContent = 'Não autenticado';
      alert('Saiu');
    });
  // ATUALIZAR SALDO
  const saldoBtn = document.getElementById('btn-atualizar');
  if (saldoBtn) {
    saldoBtn.addEventListener('click', async () => {
      try {
        const r = await fetch(`${BASE}/api/v1/transactions/balance`, { headers: authHdr() });
        const j = await r.json();
        document.getElementById('saldo').textContent = j.saldo ?? '--';
      } catch(e){ console.error(e); alert('Erro ao atualizar saldo'); }
    });
  }

  // CARREGAR EXTRATO
  const extratoBtn = document.getElementById('btn-extrato');
  if (extratoBtn) {
    extratoBtn.addEventListener('click', async () => {
      try {
        const r = await fetch(`/api/v1/transactions/paged?wallet_id=1&page=1&page_size=20`, { headers: authHdr() });
        const data = await r.json();
        const tbody = document.getElementById('tx-body');
        tbody.innerHTML = '';
        (data.items || data).forEach(tx => {
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${tx.id}</td><td>${tx.tipo||tx.type}</td><td>${tx.valor||tx.amount}</td><td>${tx.data||tx.created_at}</td>`;
          tbody.appendChild(tr);
        });
      } catch(e){ console.error(e); alert('Erro ao carregar extrato'); }
    });
  }

  // EXPORTAR CSV
  const csvBtn = document.getElementById('btn-exportar-csv');
  if (csvBtn) {
    csvBtn.addEventListener('click', async () => {
      try {
        const r = await fetch(`/api/v1/transactions/export.csv?wallet_id=1`, { headers: authHdr() });
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'extrato.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch(e){ console.error(e); alert('Erro ao exportar CSV'); }
    });
  }
});

// --- Transferência ---
(() => {
  const btn = document.getElementById('btn-transferir');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const email = document.getElementById('transfer-email').value.trim();
    const valor = parseFloat(document.getElementById('transfer-valor').value);
    const desc  = document.getElementById('transfer-descricao').value.trim();
    if (!email || isNaN(valor)) { alert('Preencha email e valor'); return; }
    try {
      const r = await fetch(`${BASE}/api/v1/transactions/transfer`, {
        method: 'POST',
        headers: { ...authHdr(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_destinatario: email, valor, descricao: desc })
      });
      if (!r.ok) throw new Error(await r.text());
      alert('Transferência concluída!');
    } catch(e) {
      console.error('Transfer erro', e);
      alert('Erro na transferência');
    }
  });
})();
function __clearTransferFields(){
  const e = document.getElementById('transfer-email');     if(e) e.value = '';
  const v = document.getElementById('transfer-valor');     if(v) v.value = '';
  const d = document.getElementById('transfer-descricao'); if(d) d.value = '';
}
document.getElementById('btn-logout')?.addEventListener('click', __clearTransferFields);

// ===== HOTFIX P1: utils + Extrato =====
(() => {
  const BASE = window.DILS_BASE || localStorage.getItem('BASE') || 'http://127.0.0.1:8686';
  const authHdr = () => {
    const t = localStorage.getItem('token');
    return t ? { 'Authorization': 'Bearer ' + t } : {};
  };

  // util: rebind sem listeners antigos
  const rebind = (id, handler) => {
    const old = document.getElementById(id);
    if (!old) return;
    const clone = old.cloneNode(true);
    old.replaceWith(clone);
    clone.addEventListener('click', handler);
  };

  // limpa campos de transferência
  function __clearTransferFields(){
    const e = document.getElementById('transfer-email');     if (e) e.value = '';
    const v = document.getElementById('transfer-valor');     if (v) v.value = '';
    const d = document.getElementById('transfer-descricao'); if (d) d.value = '';
  }
  window.__clearTransferFields = __clearTransferFields; // deixa global p/ P2

  // Extrato (/api/v1/transactions/paged)
  rebind('btn-extrato', async () => {
    try {
      const url = `${BASE}/api/v1/transactions/paged?wallet_id=1&page=1&page_size=20`;
      const r = await fetch(url, { headers: authHdr() });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      const tbody = document.getElementById('tx-body');
      if (!tbody) { alert('Tabela do extrato não encontrada'); return; }
      tbody.innerHTML = '';
      (data.items || data || []).forEach(tx => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${tx.id ?? ''}</td>
          <td>${tx.tipo ?? tx.type ?? ''}</td>
          <td>${tx.valor ?? tx.amount ?? ''}</td>
          <td>${tx.referencia ?? tx.descricao ?? tx.description ?? ''}</td>
          <td>${tx.criado_em ?? tx.created_at ?? tx.data ?? ''}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error('extrato erro', e);
      alert('Erro ao carregar extrato');
    }
  });
})();

// ===== HOTFIX P2: Transferência + Logout =====
(() => {
  const BASE = window.DILS_BASE || localStorage.getItem('BASE') || 'http://127.0.0.1:8686';
  const authHdr = () => {
    const t = localStorage.getItem('token');
    return t ? { 'Authorization': 'Bearer ' + t } : {};
  };

  const rebind = (id, handler) => {
    const old = document.getElementById(id);
    if (!old) return;
    const clone = old.cloneNode(true);
    old.replaceWith(clone);
    clone.addEventListener('click', handler);
  };

  // Transferência (payload: destino_email, valor, referencia)
  rebind('btn-transferir', async () => {
    const email = (document.getElementById('transfer-email')||{}).value?.trim();
    const valor = parseFloat((document.getElementById('transfer-valor')||{}).value);
    const desc  = (document.getElementById('transfer-descricao')||{}).value?.trim();
    if (!email || Number.isNaN(valor)) { alert('Preencha e-mail e valor'); return; }
    try {
      const r = await fetch(`${BASE}/api/v1/transactions/transfer`, {
        method: 'POST',
        headers: { ...authHdr(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ destino_email: email, valor, referencia: desc || null })
      });
      if (!r.ok) throw new Error(await r.text());
      alert('Transferência concluída!');
      (window.__clearTransferFields||(()=>{}))();
    } catch (e) {
      console.error('transfer erro', e);
      alert('Erro na transferência');
    }
  });

  // Logout: limpa token + campos
  rebind('btn-logout', () => {
    localStorage.removeItem('token');
    const s = document.getElementById('authState'); if (s) s.textContent = 'Não autenticado';
    (window.__clearTransferFields||(()=>{}))();
    alert('Saiu');
  });
})();

// ===== HOTFIX: Transferir aceita múltiplos IDs de input =====
(() => {
  const BASE = window.DILS_BASE || localStorage.getItem('BASE') || 'http://127.0.0.1:8686';
  const authHdr = () => {
    const t = localStorage.getItem('token');
    return t ? { 'Authorization': 'Bearer ' + t } : {};
  };
  const rebind = (id, handler) => {
    const old = document.getElementById(id);
    if (!old) return;
    const clone = old.cloneNode(true);
    old.replaceWith(clone);
    clone.addEventListener('click', handler);
  };
  const getValByAnyId = (ids) => {
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el && el.value != null) return el.value;
    }
    return '';
  };
  const clearByIds = (ids) => ids.forEach(id => { const el = document.getElementById(id); if (el) el.value=''; });

  rebind('btn-transferir', async () => {
    const email = (getValByAnyId(['transfer-email','destinatario']) || '').trim();
    const valorStr = (getValByAnyId(['transfer-valor','valor_transfer']) || '').replace(',', '.');
    const valor = parseFloat(valorStr);
    const desc  = (getValByAnyId(['transfer-descricao','descricao_transfer']) || '').trim();

    if (!email || Number.isNaN(valor)) { alert('Preencha e-mail e valor'); return; }

    try {
      const r = await fetch(`${BASE}/api/v1/transactions/transfer`, {
        method: 'POST',
        headers: { ...authHdr(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ destino_email: email, valor, referencia: desc || null })
      });
      if (!r.ok) throw new Error(await r.text());
      alert('Transferência concluída!');
      clearByIds(['transfer-email','destinatario','transfer-valor','valor_transfer','transfer-descricao','descricao_transfer']);
    } catch (e) {
      console.error('transfer erro', e);
      alert('Erro na transferência');
    }
  });
})();
// --- PATCH TRANSFER SIMPLES ---
(() => {
  const btn = document.getElementById('btn-transferir');
  if (!btn || btn.dataset.bound) return;
  btn.dataset.bound = '1';

  btn.addEventListener('click', async () => {
    const email = document.getElementById('destinatario')?.value.trim();
    const valor = parseFloat(document.getElementById('valor_transfer')?.value);
    const ref   = document.getElementById('descricao_transfer')?.value.trim() || '';

    if (!email || !(valor > 0)) {
      alert('Informe e-mail e valor > 0.');
      return;
    }

    btn.disabled = true;
    try {
      const r = await fetch(`${BASE}/api/v1/transactions/transfer`, {
        method: 'POST',
        headers: { ...authHdr(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ destino_email: email, valor, referencia: ref })
      });
      const j = await r.json();
      if (r.ok && j.ok) {
        alert(`✅ Transferido R$ ${valor.toFixed(2)} para ${email}`);
      } else if (r.status === 404) {
        alert('⚠️ Destinatário não encontrado.');
      } else {
        alert(`⚠️ Erro ${r.status}: ${j.detail || 'verifique os dados'}`);
      }
    } catch (e) {
      console.error(e);
      alert('Falha de rede.');
    } finally {
      btn.disabled = false;
    }
  });
})();

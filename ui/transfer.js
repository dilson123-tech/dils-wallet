
(() => {
  'use strict';

  function getToken() {
    const keys = ['access_token','token','jwt','auth_token'];
    for (const k of keys) {
      const v = localStorage.getItem(k) || sessionStorage.getItem(k);
      if (v) return v;
    }
    return null;
  }

  async function postTransfer({ email, valor, referencia }) {
    const token = getToken();
    if (!token) throw new Error('Sem token. Faça login primeiro.');
    const res = await fetch('/api/v1/transactions/transfer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        destino_email: email,
        valor: Number(valor),
        referencia: referencia || null
      })
    });
    const isJson = (res.headers.get('content-type') || '').includes('application/json');
    const data = isJson ? await res.json() : await res.text();
    if (!res.ok) throw new Error(typeof data === 'string'
      ? data
      : (data.detail || JSON.stringify(data)));
    return data;
  }

  function mountUI() {
    if (document.getElementById('transfer-section')) return; // idempotente

    const container = document.getElementById('app') || document.body;
    const section = document.createElement('section');
    section.id = 'transfer-section';
    section.style.cssText = 'margin-top:16px;padding:12px;border:1px solid #ddd;border-radius:8px';

    section.innerHTML = `
      <h2 style="margin:0 0 8px 0;">Transferência</h2>
      <form id="transfer-form" style="display:grid;gap:8px;max-width:420px;">
        <label>E-mail do destinatário
          <input type="email" id="trgEmail" required placeholder="destino@dilswallet.com" style="width:100%;">
        </label>
        <label>Valor (R$)
          <input type="number" id="trgValor" required min="0.01" step="0.01" placeholder="25.00" style="width:100%;">
        </label>
        <label>Referência (opcional)
          <input type="text" id="trgRef" placeholder="ex: primeira-transfer" style="width:100%;">
        </label>
        <button type="submit" id="btnTransfer">Transferir</button>
      </form>
      <div id="transfer-msg" style="margin-top:8px;font-size:0.95rem;"></div>
    `;
    container.appendChild(section);

    const form = section.querySelector('#transfer-form');
    const msg  = section.querySelector('#transfer-msg');

    // (Parte 2 continua abaixo: listener + saldo + bootstrap)
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      msg.textContent = 'Enviando...';
      try {
        const email = section.querySelector('#trgEmail').value.trim();
        const valor = section.querySelector('#trgValor').value;
        const referencia = section.querySelector('#trgRef').value.trim();

        await postTransfer({ email, valor, referencia });
        msg.textContent = '✅ Transferência concluída.';
        form.reset();

        // (Opcional) atualizar saldo rapidamente
        try {
          const token = getToken();
          if (token) {
            const r = await fetch('/api/v1/transactions/balance', {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            if (r.ok) {
              const j = await r.json();
              msg.textContent += ` Saldo atualizado: R$ ${Number(j.saldo).toFixed(2)}.`;
            }
          }
        } catch (_) { /* silencioso */ }
      } catch (err) {
        msg.textContent = '❌ ' + (err?.message || 'Erro ao transferir.');
      }
    });
  }

  // Bootstrap idempotente
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountUI);
  } else {
    mountUI();
  }
})();

const PATH_LOGIN = '/api/v1/auth/login';
const PATH_TX    = '/api/v1/transactions';
const PATH_TX_BAL= '/api/v1/transactions/balance';
const PATH_TX_XF = '/api/v1/transactions/transfer';

let TOKEN = localStorage.getItem('token') || '';
const $ = (id) => document.getElementById(id);

function setAuthState(){
  const ok = !!TOKEN;
  $('authState') && ($('authState').textContent = ok ? 'Autenticado ✓' : 'Sem token');
  $('btn-salvar') && ($('btn-salvar').disabled = !ok);
}

function logout(){
  TOKEN = '';
  localStorage.removeItem('token');
  setAuthState();
  $('saldo') && ($('saldo').textContent='--');
  const tb = $('tbody'); if (tb) tb.innerHTML='';
  $('msg') && ($('msg').textContent='');
}

window.addEventListener('DOMContentLoaded', ()=>{
  $('msg') && ($('msg').textContent='');
  setAuthState();
  $('btn-logout')?.addEventListener('click', logout);
});
async function login(){
  const email = $('email')?.value?.trim() || '';
  const password = $('pass')?.value || '';
  const body = new URLSearchParams({username: email, password});
  const r = await fetch(PATH_LOGIN, {
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body
  });
  const j = await r.json();
  TOKEN = j.access_token || '';
  if (TOKEN){
    localStorage.setItem('token', TOKEN);
    $('msg') && ($('msg').textContent = '');
    setAuthState();
  } else {
    $('msg') && ($('msg').textContent = 'Falha no login');
  }
}
document.addEventListener('DOMContentLoaded', ()=>{
  $('btn-login')?.addEventListener('click', login);
});
async function loadData(){
  setAuthState();
  if(!TOKEN) return;
  const h = { Authorization: 'Bearer '+TOKEN };

  try{
    const s = await fetch(PATH_TX_BAL, {headers:h});
    const sj = await s.json();
    const el = $('saldo'); if(el) el.textContent = sj?.saldo ?? '--';
  }catch{}

  try{
    const r = await fetch(PATH_TX, {headers:h});
    const arr = await r.json();
    const tb = $('tbody'); if(!tb) return;
    tb.innerHTML = '';
    (Array.isArray(arr)? arr:[]).sort((a,b)=>(b.id||0)-(a.id||0)).forEach(t=>{
      const tr = document.createElement('tr');
      const pill = t.tipo==='deposito'?'dep':t.tipo==='saque'?'saq':'tra';
      tr.innerHTML = `<td>${t.id??''}</td>
        <td><span class="pill ${pill}">${t.tipo??''}</span></td>
        <td>R$ ${(Number(t.valor||0)).toFixed(2)}</td>
        <td>${t.referencia||''}</td>
        <td>${(t.criado_em||'').replace('T',' ').split('.')[0]}</td>`;
      tb.appendChild(tr);
    });
  }catch{}
}
document.addEventListener('DOMContentLoaded', ()=>{
  $('btn-atualizar')?.addEventListener('click', loadData);
  if(TOKEN) loadData();
});
async function criar(){
  if(!TOKEN){ $('msg') && ($('msg').textContent='Faça login antes.'); return; }
  const tipo = $('tipo')?.value || 'deposito';
  const valor = Number($('valor')?.value || 0);
  const referencia = $('ref')?.value || '';
  if(!(valor>0)){ $('msg') && ($('msg').textContent='Valor deve ser > 0'); return; }

  if (tipo === 'transferencia'){
    $('msg') && ($('msg').textContent='Transferência pela UI ainda não está habilitada aqui. Use depósito/saque por enquanto.');
    return;
  }

  const r = await fetch(PATH_TX, {
    method:'POST',
    headers:{'Content-Type':'application/json', Authorization:'Bearer '+TOKEN},
    body: JSON.stringify({tipo, valor, referencia})
  });
  const j = await r.json();
  if(r.ok){
    $('msg') && ($('msg').textContent='Transação criada ✓');
    $('valor') && ($('valor').value='');
    $('ref') && ($('ref').value='');
    loadData();
  }else{
    $('msg') && ($('msg').textContent = j?.detail || 'Erro ao criar');
  }
}
document.addEventListener('DOMContentLoaded', ()=>{
  $('btn-salvar')?.addEventListener('click', criar);
});
async function transferir(){
  if(!TOKEN){ $('msg') && ($('msg').textContent='Faça login antes.'); return; }
  const dest = $('xf-email')?.value?.trim() || '';
  const valor = Number($('xf-valor')?.value || 0);
  const referencia = $('xf-ref')?.value || '';
  if(!dest || !dest.includes('@')){ $('msg') && ($('msg').textContent='E-mail destino inválido'); return; }
  if(!(valor>0)){ $('msg') && ($('msg').textContent='Valor deve ser > 0'); return; }

  try{
    const r = await fetch('/api/v1/transactions/transfer', {
      method:'POST',
      headers:{'Content-Type':'application/json', Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({destino_email: dest, valor, referencia})
    });
    const j = await r.json();
    if(r.ok){
      $('msg') && ($('msg').textContent = `Transferência OK → ${dest} (R$ ${valor.toFixed(2)})`);
      $('xf-valor') && ($('xf-valor').value='');
      $('xf-ref') && ($('xf-ref').value='');
      loadData();
    }else{
      $('msg') && ($('msg').textContent = j?.detail || 'Erro na transferência');
    }
  }catch{
    $('msg') && ($('msg').textContent='Erro de rede');
  }
}
document.addEventListener('DOMContentLoaded', ()=>{
  $('btn-xfer')?.addEventListener('click', transferir);
});


// === Dils Wallet: Pager de Transações (paged API) ===
window.addEventListener("load", function(){
(function () {
  const prevBtn = document.getElementById('tx-prev');
  const nextBtn = document.getElementById('tx-next');
  const pageEl  = document.getElementById('tx-page');
  const sizeSel = document.getElementById('tx-page-size');
  const tbody   = document.getElementById('tx-paged-tbody');
  const metaEl  = document.getElementById('tx-meta');
  if (!prevBtn || !nextBtn || !pageEl || !sizeSel || !tbody) return; // UI antiga? então não faz nada

  let page = 1;
  let pageSize = parseInt(sizeSel.value || '10', 10) || 10;

  function getToken(){
  try{ if(typeof TOKEN!=="undefined" && TOKEN) return TOKEN; }catch(_){ }

    return (window.AUTH_TOKEN)
        || (window.token)
        || localStorage.getItem('auth_token')
        || localStorage.getItem('token')
        || '';
  }

  async function fetchPaged() {
    const token = getToken();
    pageEl.textContent = String(page);
    prevBtn.disabled = page <= 1;

    if (!token) {
      metaEl.textContent = 'Faça login para listar as transações.';
      tbody.innerHTML = '';
      nextBtn.disabled = true;
      return;
    }

    metaEl.textContent = "Carregando…";
      prevBtn.disabled = true;
      nextBtn.disabled = true;
      sizeSel.disabled = true;
      const url = `/api/v1/transactions/paged?page=${page}&page_size=${pageSize}`;
    try {
      const res = await fetch(url, { headers: { 'Authorization': `Bearer ${token}` } });
      if (!res.ok) {
        metaEl.textContent = `Erro ${res.status}`;
        tbody.innerHTML = '';
        nextBtn.disabled = true;
        return;
      }
      const data = await res.json();
      tbody.innerHTML = '';
      (data.items || []).forEach(t => {
        const tr = document.createElement('tr');
        const criado = t.criado_em || t.created_at || '';
        tr.innerHTML = `<td>${t.id}</td><td>${t.tipo}</td><td>${t.valor}</td><td>${t.referencia || ''}</td><td>${criado}</td>`;
        tbody.appendChild(tr);
      });
      const m = data.meta || {};
      metaEl.textContent = `total ${m.total ?? 0} • páginas ${m.total_pages ?? 1}`;
      nextBtn.disabled = !(m.has_next);
      prevBtn.disabled = page <= 1;
      sizeSel.disabled = false;
    } catch (e) {
      metaEl.textContent = 'Erro de rede';
      tbody.innerHTML = '';
      nextBtn.disabled = true;
    }
  }

  prevBtn.addEventListener('click', () => { if (page > 1) { page--; fetchPaged(); } });
  nextBtn.addEventListener('click', () => { page++; fetchPaged(); });
  sizeSel.addEventListener('change', () => { pageSize = parseInt(sizeSel.value || '10', 10) || 10; page = 1; fetchPaged(); });

  // tenta rodar após o load (se já tiver token, lista; senão mostra dica de login)
  window.addEventListener('load', () => setTimeout(fetchPaged, 300));

  // expõe um hook opcional para o fluxo de login existente
  window.dilsPagedRefresh = fetchPaged;
})()
});
;


/* === Pager v2 (robusto, auto-boot) === */
(function(){
  function boot(){
    const prevBtn = document.getElementById('tx-prev');
    const nextBtn = document.getElementById('tx-next');
    const pageEl  = document.getElementById('tx-page');
    const sizeSel = document.getElementById('tx-page-size');
    const tbody   = document.getElementById('tx-paged-tbody');
    const metaEl  = document.getElementById('tx-meta');
    if (!prevBtn || !nextBtn || !pageEl || !sizeSel || !tbody) return;
    if (tbody.dataset.pagerBound) return; // evita dupla ligação

    let page = 1;
    let pageSize = parseInt(sizeSel.value || '10', 10) || 10;

    function getToken(){
      return (window.AUTH_TOKEN) || (window.token) ||
             localStorage.getItem('auth_token') || localStorage.getItem('token') || '';
    }

    async function fetchPaged(){
      const t = getToken();
      pageEl.textContent = String(page);
      prevBtn.disabled = page <= 1;

      if (!t){
        metaEl.textContent = 'Faça login para listar as transações.';
        tbody.innerHTML = '';
        nextBtn.disabled = true;
        return;
      }
      metaEl.textContent = "Carregando…";
      prevBtn.disabled = true;
      nextBtn.disabled = true;
      sizeSel.disabled = true;
      const url = `/api/v1/transactions/paged?page=${page}&page_size=${pageSize}`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${t}` } });
      if (!res.ok){
        metaEl.textContent = `Erro ${res.status}`;
        tbody.innerHTML = '';
        nextBtn.disabled = true;
        return;
      }
      const data = await res.json();
      tbody.innerHTML = '';
      (data.items || []).forEach(it => {
        const tr = document.createElement('tr');
        const criado = it.criado_em || it.created_at || '';
        tr.innerHTML = `<td>${it.id}</td><td>${it.tipo}</td><td>${it.valor}</td><td>${it.referencia || ''}</td><td>${criado}</td>`;
        tbody.appendChild(tr);
      });
      const m = data.meta || {};
      metaEl.textContent = `total ${m.total ?? 0} • páginas ${m.total_pages ?? 1}`;
      nextBtn.disabled = !(m.has_next);
      prevBtn.disabled = page <= 1;
      sizeSel.disabled = false;
    }

    prevBtn.addEventListener('click', () => { if (page > 1){ page--; fetchPaged(); } });
    nextBtn.addEventListener('click', () => { page++; fetchPaged(); });
    sizeSel.addEventListener('change', () => { pageSize = parseInt(sizeSel.value || '10', 10) || 10; page = 1; fetchPaged(); });

    tbody.dataset.pagerBound = '1';
    window.dilsPagedRefresh = fetchPaged;
    fetchPaged();
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive'){
    setTimeout(boot, 0);
  } else {
    window.addEventListener('DOMContentLoaded', boot);
  }
})();

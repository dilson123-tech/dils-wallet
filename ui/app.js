const PATH_LOGIN = '/api/v1/auth/login';
let TOKEN = localStorage.getItem('token') || '';

const $ = (id) => document.getElementById(id);

function setAuthState(){
  const ok = !!TOKEN;
  $('authState') && ($('authState').textContent = ok ? 'Autenticado ✓' : 'Sem token');
  $('btn-salvar') && ($('btn-salvar').disabled = !ok);
}

async function login(){
  const email = $('email').value.trim();
  const password = $('pass').value;
  const body = new URLSearchParams({username: email, password});
  const r = await fetch(PATH_LOGIN, {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body});
  const j = await r.json();
  TOKEN = j.access_token || '';
  if (TOKEN){
    localStorage.setItem('token', TOKEN);
    $('msg').textContent = '';
    setAuthState();
    loadData();
  } else {
    $('msg').textContent = 'Falha no login';
  }
}

function logout(){
  TOKEN = '';
  localStorage.removeItem('token');
  setAuthState();
  // limpa UI
  $('saldo') && ($('saldo').textContent = '--');
  const tbody = $('tbody'); if (tbody) tbody.innerHTML = '';
  $('msg').textContent = '';
}

async function loadData(){
  $('msg').textContent = '';
  setAuthState();
  if (!TOKEN) return;
  const h = {Authorization: 'Bearer '+TOKEN};

  try {
    const s = await fetch('/api/v1/transactions/balance', {headers:h});
    const sj = await s.json();
    $('saldo') && ($('saldo').textContent = sj?.saldo ?? '--');
  } catch {}

  try {
    const l = await fetch('/api/v1/transactions', {headers:h});
    const lj = await l.json();
    const tbody = $('tbody'); if (!tbody) return;
    tbody.innerHTML = '';
    (Array.isArray(lj)? lj:[]).sort((a,b)=>(b.id||0)-(a.id||0)).forEach(t=>{
      const tr = document.createElement('tr');
      const pill = t.tipo==='deposito'?'dep':t.tipo==='saque'?'saq':'tra';
      tr.innerHTML = `<td>${t.id??''}</td>
        <td><span class="pill ${pill}">${t.tipo??''}</span></td>
        <td>R$ ${(Number(t.valor||0)).toFixed(2)}</td>
        <td>${t.referencia||''}</td>
        <td>${(t.criado_em||'').replace('T',' ').split('.')[0]}</td>`;
      tbody.appendChild(tr);
    });
  } catch {}
}

async function criar(){
  if (!TOKEN){ $('msg').textContent='Faça login antes.'; return; }
  const payload = { tipo:$('tipo').value, valor:Number($('valor').value), referencia:$('ref').value };
  const r = await fetch('/api/v1/transactions', {
    method:'POST', headers:{'Content-Type':'application/json', Authorization:'Bearer '+TOKEN},
    body: JSON.stringify(payload)
  });
  const j = await r.json();
  if (r.ok){ $('msg').textContent='Transação criada ✓'; $('valor').value=''; $('ref').value=''; loadData(); }
  else { $('msg').textContent = j?.detail || 'Erro ao criar'; }
}

window.addEventListener('DOMContentLoaded', ()=>{
  $('msg').textContent = '';
  setAuthState();
  $('btn-login')?.addEventListener('click', login);
  $('btn-logout')?.addEventListener('click', logout);
  $('btn-atualizar')?.addEventListener('click', loadData);
  $('btn-salvar')?.addEventListener('click', criar);
  if (TOKEN) loadData();
});

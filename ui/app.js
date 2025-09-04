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

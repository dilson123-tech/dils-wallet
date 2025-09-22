const BASE = window.location.origin;

// Helpers
function show(el){el.classList.remove('hidden')}
function hide(el){el.classList.add('hidden')}
async function api(path, opts={}){
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type':'application/json', ...opts.headers };
  if(token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if(res.status === 401){
    localStorage.removeItem('token');
    show(document.getElementById('loginForm'));
    hide(document.getElementById('dashboard'));
  }
  return res;
}

// Elements
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const dash = document.getElementById('dashboard');
const saldoSpan = document.getElementById('saldoSpan');
const extratoList = document.getElementById('extratoList');
const logoutBtn = document.getElementById('logoutBtn');
const btnDepositar = document.getElementById('btnDepositar');
const btnSacar = document.getElementById('btnSacar');

async function loadSaldo() {
  const r = await api('/api/v1/transactions/balance');
  if(!r.ok) return;
  const j = await r.json();
  saldoSpan.textContent = Number(j.saldo).toFixed(2);

  const extrato = await api('/api/v1/transactions/paged?page=1&page_size=10');
  if(!extrato.ok) return;
  const ej = await extrato.json();
  extratoList.innerHTML = (ej.items||[]).map(i =>
    `<li>${i.tipo} - R$ ${Number(i.valor).toFixed(2)} (${new Date(i.created_at).toLocaleString()})</li>`
  ).join('');
}

loginForm.onsubmit = async e => {
  e.preventDefault();
  hide(loginError); loginError.textContent = '';
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;

  // >>> ajuste importante: grant_type + scope <<<
  const body = new URLSearchParams({grant_type:'password', username: email, password, scope:''});
  const r = await fetch(`${BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: {'Content-Type':'application/x-www-form-urlencoded'},
    body
  });
  if(!r.ok){
    loginError.textContent = 'Login inválido';
    show(loginError);
    return;
  }
  const j = await r.json();
  localStorage.setItem('token', j.access_token);
  hide(loginForm);
  show(dash);
  await loadSaldo();
};

logoutBtn.onclick = () => {
  localStorage.removeItem('token');
  hide(dash);
  show(loginForm);
};

btnDepositar.onclick = async () => {
  const r = await api('/api/v1/transactions', {
    method: 'POST',
    body: JSON.stringify({tipo:'deposito', valor:10, descricao:'via UI'})
  });
  if(!r.ok){
    const j = await r.json().catch(()=>({detail:'erro'}));
    alert(`Depósito falhou: ${j.detail||r.status}`);
    return;
  }
  await loadSaldo();
};

btnSacar.onclick = async () => {
  const r = await api('/api/v1/transactions', {
    method: 'POST',
    body: JSON.stringify({tipo:'saque', valor:10, descricao:'via UI'})
  });
  if(!r.ok){
    const j = await r.json().catch(()=>({detail:'erro'}));
    alert(`Saque falhou: ${j.detail||r.status}`);
    return;
  }
  await loadSaldo();
};

// auto-login se token presente
if(localStorage.getItem('token')){
  hide(loginForm);
  show(dash);
  loadSaldo();
}

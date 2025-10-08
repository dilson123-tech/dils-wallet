const BASE_PIX = "https://dils-wallet-production.up.railway.app/api/v1/pix";

const els = {
  totalCount: document.getElementById("totalCount"),
  totalAmount: document.getElementById("totalAmount"),
  avgAmount: document.getElementById("avgAmount"),
  lastTx: document.getElementById("lastTx"),
  debug: document.getElementById("debugArea"),
  refresh: document.getElementById("btn-refresh"),
  chartCanvas: document.getElementById("summaryChart"),
};

let chartRef = null;

function brl(n) {
  if (typeof n !== "number") n = Number(n || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function getJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`HTTP ${r.status} @ ${url}`);
  return r.json();
}

function drawChart(summary) {
  const labels = summary.map(x => `Conta ${x.account_id}`);
  const values = summary.map(x => Number(x.net_balance || 0));
  const colors = values.map(v => (v >= 0 ? "rgba(0, 160, 0, 0.7)" : "rgba(200, 0, 0, 0.7)"));
  const borders = values.map(v => (v >= 0 ? "rgba(0, 120, 0, 1)" : "rgba(160, 0, 0, 1)"));

  if (chartRef) {
    chartRef.destroy();
  }

  chartRef = new Chart(els.chartCanvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Saldo líquido (R$)",
        data: values,
        backgroundColor: colors,
        borderColor: borders,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (v) => brl(v) }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${brl(ctx.parsed.y)}`
          }
        }
      }
    }
  });
}

async function loadAll() {
  try {
    const [stats, summary] = await Promise.all([
      getJSON(`${BASE_PIX}/stats`),
      getJSON(`${BASE_PIX}/summary`),
    ]);

    // Cards
    els.totalCount.textContent = stats.total_count ?? "0";
    els.totalAmount.textContent = brl(stats.total_amount ?? 0);
    els.avgAmount.textContent = brl(stats.avg_amount ?? 0);
    els.lastTx.textContent = stats.last_tx ?? "—";

    // Gráfico
    drawChart(summary || []);

    // Debug
    els.debug.textContent = JSON.stringify({ stats, summary }, null, 2);
  } catch (err) {
    const msg = `Erro ao carregar dados: ${err.message}`;
    console.error(msg);
    els.debug.textContent = msg;
  }
}

els.refresh?.addEventListener("click", loadAll);

// Auto-load
loadAll();
// === PATCH: auto-refresh + export CSV ===
(function () {
  const btnExport = document.getElementById("btn-export");

  // Auto-refresh a cada 10s
  setInterval(() => {
    if (document.hasFocus()) {
      loadAll();
    }
  }, 10000);

  // Exporta CSV gerado no navegador
  async function exportCSV() {
    try {
      const hist = await getJSON(`${BASE_PIX}/history?limit=200`);
      if (!Array.isArray(hist) || hist.length === 0) {
        alert("Sem dados para exportar.");
        return;
      }
      const headers = ["id","from_account_id","to_account_id","amount","created_at"];
      const rows = hist.map(x => [
        x.id, x.from_account_id, x.to_account_id, x.amount, x.created_at
      ]);

      // Monta CSV (escapando separador por vírgula)
      const toCSV = arr => arr.map(v => {
        const s = (v===null||v===undefined) ? "" : String(v);
        return /[",\n]/.test(s) ? `"${s.replace(/"/g,'""')}"` : s;
      }).join(",");

      const csv = [toCSV(headers), ...rows.map(toCSV)].join("\n");
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const ts = new Date().toISOString().replace(/[:.]/g,"-");
      a.href = url;
      a.download = `pix_history_${ts}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Falha ao exportar CSV: " + e.message);
      console.error(e);
    }
  }

  btnExport?.addEventListener("click", exportCSV);
})();

// ====== PATCH: período + gráfico de volume diário ======
const els2 = {
  periodSel: document.getElementById("periodSel"),
  volumeCanvas: document.getElementById("volumeChart"),
};
let chartVolumeRef = null;

function cutoffFrom(period){
  const now = new Date();
  if(period === "24h"){ return new Date(now.getTime() - 24*60*60*1000); }
  if(period === "7d"){  return new Date(now.getTime() - 7*24*60*60*1000); }
  return null; // all
}

function toDateOnlyISO(d){
  const z = new Date(d);
  const y = z.getUTCFullYear();
  const m = String(z.getUTCMonth()+1).padStart(2,"0");
  const dd= String(z.getUTCDate()).padStart(2,"0");
  return `${y}-${m}-${dd}`;
}

function buildDaily(history, period){
  const cut = cutoffFrom(period);
  const daily = new Map();
  (history||[]).forEach(tx=>{
    const t = new Date(tx.created_at);
    if(cut && t < cut) return; // filtra fora do período
    const key = toDateOnlyISO(t);
    const val = Number(tx.amount||0);
    daily.set(key, (daily.get(key)||0) + val);
  });
  // ordenar por dia
  return Array.from(daily.entries()).sort((a,b)=>a[0].localeCompare(b[0]));
}

function drawVolumeChart(pairs){
  const labels = pairs.map(p=>p[0]);
  const values = pairs.map(p=>p[1]);

  if(chartVolumeRef){ chartVolumeRef.destroy(); }
  chartVolumeRef = new Chart(els2.volumeCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Volume diário (R$)",
        data: values,
        fill: false,
        tension: 0.2
      }]
    },
    options: {
      responsive:true,
      animation:false,
      scales:{
        y:{beginAtZero:true, ticks:{callback:(v)=>brl(v)}}
      },
      plugins:{legend:{display:false}}
    }
  });
}

// Hook no seletor de período
els2.periodSel?.addEventListener("change", loadAll);

// ---- Patch em loadAll: incluir history e redesenhar volume ----
const _loadAll_orig = loadAll;
loadAll = async function(){
  try{
    const [stats, summary, history] = await Promise.all([
      getJSON(`${BASE_PIX}/stats`),
      getJSON(`${BASE_PIX}/summary`),
      getJSON(`${BASE_PIX}/history?limit=200`),
    ]);

    // preencher cards (reuso do original)
    els.totalCount.textContent = stats.total_count ?? "0";
    els.totalAmount.textContent = brl(stats.total_amount ?? 0);
    els.avgAmount.textContent = brl(stats.avg_amount ?? 0);
    els.lastTx.textContent = stats.last_tx ?? "—";

    // gráfico de saldo líquido por conta
    drawChart(summary || []);

    // gráfico de volume diário por período
    const period = els2.periodSel?.value || "all";
    const dailyPairs = buildDaily(history || [], period);
    drawVolumeChart(dailyPairs);

    // debug
    els.debug.textContent = JSON.stringify({ stats, summary, history, period, dailyPairs }, null, 2);
  }catch(err){
    const msg = `Erro ao carregar dados: ${err.message}`;
    console.error(msg);
    els.debug.textContent = msg;
  }
}

// ====== PATCH: Healthcheck em tempo real ======
const BASE_API = (function(){
  // BASE_PIX = https://.../api/v1/pix  => BASE_API = https://.../api/v1
  try { return BASE_PIX.replace(/\/pix\/?$/,""); } catch { return ""; }
})();

const hc = {
  badge: document.getElementById("hc-badge"),
  btn: document.getElementById("btn-health"),
  lastStatus: "warn",
};

function setBadge(state, msg){
  if(!hc.badge) return;
  hc.badge.classList.remove("badge-ok","badge-err","badge-warn");
  hc.badge.classList.add(
    state === "ok" ? "badge-ok" :
    state === "err" ? "badge-err" : "badge-warn",
    "badge"
  );
  hc.badge.textContent = msg;
  hc.badge.title = `Backend: ${msg}`;
  hc.lastStatus = state;
}

async function pingHealth(){
  try{
    const r = await fetch(`${BASE_API}/health`, { cache: "no-store" });
    const ok = r.ok;
    let txt = "";
    try { txt = await r.text(); } catch {}
    if(ok){
      setBadge("ok", "Online");
    } else {
      setBadge("err", `Erro ${r.status}`);
      console.error("Health NOK:", r.status, txt);
    }
  }catch(e){
    setBadge("err", "Offline");
    console.error("Health error:", e);
  }
}

// botão manual
hc.btn?.addEventListener("click", pingHealth);

// roda ao carregar
pingHealth();

// auto-poll a cada 30s (só quando aba está ativa)
setInterval(()=>{ if(document.hasFocus()) pingHealth(); }, 30000);

// ===== PATCH: cards dinâmicos + export por período =====
async function loadAll() {
  try {
    // dados brutos
    const [statsRaw, summary, history] = await Promise.all([
      getJSON(`${BASE_PIX}/stats`),
      getJSON(`${BASE_PIX}/summary`),
      getJSON(`${BASE_PIX}/history?limit=200`),
    ]);

    const period = els2.periodSel?.value || "all";
    const cut = cutoffFrom(period);
    // filtrar history pelo período
    const histFiltered = (history||[]).filter(tx=>{
      const t = new Date(tx.created_at);
      return !(cut && t < cut);
    });

    // recalcular stats no período
    const amounts = histFiltered.map(x=>Number(x.amount||0));
    const total_count = amounts.length;
    const total_amount = amounts.reduce((a,b)=>a+b,0);
    const avg_amount = total_count ? (total_amount/total_count) : 0;
    const last_tx = histFiltered.length ? histFiltered[0].created_at : "—";

    // preencher cards
    els.totalCount.textContent = total_count;
    els.totalAmount.textContent = brl(total_amount);
    els.avgAmount.textContent = brl(avg_amount);
    els.lastTx.textContent = last_tx;

    // gráfico de saldo líquido por conta (sempre total)
    drawChart(summary || []);

    // gráfico de volume diário filtrado
    const dailyPairs = buildDaily(history || [], period);
    drawVolumeChart(dailyPairs);

    // debug
    els.debug.textContent = JSON.stringify({ period, total_count, total_amount, avg_amount, last_tx, dailyPairs }, null, 2);
  } catch (err) {
    const msg = `Erro ao carregar dados: ${err.message}`;
    console.error(msg);
    els.debug.textContent = msg;
  }
}

// substitui exportCSV para respeitar período
async function exportCSV() {
  try {
    const period = els2.periodSel?.value || "all";
    const cut = cutoffFrom(period);
    const hist = await getJSON(`${BASE_PIX}/history?limit=200`);
    const histFiltered = (hist||[]).filter(tx=>{
      const t = new Date(tx.created_at);
      return !(cut && t < cut);
    });
    if(histFiltered.length === 0){
      alert("Sem dados para exportar nesse período.");
      return;
    }
    const headers = ["id","from_account_id","to_account_id","amount","created_at"];
    const rows = histFiltered.map(x => [
      x.id, x.from_account_id, x.to_account_id, x.amount, x.created_at
    ]);

    const toCSV = arr => arr.map(v=>{
      const s=(v===null||v===undefined)?"":String(v);
      return /[",\n]/.test(s)?`"${s.replace(/"/g,'""')}"`:s;
    }).join(",");
    const csv = [toCSV(headers), ...rows.map(toCSV)].join("\n");
    const blob = new Blob([csv],{type:"text/csv;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const ts=new Date().toISOString().replace(/[:.]/g,"-");
    a.href=url;
    a.download=`pix_history_${period}_${ts}.csv`;
    document.body.appendChild(a);a.click();a.remove();
    URL.revokeObjectURL(url);
  }catch(e){
    alert("Falha ao exportar CSV: "+e.message);
    console.error(e);
  }
}

// ===== PATCH: usar /pix/daily-summary no gráfico de volume =====
async function fetchDailySummary(period){
  const cut = cutoffFrom(period); // já existe
  let url = `${BASE_API}/pix/daily-summary`;
  if (cut){
    const y = cut.getUTCFullYear();
    const m = String(cut.getUTCMonth()+1).padStart(2,"0");
    const d = String(cut.getUTCDate()).padStart(2,"0");
    url += `?start=${y}-${m}-${d}`;
  }
  return getJSON(url);
}

function pairsFromDailySummary(daily){
  // daily = [{day_utc, total_amount, ...}]
  const byDay = (daily||[]).map(row => {
    const day = row.day_utc; // "YYYY-MM-DD"
    const val = Number(row.total_amount); // vem como string do Postgres
    return [day, val];
  }).sort((a,b)=> a[0].localeCompare(b[0]));
  return byDay;
}

// override de loadAll para usar daily-summary no volume
const _loadAll_prev_for_daily = loadAll;
loadAll = async function(){
  try{
    const [stats, summary] = await Promise.all([
      getJSON(`${BASE_PIX}/stats`),
      getJSON(`${BASE_PIX}/summary`),
    ]);

    // cards globais (mantém)
    els.totalCount.textContent = stats.total_count ?? "0";
    els.totalAmount.textContent = brl(stats.total_amount ?? 0);
    els.avgAmount.textContent = brl(stats.avg_amount ?? 0);
    els.lastTx.textContent = stats.last_tx ?? "—";

    // gráfico de saldo líquido por conta
    drawChart(summary || []);

    // novo: volume diário via MV
    const period = (els2?.periodSel?.value) || "all";
    const daily = await fetchDailySummary(period);
    const dailyPairs = pairsFromDailySummary(daily);
    drawVolumeChart(dailyPairs);

    // debug
    els.debug.textContent = JSON.stringify({ stats, summary, dailyPairs }, null, 2);
  }catch(err){
    const msg = `Erro ao carregar dados (daily-summary): ${err.message}`;
    console.error(msg);
    els.debug.textContent = msg;
  }
};

// === PATCH VISUAL: animação e estilo Nubank ===
function drawVolumeChart(dataPairs){
  const ctx = document.getElementById("volumeChart").getContext("2d");
  if (window.volumeChartInstance) {
    window.volumeChartInstance.destroy();
  }

  const labels = dataPairs.map(p => p[0]);
  const values = dataPairs.map(p => p[1]);

  window.volumeChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Volume diário (R$)",
        data: values,
        borderRadius: 6,
        backgroundColor: (ctx) => {
          const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 400);
          gradient.addColorStop(0, "#8A05BE");  // Nubank roxo
          gradient.addColorStop(1, "#C86DD7");
          return gradient;
        },
        borderWidth: 0,
      }],
    },
    options: {
      animation: {
        duration: 900,
        easing: "easeOutQuart"
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: (ctx) => `Total do dia: R$ ${ctx.formattedValue}`
          }
        },
        legend: { display: false }
      },
      scales: {
        y: {
          ticks: {
            color: "#CCC",
            callback: v => `R$ ${v.toFixed(2)}`
          },
          grid: { color: "#333" }
        },
        x: {
          ticks: { color: "#AAA" },
          grid: { display: false }
        }
      }
    }
  });
}

// === Dils Wallet Theme Helpers ===
function cssVar(name){ return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
const DILS = {
  primary: cssVar('--dils-primary') || '#007BFF',
  accent:  cssVar('--dils-accent')  || '#6A00F4',
  success: cssVar('--dils-success') || '#00FF99',
  warn:    cssVar('--dils-warn')    || '#FF6B00',
  text:    cssVar('--dils-text')    || '#E8EAF0'
};

// --- Reestiliza "Saldo Líquido por Conta" (vermelho/verde -> nossa paleta)
if (typeof drawChart === 'function') {
  const _drawChart = drawChart;
  drawChart = function(summary){
    // delega cálculo ao original, mas sobrepõe cores se existir Chart instance global
    try {
      _drawChart(summary);
      if (window.balanceChartInstance) {
        const ds = window.balanceChartInstance.data.datasets?.[0];
        if (ds){
          // negativo = laranja (warn), positivo = verde (success)
          ds.backgroundColor = (ctx)=> {
            const v = ds.data[ctx.dataIndex] || 0;
            const c = v < 0 ? DILS.warn : DILS.success;
            return c;
          };
          window.balanceChartInstance.update('none');
        }
      }
    } catch(e){ console.warn('drawChart override fallback:', e); _drawChart(summary); }
  }
}

// --- Reestiliza "Volume diário (R$)" com gradiente Dils
if (typeof drawVolumeChart === 'function') {
  const _drawVolumeChart = drawVolumeChart;
  drawVolumeChart = function(dataPairs){
    const el = document.getElementById('volumeChart');
    if (!el) return _drawVolumeChart(dataPairs);
    const ctx = el.getContext('2d');
    const grad = ctx.createLinearGradient(0,0,0,300);
    grad.addColorStop(0, DILS.accent);
    grad.addColorStop(1, DILS.primary);

    // cria gráfico com nossa estética
    if (window.volumeChartInstance) window.volumeChartInstance.destroy();
    const labels = dataPairs.map(p=>p[0]);
    const values = dataPairs.map(p=>p[1]);

    window.volumeChartInstance = new Chart(ctx, {
      type: "bar",
      data: { labels, datasets: [{ data: values, backgroundColor: grad, borderRadius: 7 }] },
      options: {
        animation: { duration: 900, easing: 'easeOutQuart' },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: s => `Total do dia: R$ ${s.formattedValue}` } }
        },
        scales: {
          y: { ticks: { color: DILS.text, callback: v => `R$ ${Number(v).toFixed(2)}` }, grid: { color: 'rgba(255,255,255,.07)' } },
          x: { ticks: { color: '#B5BCD0' }, grid: { display: false } }
        }
      }
    });
  }
}

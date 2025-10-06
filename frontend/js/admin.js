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

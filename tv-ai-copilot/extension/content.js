/**
 * content.js
 * Runs on every tradingview.com chart page.
 * - Reads the currently open symbol from the URL / page.
 * - Calls the local backend (http://127.0.0.1:8000/analyze).
 * - Renders a draggable overlay panel with all the analysis.
 *
 * NOTE: This panel only DISPLAYS information. It never places, modifies,
 * or cancels any trade. Decision stays with you.
 */

const BACKEND_URL = "http://127.0.0.1:8000";
const REFRESH_MS = 15000; // refresh every 15s

let currentInterval = "1h";
let panelEl = null;

function getSymbolFromPage() {
  // TradingView chart URLs look like:
  // https://www.tradingview.com/chart/XXXXXXXX/?symbol=BINANCE%3ABTCUSDT
  const params = new URLSearchParams(window.location.search);
  let symbol = params.get("symbol");
  if (symbol) {
    // strip exchange prefix like "BINANCE:"
    symbol = symbol.split(":").pop();
    return symbol;
  }
  // fallback: try reading the page title, e.g. "BTCUSDT chart — TradingView"
  const titleMatch = document.title.match(/([A-Z0-9]{4,15})/);
  return titleMatch ? titleMatch[1] : "BTCUSDT";
}

function buildPanel() {
  if (panelEl) return panelEl;

  panelEl = document.createElement("div");
  panelEl.id = "tv-ai-copilot-panel";
  panelEl.innerHTML = `
    <div id="tvac-header">
      <span>AI Copilot</span>
      <select id="tvac-interval">
        <option value="15m">15m</option>
        <option value="30m">30m</option>
        <option value="1h" selected>1h</option>
        <option value="4h">4h</option>
        <option value="1d">1D</option>
      </select>
      <button id="tvac-collapse">—</button>
    </div>
    <div id="tvac-body">
      <div class="tvac-loading">Loading...</div>
    </div>
  `;
  document.body.appendChild(panelEl);

  panelEl.querySelector("#tvac-interval").addEventListener("change", (e) => {
    currentInterval = e.target.value;
    refresh();
  });
  panelEl.querySelector("#tvac-collapse").addEventListener("click", () => {
    panelEl.classList.toggle("tvac-collapsed");
  });

  makeDraggable(panelEl, panelEl.querySelector("#tvac-header"));
  return panelEl;
}

function makeDraggable(el, handle) {
  let offsetX = 0, offsetY = 0, dragging = false;
  handle.addEventListener("mousedown", (e) => {
    dragging = true;
    offsetX = e.clientX - el.offsetLeft;
    offsetY = e.clientY - el.offsetTop;
  });
  document.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    el.style.left = (e.clientX - offsetX) + "px";
    el.style.top = (e.clientY - offsetY) + "px";
  });
  document.addEventListener("mouseup", () => (dragging = false));
}

function renderData(data) {
  const body = panelEl.querySelector("#tvac-body");

  const candlesHtml = data.recent_candles
    .slice(-10)
    .reverse()
    .map(c => `<li class="tvac-${c.direction}">${c.pattern} <span>(${c.direction})</span></li>`)
    .join("");

  const projHtml = data.projections
    .map(p => `<tr><td>${p.horizon_hours}h</td><td>${p.expected_price}</td><td>${p.range_low} – ${p.range_high}</td></tr>`)
    .join("");

  body.innerHTML = `
    <div class="tvac-row"><b>${data.symbol}</b> · ${data.interval} · Price: ${data.last_price}</div>
    <div class="tvac-row tvac-signal tvac-${data.signal.toLowerCase()}">
      Signal: ${data.signal} &nbsp; | &nbsp; Structure: ${data.structure}
    </div>
    <div class="tvac-row">
      Bullish: ${data.probability.bullish_pct}% &nbsp; Bearish: ${data.probability.bearish_pct}%
    </div>

    <div class="tvac-section">Indicators</div>
    <div class="tvac-grid">
      <div>RSI: ${data.indicators.rsi}</div>
      <div>ADX(32): ${data.indicators.adx.adx}</div>
      <div>MACD hist: ${data.indicators.macd.histogram}</div>
      <div>Stoch K/D: ${data.indicators.stochastic.k}/${data.indicators.stochastic.d}</div>
      <div>CMF: ${data.indicators.cmf}</div>
      <div>OBV: ${data.indicators.obv.trend}</div>
    </div>

    <div class="tvac-section">Fibonacci</div>
    <div class="tvac-grid">
      ${Object.entries(data.fibonacci).map(([k, v]) => `<div>${k}: ${v}</div>`).join("")}
    </div>

    <div class="tvac-section">Last 10 Candles</div>
    <ul class="tvac-candles">${candlesHtml}</ul>

    <div class="tvac-section">Projected Move (${data.signal})</div>
    <table class="tvac-table">
      <tr><th>Horizon</th><th>Expected</th><th>Range</th></tr>
      ${projHtml}
    </table>
    <div class="tvac-disclaimer">Informational only. Not financial advice — you decide every trade.</div>
  `;
}

async function refresh() {
  buildPanel();
  const symbol = getSymbolFromPage();
  const body = panelEl.querySelector("#tvac-body");
  try {
    const res = await fetch(`${BACKEND_URL}/analyze?symbol=${symbol}&interval=${currentInterval}`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderData(data);
  } catch (err) {
    body.innerHTML = `<div class="tvac-error">Backend error: ${err.message}<br>Is your local backend running on port 8000?</div>`;
  }
}

buildPanel();
refresh();
setInterval(refresh, REFRESH_MS);

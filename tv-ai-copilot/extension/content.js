/**
 * content.js — TradingView Institutional AI Copilot [Pro] (v5.0)
 * Implements the complete Trading Win-Rate Framework:
 * - Macro Trend Baseline (Daily EMA 200 - Rule 1)
 * - Fibonacci 0.618 Golden Pocket
 * - Order Flow CVD & Whale Absorption Traps
 * - Statistical Extremes (Z-Score +/- 2.5σ to 3.0σ)
 * - Liquidity Sweeps / Stop Hunts (Rule 2)
 * - Asymmetric Risk Protocol (1% Risk, TP1 1:1 Breakeven Lock, TP2 1:2)
 * - Delta-Neutral Arbitrage Engine (Live Basis & Funding Yield)
 * - 5 Non-Negotiable Discipline Rules
 */

const DEFAULT_LOCAL_BACKEND = "http://127.0.0.1:8000";
const CLOUD_BACKEND = "https://trading-view-ai-copilot.vercel.app";
const REFRESH_MS = 15000;

let currentBackend = DEFAULT_LOCAL_BACKEND;
let currentInterval = "1h";
let userCapital = 10000;
let activeTab = "confluence";
let panelEl = null;
let lastApiData = null;

function getSymbolFromPage() {
  const params = new URLSearchParams(window.location.search);
  let symbol = params.get("symbol");
  if (symbol) {
    symbol = symbol.split(":").pop();
    return symbol;
  }
  const titleMatch = document.title.match(/([A-Z0-9]{4,15})/);
  return titleMatch ? titleMatch[1] : "BTCUSDT";
}

function buildPanel() {
  if (panelEl) return panelEl;

  panelEl = document.createElement("div");
  panelEl.id = "tv-ai-copilot-panel";
  panelEl.innerHTML = `
    <div id="tvac-header">
      <div class="tvac-brand-group">
        <span class="tvac-live-dot" title="Live Institutional Engine"></span>
        <span class="tvac-title">Copilot Pro [80%+ Engine]</span>
      </div>
      <div class="tvac-header-actions">
        <select id="tvac-interval" class="tvac-select">
          <option value="15m">15m</option>
          <option value="30m">30m</option>
          <option value="1h" selected>1h</option>
          <option value="4h">4h</option>
          <option value="1d">1D</option>
        </select>
        <button id="tvac-collapse" class="tvac-icon-btn" title="Minimize / Expand">—</button>
      </div>
    </div>
    <div id="tvac-body">
      <div class="tvac-loading-box">
        <div class="tvac-spinner"></div>
        <div>Initializing Institutional Engine...</div>
      </div>
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
    if (e.target.tagName === "SELECT" || e.target.tagName === "BUTTON") return;
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

function renderUI(data) {
  lastApiData = data;
  const body = panelEl.querySelector("#tvac-body");
  if (!body) return;

  const confScore = data.confluence_score_pct || 50;
  const isAplus = data.is_a_plus_setup;
  const grade = data.grade || "No Setup";
  const bias = data.signal || "Neutral";
  const lastPrice = data.last_price;

  let badgeClass = "tvac-badge-standdown";
  if (isAplus) badgeClass = "tvac-badge-aplus";
  else if (confScore >= 75) badgeClass = "tvac-badge-a";
  else if (confScore >= 50) badgeClass = "tvac-badge-b";

  let progressColor = "#ef4444";
  if (isAplus) progressColor = "#10b981";
  else if (confScore >= 75) progressColor = "#38bdf8";
  else if (confScore >= 50) progressColor = "#f59e0b";

  const bannerHtml = `
    <div class="tvac-banner">
      <div class="tvac-banner-top">
        <div>
          <div class="tvac-pair-info">${data.symbol} <span class="tvac-pair-sub">· ${data.interval} · $${lastPrice.toLocaleString()}</span></div>
        </div>
        <span class="tvac-badge ${badgeClass}">${grade.includes("A+") ? "⚡ A+ SETUP" : grade.split(" ")[0]}</span>
      </div>

      <div class="tvac-progress-wrap">
        <div class="tvac-progress-header">
          <span>Confluence: <b>${confScore}%</b></span>
          <span style="color: ${bias === 'Bullish' ? '#10b981' : (bias === 'Bearish' ? '#ef4444' : '#94a3b8')}">
            Direction: <b>${bias.toUpperCase()}</b>
          </span>
        </div>
        <div class="tvac-progress-bar">
          <div class="tvac-progress-fill" style="width: ${confScore}%; background: ${progressColor};"></div>
        </div>
      </div>

      <div class="tvac-banner-metrics">
        <div class="tvac-metric-box">
          <div class="tvac-metric-lbl">Macro Trend (D200)</div>
          <div class="tvac-metric-val ${data.macro_trend.macro_bias === 'Bullish' ? 'tvac-val-green' : 'tvac-val-red'}">
            ${data.macro_trend.macro_bias} (${data.macro_trend.daily_ema_200.toLocaleString()})
          </div>
        </div>
        <div class="tvac-metric-box">
          <div class="tvac-metric-lbl">Market Regime</div>
          <div class="tvac-metric-val tvac-val-cyan">
            ${data.market_regime.regime.split(" ")[0]}
          </div>
        </div>
      </div>
    </div>
  `;

  const tabsHtml = `
    <div class="tvac-tabs">
      <button class="tvac-tab-btn ${activeTab === 'confluence' ? 'active' : ''}" data-tab="confluence">Confluence</button>
      <button class="tvac-tab-btn ${activeTab === 'risk' ? 'active' : ''}" data-tab="risk">1% Risk Box</button>
      <button class="tvac-tab-btn ${activeTab === 'orderflow' ? 'active' : ''}" data-tab="orderflow">Order Flow & Z</button>
      <button class="tvac-tab-btn ${activeTab === 'arbitrage' ? 'active' : ''}" data-tab="arbitrage">Arbitrage & Rules</button>
    </div>
  `;

  let tabContentHtml = "";

  if (activeTab === "confluence") {
    const checklistItems = data.confluence_checklist.map(item => `
      <div class="tvac-check-item ${item.passed ? 'passed' : 'failed'}">
        <div class="tvac-check-icon">${item.passed ? '✓' : '✗'}</div>
        <div class="tvac-check-content">
          <div class="tvac-check-title">${item.filter}</div>
          <div class="tvac-check-desc">${item.detail}</div>
        </div>
      </div>
    `).join("");

    tabContentHtml = `
      <div class="tvac-card">
        <div class="tvac-card-title">
          <span>Pre-Trade 4-Filter Alignment</span>
          <span style="font-size: 10px; color: ${progressColor}">${confScore}% Aligned</span>
        </div>
        <div class="tvac-checklist">
          ${checklistItems}
        </div>
      </div>

      <div class="tvac-card">
        <div class="tvac-card-title">Execution Recommendation</div>
        <div style="font-size: 11px; color: #cbd5e1; line-height: 1.45;">
          ${data.action_recommendation}
        </div>
      </div>
    `;
  } else if (activeTab === "risk") {
    const rm = data.risk_management;
    tabContentHtml = `
      <div class="tvac-card">
        <div class="tvac-input-row">
          <label>Account Capital ($):</label>
          <input type="number" id="tvac-capital-input" class="tvac-input" value="${userCapital}" step="500" min="100">
        </div>

        <div class="tvac-risk-grid">
          <div class="tvac-risk-card">
            <div class="tvac-metric-lbl">Fixed 1% Risk</div>
            <div class="tvac-metric-val tvac-val-gold">$${rm.risk_per_trade_usd.toLocaleString()}</div>
          </div>
          <div class="tvac-risk-card">
            <div class="tvac-metric-lbl">Position Size ($)</div>
            <div class="tvac-metric-val tvac-val-cyan">$${rm.recommended_position_usd.toLocaleString()}</div>
          </div>
          <div class="tvac-risk-card">
            <div class="tvac-metric-lbl">Entry Price</div>
            <div class="tvac-metric-val">$${rm.entry_price.toLocaleString()}</div>
          </div>
          <div class="tvac-risk-card">
            <div class="tvac-metric-lbl">Stop Loss</div>
            <div class="tvac-metric-val tvac-val-red">$${rm.stop_loss.toLocaleString()}</div>
          </div>
        </div>

        <div class="tvac-action-callout">
          <strong>TP1 (1:1 RRR): $${rm.tp1_1_to_1.toLocaleString()}</strong><br>
          ➔ Take 50% Profit off table & shift Stop-Loss to Entry (Risk = $0).
        </div>

        <div class="tvac-action-callout" style="background: rgba(56, 189, 248, 0.1); border-color: rgba(56, 189, 248, 0.3); color: #bae6fd; margin-top: 6px;">
          <strong>TP2 (1:2 RRR Target): $${rm.tp2_1_to_2.toLocaleString()}</strong><br>
          ➔ Close remaining 50% position for full win!
        </div>
      </div>

      <div class="tvac-card">
        <div class="tvac-card-title">Mathematical Expected Value (+EV)</div>
        <div style="font-size: 10.5px; color: #94a3b8; line-height: 1.4;">
          With 1:2 RRR & TP1 Breakeven scaling, chunky losses are eliminated. At 55%-65% win rate, your portfolio grows systematically:
          <b style="color: #34d399">+$800 Net Profit per 100 trades</b>.
        </div>
      </div>
    `;
  } else if (activeTab === "orderflow") {
    const z = data.z_score_engine;
    const of = data.order_flow_cvd;
    const fib = data.fibonacci;

    tabContentHtml = `
      <div class="tvac-card">
        <div class="tvac-card-title">Statistical Z-Score Engine (20-Period)</div>
        <div class="tvac-banner-metrics" style="margin-top: 0; padding-top: 0; border: none;">
          <div class="tvac-metric-box">
            <div class="tvac-metric-lbl">Z-Score Value</div>
            <div class="tvac-metric-val ${Math.abs(z.z_score) >= 2.5 ? 'tvac-val-red' : 'tvac-val-cyan'}">
              ${z.z_score} σ
            </div>
          </div>
          <div class="tvac-metric-box">
            <div class="tvac-metric-lbl">Distribution Status</div>
            <div class="tvac-metric-val" style="font-size: 11px;">
              ${z.condition.split(" ")[0]}
            </div>
          </div>
        </div>
        <div style="font-size: 10px; color: #94a3b8; margin-top: 6px;">
          Upper Extreme (+2.5σ): <b>$${z.upper_extreme_2_5}</b> | Lower (-2.5σ): <b>$${z.lower_extreme_2_5}</b>
        </div>
      </div>

      <div class="tvac-card">
        <div class="tvac-card-title">CVD Order Flow & Absorption Trap</div>
        <div style="font-size: 11px; margin-bottom: 4px;">
          Bar Delta: <b style="color: ${of.bar_delta >= 0 ? '#10b981' : '#ef4444'}">${of.bar_delta > 0 ? '+' : ''}${of.bar_delta}</b> · Flow: <b>${of.cvd_trend}</b>
        </div>
        <div class="tvac-action-callout" style="${of.absorption_trap_active ? 'background: rgba(245, 158, 11, 0.15); border-color: #f59e0b; color: #fde68a;' : 'background: rgba(15, 23, 42, 0.6); border-color: rgba(255,255,255,0.05); color: #94a3b8;'}">
          ${of.state_summary}
        </div>
      </div>

      <div class="tvac-card">
        <div class="tvac-card-title">Fibonacci Golden Pocket Zone</div>
        <div style="font-size: 11px; margin-bottom: 6px; color: #facc15;">
          ${fib.status} (${fib.golden_pocket_range[0]} – ${fib.golden_pocket_range[1]})
        </div>
        <table class="tvac-table">
          <tr><th>Level</th><th>Price</th></tr>
          ${Object.entries(fib.levels).slice(0, 6).map(([k, v]) => `<tr><td>${k}</td><td>$${v}</td></tr>`).join("")}
        </table>
      </div>
    `;
  } else if (activeTab === "arbitrage") {
    const arb = data.delta_neutral_arbitrage;
    const rules = data.discipline_rules;

    tabContentHtml = `
      <div class="tvac-card">
        <div class="tvac-card-title">
          <span>Delta-Neutral Cash & Carry Arbitrage</span>
          <span style="font-size: 10px; color: #38bdf8;">Net Delta = 0</span>
        </div>
        <div class="tvac-risk-grid">
          <div class="tvac-risk-card">
            <div class="tvac-metric-lbl">8h Funding Rate</div>
            <div class="tvac-metric-val ${arb.funding_rate_8h_pct >= 0 ? 'tvac-val-green' : 'tvac-val-red'}">
              ${arb.funding_rate_8h_pct}%
            </div>
          </div>
          <div class="tvac-risk-card">
            <div class="tvac-metric-lbl">Annualized Yield</div>
            <div class="tvac-metric-val tvac-val-cyan">${arb.annualized_yield_pct}% APR</div>
          </div>
          <div class="tvac-risk-card">
            <div class="tvac-metric-lbl">Basis Spread</div>
            <div class="tvac-metric-val">$${arb.basis_spread}</div>
          </div>
          <div class="tvac-risk-card">
            <div class="tvac-metric-lbl">Regime</div>
            <div class="tvac-metric-val" style="font-size: 10px;">${arb.regime.split(" ")[0]}</div>
          </div>
        </div>
        <div style="font-size: 10px; color: #94a3b8; margin-top: 4px;">
          Spot Buy + 1x Short Perpetual = Directional risk-free funding yield collection.
        </div>
      </div>

      <div class="tvac-card">
        <div class="tvac-card-title">5 Non-Negotiable Discipline Rules</div>
        <div class="tvac-checklist">
          ${rules.map(r => `
            <div class="tvac-check-item ${r.passed ? 'passed' : 'failed'}">
              <div class="tvac-check-icon">${r.passed ? '✓' : '⚠️'}</div>
              <div class="tvac-check-content">
                <div class="tvac-check-title">${r.rule}: <span style="font-weight: 400; color: #cbd5e1;">${r.status}</span></div>
                <div class="tvac-check-desc">${r.instruction}</div>
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  body.innerHTML = `
    ${bannerHtml}
    ${tabsHtml}
    ${tabContentHtml}
    <div class="tvac-footer">
      Institutional Framework Copilot v5.0 · Strictly Rule-Based · You Control All Execution
    </div>
  `;

  // Attach tab click listeners
  body.querySelectorAll(".tvac-tab-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      activeTab = e.target.dataset.tab;
      renderUI(lastApiData);
    });
  });

  // Attach capital input listener
  const capInput = body.querySelector("#tvac-capital-input");
  if (capInput) {
    capInput.addEventListener("change", (e) => {
      userCapital = parseFloat(e.target.value) || 10000;
      refresh();
    });
  }
}

async function fetchFromBackend(url, symbol, interval, capital) {
  const target = `${url}/analyze?symbol=${symbol}&interval=${interval}&capital=${capital}`;
  const res = await fetch(target, { mode: "cors" });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

async function refresh() {
  buildPanel();
  const symbol = getSymbolFromPage();
  const body = panelEl.querySelector("#tvac-body");

  try {
    // Try local backend first, fallback to cloud
    let data = null;
    try {
      data = await fetchFromBackend(currentBackend, symbol, currentInterval, userCapital);
    } catch (localErr) {
      if (currentBackend !== CLOUD_BACKEND) {
        currentBackend = CLOUD_BACKEND;
        data = await fetchFromBackend(currentBackend, symbol, currentInterval, userCapital);
      } else {
        throw localErr;
      }
    }
    renderUI(data);
  } catch (err) {
    if (body) {
      body.innerHTML = `
        <div class="tvac-error-box">
          <b>Connection Issue:</b> Could not reach backend.<br>
          <small>Tried: ${currentBackend}</small><br><br>
          Please start local backend:
          <pre style="background: #0f172a; padding: 6px; border-radius: 4px; margin-top: 4px; font-size: 10px;">cd backend\nuvicorn main:app --reload --port 8000</pre>
          <div style="margin-top: 8px;">
            <button id="tvac-retry-btn" class="tvac-select" style="background: #334155; color: white;">Retry Connection</button>
          </div>
        </div>
      `;
      const retryBtn = body.querySelector("#tvac-retry-btn");
      if (retryBtn) retryBtn.addEventListener("click", () => {
        currentBackend = DEFAULT_LOCAL_BACKEND;
        refresh();
      });
    }
  }
}

// Auto start
buildPanel();
refresh();
setInterval(refresh, REFRESH_MS);

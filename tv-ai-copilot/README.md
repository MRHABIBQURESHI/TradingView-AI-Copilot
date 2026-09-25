# 🏛️ TradingView Institutional Win-Rate Framework [Pro] (v5.0)

A comprehensive, institutional-grade trading system and indicator suite based on the **Delta-Neutral Arbitrage & Institutional Directional Strategy (80%–85% Framework)**.

---

## 📦 What's Included

This repository provides **two integrated ways** to use the system:

1. **Native TradingView Pine Script v5 Indicator** (`Institutional_WinRate_Framework_Pro.pine`)  
   Can be pasted directly into TradingView's Pine Editor to plot all institutional levels, signals, zones, risk execution boxes, and on-chart HUD dashboard directly on your charts.
2. **AI Copilot Chrome Extension + Python FastAPI Backend** (`extension/` + `backend/`)  
   A glassmorphic overlay for TradingView charts providing live order-flow CVD delta, statistical Z-score meters, live 8-hour funding rate arbitrage calculations, and dynamic 1% risk position sizing.

---

## 🎯 Core Framework Implementation (From Document)

### 1. Macro Trend Baseline Filter (Rule 1)
- **Formula:** $P_t > EMA_{200}$ (Daily Timeframe)
- **Discipline Rule:** *"Never Short an Uptrend / Long a Downtrend"*. Long trades are allowed only when price is above the Daily 200 EMA; short trades only when price is below it.

### 2. Fibonacci Golden Pocket (0.618 - 0.650 OTE Zone)
- **Formula:** $P = \text{High} - [(\text{High} - \text{Low}) \times 0.618]$
- Detects swing highs/lows and automatically identifies when price pulls back into the mathematical golden pocket reversal zone.

### 3. Order Flow Imbalance & CVD Absorption Traps
- **Formula:** $CVD_{\text{reversal}} \neq \Delta P$
- Monitors Cumulative Volume Delta and bar deltas. When aggressive market orders hit key levels but price cannot advance, the system flags **Whale Limit Absorption Traps** for high-probability reversals.

### 4. Statistical Extremes (Z-Score Mean Reversion)
- **Formula:** $Z = (P_t - \mu_{20}) / \sigma_{20}$
- Calculates standard deviation boundaries:
  - $\pm 2.5\sigma$: Statistical Extreme ($\approx 98.7\%$ probability boundary)
  - $\pm 3.0\sigma$: Fat-Tail / Aggressive Institutional Mean Reversion ($\approx 99.7\%$ boundary)

### 5. Liquidity Sweeps & Stop Hunts (Rule 2)
- **Discipline Rule:** *"Never Enter Without a Stop Hunt"*.
- Identifies wick sweeps above swing highs (Buy-Side Liquidity - BSL) or below swing lows (Sell-Side Liquidity - SSL) with $>40\%$ wick rejection.

### 6. Asymmetric Risk Scaling Protocol (How 80%+ Is Locked)
- **Strict 1% Position Sizing:**
  $$\text{Position Size} = \frac{\text{Account Capital} \times 0.01}{|\text{Entry} - \text{Stop-Loss}| / \text{Entry}}$$
- **TP1 at 1:1 RRR (Close 50% Position):** The moment price hits 1:1 RRR, 50% profit is taken and the Stop-Loss is shifted to Entry (**Breakeven Step** — Remaining Risk = $0$).
- **TP2 at 1:2 RRR (Remaining 50% Position):** Captures full asymmetric reward.
- **Result:** Chunky losing trades are eliminated at the execution level, achieving an 80%–85% win + scratch rate.

### 7. Delta-Neutral Cash & Carry Arbitrage Engine
- **Spot + 1x Short Perpetual Futures** ($\Delta_{\text{total}} = 0$).
- Live 8-hour funding rate tracker and annualized yield calculation ($12\% - 35\%$ typical APR).
- Basis spread tracking ($\text{Basis} = \text{Futures Price} - \text{Spot Price}$) and inverted negative funding warning.

### 8. 5 Non-Negotiable Discipline Rules Checklist
1. Never Short an Uptrend / Long a Downtrend (Daily EMA 200).
2. Never Enter Without a Stop Hunt (Wick Rejection).
3. No Setup, No Trade (Confluence $\ge 75\%$).
4. Fixed Sizing (Strict 1% Risk).
5. Move to Breakeven at TP1.

---

## 🚀 How to Use the TradingView Pine Script Indicator

1. Open [TradingView.com](https://www.tradingview.com) and open any chart (e.g. BTCUSDT, ETHUSDT).
2. Click **Pine Editor** at the bottom of the screen.
3. Click **Open** ➔ **New indicator**.
4. Copy the entire code from [`Institutional_WinRate_Framework_Pro.pine`](file:///e:/Project/reports/refunds/TradingView-AI-Copilot-main/tv-ai-copilot/Institutional_WinRate_Framework_Pro.pine).
5. Paste it into the Pine Editor and click **Add to Chart**.
6. The indicator will plot:
   - Macro Daily 200 EMA cloud
   - Golden Pocket zones
   - Statistical $\pm 2.5\sigma$ and $\pm 3.0\sigma$ Z-score bands
   - Stop Hunt / Liquidity Sweep marks (`⚡SSL SWEEP`, `⚡BSL SWEEP`)
   - **`A+ BUY`** and **`A+ SELL`** confluence signals
   - An on-chart **Institutional HUD Table** displaying live metrics, confluence score, and 1% risk position sizing.

---

## 💻 How to Run the Python Backend & Chrome Extension

### Step 1: Start Backend (Local PC)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

To test: open `http://127.0.0.1:8000/analyze?symbol=BTCUSDT&interval=1h&capital=10000` in your browser.

### Step 2: Load Chrome Extension

1. Open Google Chrome and navigate to: `chrome://extensions`
2. Enable **Developer mode** (toggle in the top-right corner).
3. Click **Load unpacked**.
4. Select the [`extension/`](file:///e:/Project/reports/refunds/TradingView-AI-Copilot-main/tv-ai-copilot/extension/) folder.
5. Open any TradingView chart — the **Copilot Pro HUD Panel** will appear in the top-right corner.

---

## 🛡️ Risk Disclaimer

*This software and framework are for educational, research, and informational purposes only. Trading financial assets and cryptocurrencies involves significant risk of loss. Always trade responsibly with proper risk management.*

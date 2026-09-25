"""
main.py
TradingView Institutional AI Copilot Backend (80%-85% Precision System)
Run with: uvicorn main:app --reload --port 8000

Endpoint:
  GET /analyze?symbol=BTCUSDT&interval=1h&capital=10000
"""

import numpy as np
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data import fetch_klines, fetch_macro_daily, fetch_funding_and_basis
from indicators import (
    compute_indicators,
    compute_zscore,
    compute_cvd_and_absorption,
    detect_liquidity_sweeps,
    compute_fibonacci,
    calculate_risk_management,
    recent_candles
)
from structure import (
    detect_macro_trend,
    detect_market_regime,
    detect_structure,
    composite_score,
    evaluate_institutional_confluence,
    evaluate_discipline_rules,
    project_moves
)

app = FastAPI(title="TradingView Institutional Copilot Backend")


def _sanitize(obj):
    """Recursively convert numpy scalar types to plain Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/analyze")
def analyze(
    symbol: str = Query(..., examples=["BTCUSDT"]),
    interval: str = Query("1h", examples=["1h"]),
    capital: float = Query(10000.0, description="Account capital in USD for 1% risk sizing")
):
    try:
        df = fetch_klines(symbol=symbol, interval=interval, limit=300)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch candle data: {e}")

    last_price = round(float(df["close"].iloc[-1]), 4)

    # 1. Macro Trend (Daily EMA 200)
    try:
        daily_df = fetch_macro_daily(symbol=symbol, limit=250)
    except Exception:
        daily_df = None
    macro = detect_macro_trend(daily_df, last_price)

    # 2. Institutional Indicators & Order Flow
    ind = compute_indicators(df, adx_period=32)
    zscore = compute_zscore(df, period=20, extreme_thresh=2.5, fat_tail_thresh=3.0)
    cvd = compute_cvd_and_absorption(df)
    sweeps = detect_liquidity_sweeps(df, lookback=20)
    fib = compute_fibonacci(df, lookback=100)
    regime = detect_market_regime(df)
    candles = recent_candles(df, count=15)
    structure = detect_structure(df)

    # 3. Pre-Trade 4-Filter Confluence Evaluation
    confluence = evaluate_institutional_confluence(
        macro=macro,
        fibo=fib,
        zscore=zscore,
        cvd=cvd,
        sweep=sweeps,
        current_price=last_price,
        structure=structure["structure"]
    )

    # 4. Asymmetric Risk Management Protocol (1% Risk, TP1 1:1 Breakeven, TP2 1:2)
    risk_mgmt = calculate_risk_management(
        capital=capital,
        last_price=last_price,
        bias=confluence["bias"],
        stop_hunt=sweeps,
        z_score=zscore
    )

    # 5. Non-Negotiable Discipline Rules
    rules = evaluate_discipline_rules(confluence, risk_mgmt)

    # 6. Delta-Neutral Arbitrage Engine (Live Basis & Funding Yield)
    arbitrage = fetch_funding_and_basis(symbol)

    # Legacy compatibility fields
    scores = composite_score(ind, structure["structure"])
    projections = project_moves(df, confluence["bias"], scores["bullish_pct"])

    result = {
        "symbol": symbol.upper(),
        "interval": interval,
        "last_price": last_price,
        "structure": structure["structure"],
        "market_regime": regime,
        "macro_trend": macro,
        "signal": confluence["bias"],
        "grade": confluence["grade"],
        "is_a_plus_setup": confluence["is_a_plus_setup"],
        "confluence_score_pct": confluence["confluence_score_pct"],
        "action_recommendation": confluence["action_recommendation"],
        "probability": {
            "bullish_pct": scores["bullish_pct"],
            "bearish_pct": scores["bearish_pct"],
        },
        "z_score_engine": zscore,
        "order_flow_cvd": cvd,
        "liquidity_sweeps": sweeps,
        "fibonacci": fib,
        "risk_management": risk_mgmt,
        "discipline_rules": rules,
        "delta_neutral_arbitrage": arbitrage,
        "confluence_checklist": confluence["checklist"],
        "indicators": ind,
        "recent_candles": candles,
        "projections": projections,
    }
    return _sanitize(result)


@app.get("/")
def health():
    return {
        "status": "ok",
        "system": "TradingView Institutional Win-Rate Framework Copilot",
        "version": "5.0 Pro",
        "usage": "/analyze?symbol=BTCUSDT&interval=1h&capital=10000"
    }

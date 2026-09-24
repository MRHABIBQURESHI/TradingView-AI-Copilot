"""
main.py
Run with:  uvicorn main:app --reload --port 8000

Endpoint:
  GET /analyze?symbol=BTCUSDT&interval=1h
"""

import numpy as np
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data import fetch_klines
from indicators import compute_indicators, compute_fibonacci, recent_candles
from structure import detect_structure, composite_score, project_moves

app = FastAPI(title="TradingView AI Copilot Backend")


def _sanitize(obj):
    """Recursively convert numpy scalar types to plain Python types so JSON encoding never fails."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    return obj

# Allow the Chrome extension / TradingView to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/analyze")
def analyze(symbol: str = Query(..., examples=["BTCUSDT"]),
            interval: str = Query("1h", examples=["1h"])):
    try:
        df = fetch_klines(symbol=symbol, interval=interval, limit=300)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch data: {e}")

    ind = compute_indicators(df, adx_period=32)
    fib = compute_fibonacci(df)
    candles = recent_candles(df, count=15)
    structure = detect_structure(df)
    scores = composite_score(ind, structure["structure"])
    projections = project_moves(df, scores["bias"], scores["bullish_pct"])

    result = {
        "symbol": symbol.upper(),
        "interval": interval,
        "last_price": round(float(df["close"].iloc[-1]), 4),
        "structure": structure["structure"],
        "signal": scores["bias"],
        "probability": {
            "bullish_pct": scores["bullish_pct"],
            "bearish_pct": scores["bearish_pct"],
        },
        "indicators": ind,
        "fibonacci": fib,
        "recent_candles": candles,
        "projections": projections,
    }
    return _sanitize(result)


@app.get("/")
def health():
    return {"status": "ok", "usage": "/analyze?symbol=BTCUSDT&interval=1h"}

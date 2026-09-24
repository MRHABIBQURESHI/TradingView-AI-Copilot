"""
structure.py
- Detects market structure (uptrend / downtrend / range)
- Builds a rule-based composite score -> bullish/bearish "confidence"
- Projects a simple price range for future time horizons

IMPORTANT: The "confidence %" and "expected move" here are NOT machine-learned
predictions. They are a transparent, rule-based composite of the indicators
above (weighted scoring), plus an ATR-based volatility projection. This is
meant to be a decision-support signal, not a guarantee of where price goes.
Treat it exactly as you said you would: one input among several, not an
auto-trade instruction.
"""

import numpy as np
import pandas as pd
from ta.volatility import AverageTrueRange


def detect_structure(df: pd.DataFrame, swing_window: int = 5) -> dict:
    """Basic higher-high/higher-low vs lower-high/lower-low structure check."""
    highs = df["high"]
    lows = df["low"]

    # find local swing highs/lows over a rolling window
    swing_highs = highs[(highs.shift(swing_window) < highs) & (highs.shift(-swing_window) < highs)]
    swing_lows = lows[(lows.shift(swing_window) > lows) & (lows.shift(-swing_window) > lows)]

    swing_highs = swing_highs.dropna().tail(3)
    swing_lows = swing_lows.dropna().tail(3)

    trend = "range"
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        hh = swing_highs.iloc[-1] > swing_highs.iloc[-2]
        hl = swing_lows.iloc[-1] > swing_lows.iloc[-2]
        lh = swing_highs.iloc[-1] < swing_highs.iloc[-2]
        ll = swing_lows.iloc[-1] < swing_lows.iloc[-2]
        if hh and hl:
            trend = "uptrend"
        elif lh and ll:
            trend = "downtrend"

    return {"structure": trend}


def composite_score(ind: dict, structure: str) -> dict:
    """
    Combine indicators into a 0-100 bullish score (and its mirror bearish score).
    Simple transparent weighting -- easy for you to retune later.
    """
    score = 50.0  # neutral baseline

    # RSI: >50 bullish tilt, <50 bearish tilt
    score += (ind["rsi"] - 50) * 0.4

    # MACD histogram sign/magnitude
    score += np.clip(ind["macd"]["histogram"] * 5, -10, 10)

    # ADX: only trust direction if trend strength (ADX) is meaningful
    if ind["adx"]["adx"] > 20:
        if ind["adx"]["plus_di"] > ind["adx"]["minus_di"]:
            score += 8
        else:
            score -= 8

    # Stochastic
    score += (ind["stochastic"]["k"] - 50) * 0.15

    # CMF / OBV
    score += np.clip(ind["cmf"] * 40, -8, 8)
    score += 5 if ind["obv"]["trend"] == "rising" else -5

    # Structure bias
    if structure == "uptrend":
        score += 10
    elif structure == "downtrend":
        score -= 10

    score = float(np.clip(score, 1, 99))
    return {
        "bullish_pct": round(score, 1),
        "bearish_pct": round(100 - score, 1),
        "bias": "Bullish" if score > 55 else ("Bearish" if score < 45 else "Neutral / Wait"),
    }


HORIZONS_HOURS = [1, 2, 3, 6, 12, 24, 48]


def project_moves(df: pd.DataFrame, bias: str, bullish_pct: float) -> list:
    """
    ATR-based projected range per time horizon. This is a volatility-scaled
    extrapolation, NOT a certainty -- wider horizons = wider, less reliable range.
    """
    atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14).average_true_range().iloc[-1]
    last_price = df["close"].iloc[-1]

    # crude bars-per-hour guess based on candle spacing in the df
    time_diffs = df["open_time"].diff().dropna()
    minutes_per_candle = time_diffs.dt.total_seconds().median() / 60 if len(time_diffs) else 60
    bars_per_hour = max(60 / minutes_per_candle, 1 / 24)

    direction = 1 if bias == "Bullish" else (-1 if bias == "Bearish" else 0)
    strength = abs(bullish_pct - 50) / 50  # 0..1

    projections = []
    for h in HORIZONS_HOURS:
        bars = bars_per_hour * h
        move = atr * np.sqrt(bars) * 0.5  # volatility scaling, dampened
        center = last_price + direction * move * strength
        low_b = center - move
        high_b = center + move
        projections.append({
            "horizon_hours": h,
            "expected_price": round(center, 4),
            "range_low": round(low_b, 4),
            "range_high": round(high_b, 4),
        })
    return projections

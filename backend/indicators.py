"""
indicators.py
Calculates all the technical indicators requested:
MACD, ADX, RSI, Stochastic, CMF, OBV, Fibonacci levels.
"""

import pandas as pd
from ta.trend import MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volume import ChaikinMoneyFlowIndicator, OnBalanceVolumeIndicator


def compute_indicators(df: pd.DataFrame, adx_period: int = 32) -> dict:
    close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]

    macd_ind = MACD(close=close)
    macd_line = macd_ind.macd().iloc[-1]
    macd_signal = macd_ind.macd_signal().iloc[-1]
    macd_hist = macd_ind.macd_diff().iloc[-1]

    rsi = RSIIndicator(close=close, window=14).rsi().iloc[-1]

    adx_ind = ADXIndicator(high=high, low=low, close=close, window=adx_period)
    adx = adx_ind.adx().iloc[-1]
    adx_pos = adx_ind.adx_pos().iloc[-1]
    adx_neg = adx_ind.adx_neg().iloc[-1]

    stoch_ind = StochasticOscillator(high=high, low=low, close=close, window=14, smooth_window=3)
    stoch_k = stoch_ind.stoch().iloc[-1]
    stoch_d = stoch_ind.stoch_signal().iloc[-1]

    cmf = ChaikinMoneyFlowIndicator(high=high, low=low, close=close, volume=volume, window=20).chaikin_money_flow().iloc[-1]

    obv_series = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
    obv = obv_series.iloc[-1]
    obv_slope = obv_series.iloc[-1] - obv_series.iloc[-10] if len(obv_series) > 10 else 0

    return {
        "macd": {"macd": round(macd_line, 4), "signal": round(macd_signal, 4), "histogram": round(macd_hist, 4)},
        "rsi": round(rsi, 2),
        "adx": {"adx": round(adx, 2), "plus_di": round(adx_pos, 2), "minus_di": round(adx_neg, 2)},
        "stochastic": {"k": round(stoch_k, 2), "d": round(stoch_d, 2)},
        "cmf": round(cmf, 4),
        "obv": {"value": round(obv, 2), "trend": "rising" if obv_slope > 0 else "falling"},
    }


def compute_fibonacci(df: pd.DataFrame, lookback: int = 100) -> dict:
    """Fibonacci retracement levels based on the recent swing high/low."""
    recent = df.tail(lookback)
    swing_high = recent["high"].max()
    swing_low = recent["low"].min()
    diff = swing_high - swing_low

    levels = {
        "0.0": swing_high,
        "0.236": swing_high - 0.236 * diff,
        "0.382": swing_high - 0.382 * diff,
        "0.5": swing_high - 0.5 * diff,
        "0.618": swing_high - 0.618 * diff,
        "0.786": swing_high - 0.786 * diff,
        "1.0": swing_low,
    }
    return {k: round(v, 4) for k, v in levels.items()}


CANDLE_NAMES = {
    "doji": "Doji",
    "bull_engulf": "Bullish Engulfing",
    "bear_engulf": "Bearish Engulfing",
    "hammer": "Hammer",
    "shooting_star": "Shooting Star",
    "bull_marubozu": "Bullish Marubozu",
    "bear_marubozu": "Bearish Marubozu",
    "spinning_top": "Spinning Top",
    "normal": "Normal Candle",
}


def _classify_candle(o, h, l, c, prev_o=None, prev_c=None):
    body = abs(c - o)
    range_ = h - l if h != l else 1e-9
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l

    if body / range_ < 0.1:
        return "doji"
    if body / range_ > 0.9:
        return "bull_marubozu" if c > o else "bear_marubozu"
    if lower_wick > body * 2 and upper_wick < body:
        return "hammer"
    if upper_wick > body * 2 and lower_wick < body:
        return "shooting_star"
    if prev_o is not None and prev_c is not None:
        prev_body = abs(prev_c - prev_o)
        if c > o and prev_c < prev_o and c > prev_o and o < prev_c and body > prev_body:
            return "bull_engulf"
        if c < o and prev_c > prev_o and o > prev_c and c < prev_o and body > prev_body:
            return "bear_engulf"
    if body / range_ < 0.3:
        return "spinning_top"
    return "normal"


def recent_candles(df: pd.DataFrame, count: int = 15) -> list:
    """Names the last N candles (simple pattern recognition, not TA-Lib)."""
    tail = df.tail(count + 1).reset_index(drop=True)
    results = []
    for i in range(1, len(tail)):
        row, prev = tail.iloc[i], tail.iloc[i - 1]
        pattern = _classify_candle(row.open, row.high, row.low, row.close, prev.open, prev.close)
        results.append({
            "time": str(row.open_time),
            "pattern": CANDLE_NAMES[pattern],
            "direction": "bull" if row.close >= row.open else "bear",
        })
    return results

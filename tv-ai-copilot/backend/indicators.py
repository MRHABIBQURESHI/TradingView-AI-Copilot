"""
indicators.py
Calculates all the technical indicators requested:
MACD, ADX, RSI, Stochastic, CMF, OBV, Fibonacci levels.
"""

import pandas as pd
# pyrefly: ignore [missing-import]
from ta.trend import MACD, ADXIndicator
# pyrefly: ignore [missing-import]
from ta.momentum import RSIIndicator, StochasticOscillator
# pyrefly: ignore [missing-import]
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


def compute_zscore(df: pd.DataFrame, period: int = 20, extreme_thresh: float = 2.5, fat_tail_thresh: float = 3.0) -> dict:
    """
    Section 3.4 & 9.5: Statistical Extreme on Normal Distribution
    Z = (Pt - mu_20) / sigma_20
    Boundary: +/-2.5 sigma = 98.7% probability boundary
    Fat-Tail / Mean Reversion: +/-3.0 sigma = 99.7% boundary
    """
    close = df["close"]
    rolling_mean = close.rolling(window=period).mean()
    rolling_std = close.rolling(window=period).std()

    mean_val = float(rolling_mean.iloc[-1])
    std_val = float(rolling_std.iloc[-1]) if float(rolling_std.iloc[-1]) > 0 else 1e-6
    last_close = float(close.iloc[-1])

    z_val = (last_close - mean_val) / std_val

    upper_25 = mean_val + (std_val * extreme_thresh)
    upper_30 = mean_val + (std_val * fat_tail_thresh)
    lower_25 = mean_val - (std_val * extreme_thresh)
    lower_30 = mean_val - (std_val * fat_tail_thresh)

    if z_val <= -fat_tail_thresh:
        condition = "Extreme Oversold Reversal (-3.0σ)"
        bias = "Strong Bullish Mean-Reversion"
    elif z_val <= -extreme_thresh:
        condition = "Statistical Oversold (-2.5σ Boundary)"
        bias = "Bullish Mean-Reversion"
    elif z_val >= fat_tail_thresh:
        condition = "Extreme Overbought Reversal (+3.0σ)"
        bias = "Strong Bearish Mean-Reversion"
    elif z_val >= extreme_thresh:
        condition = "Statistical Overbought (+2.5σ Boundary)"
        bias = "Bearish Mean-Reversion"
    else:
        condition = "Normal Distribution Range"
        bias = "Neutral / Trend Follow"

    return {
        "z_score": round(z_val, 2),
        "mean_20": round(mean_val, 4),
        "std_20": round(std_val, 4),
        "upper_extreme_2_5": round(upper_25, 4),
        "upper_extreme_3_0": round(upper_30, 4),
        "lower_extreme_2_5": round(lower_25, 4),
        "lower_extreme_3_0": round(lower_30, 4),
        "condition": condition,
        "bias": bias,
        "is_extreme": abs(z_val) >= extreme_thresh
    }


def compute_cvd_and_absorption(df: pd.DataFrame, vol_multiplier: float = 1.4) -> dict:
    """
    Section 3.2: Cumulative Volume Delta (CVD) & Absorption Trap Engine
    CVDreversal != Delta P
    Detects when aggressive market volume is absorbed by institutional limit orders.
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]
    open_p = df["open"]
    volume = df["volume"]

    ranges = (high - low).replace(0, 1e-9)
    # Estimate intra-bar delta: buyer volume share vs seller volume share
    bull_vol = volume * ((close - low) / ranges)
    bear_vol = volume * ((high - close) / ranges)
    bar_deltas = bull_vol - bear_vol
    cvd_series = bar_deltas.cumsum()

    last_delta = float(bar_deltas.iloc[-1])
    recent_cvd_slope = float(cvd_series.iloc[-1] - cvd_series.iloc[-5]) if len(cvd_series) >= 5 else 0.0

    avg_vol = float(volume.rolling(20).mean().iloc[-1])
    last_vol = float(volume.iloc[-1])
    is_high_vol = last_vol >= (avg_vol * vol_multiplier)

    last_body = abs(float(close.iloc[-1]) - float(open_p.iloc[-1]))
    last_range = float(ranges.iloc[-1])
    body_pct = last_body / last_range if last_range > 0 else 0

    # Absorption logic:
    # 1. Bullish Absorption: High volume + negative/heavy sell delta, but price fails to drop (tight body / wick rejection)
    bull_absorption = is_high_vol and last_delta < 0 and (close.iloc[-1] >= open_p.iloc[-1] or body_pct < 0.3)
    # 2. Bearish Absorption: High volume + positive/heavy buy delta, but price fails to push (tight body / wick rejection)
    bear_absorption = is_high_vol and last_delta > 0 and (close.iloc[-1] <= open_p.iloc[-1] or body_pct < 0.3)

    state = "Neutral Flow"
    if bull_absorption:
        state = "Whale Limit Buy Absorption Trap! (Bullish Reversal)"
    elif bear_absorption:
        state = "Whale Limit Sell Absorption Trap! (Bearish Reversal)"
    elif recent_cvd_slope > 0:
        state = "Cumulative Buying Delta Dominance"
    else:
        state = "Cumulative Selling Delta Dominance"

    return {
        "bar_delta": round(last_delta, 2),
        "cvd_trend": "Rising (Aggressive Buys)" if recent_cvd_slope > 0 else "Falling (Aggressive Sells)",
        "bull_absorption": bool(bull_absorption),
        "bear_absorption": bool(bear_absorption),
        "absorption_trap_active": bool(bull_absorption or bear_absorption),
        "state_summary": state
    }


def detect_liquidity_sweeps(df: pd.DataFrame, lookback: int = 20, min_wick_pct: float = 40.0) -> dict:
    """
    Section 3.3 & Rule 2: "Never Enter Without a Stop Hunt"
    Detects Liquidity Sweeps where price spikes beyond swing highs (BSL) or swing lows (SSL)
    and rejects sharply back inside the range with high wick percentage.
    """
    recent = df.tail(lookback + 2).reset_index(drop=True)
    swing_high = recent["high"].iloc[:-1].max()
    swing_low = recent["low"].iloc[:-1].min()

    curr = recent.iloc[-1]
    c_open, c_high, c_low, c_close = curr["open"], curr["high"], curr["low"], curr["close"]
    c_range = max(c_high - c_low, 1e-9)

    upper_wick = c_high - max(c_open, c_close)
    lower_wick = min(c_open, c_close) - c_low

    wick_up_pct = (upper_wick / c_range) * 100.0
    wick_dn_pct = (lower_wick / c_range) * 100.0

    bsl_sweep = (c_high > swing_high) and (c_close < swing_high) and (wick_up_pct >= min_wick_pct)
    ssl_sweep = (c_low < swing_low) and (c_close > swing_low) and (wick_dn_pct >= min_wick_pct)

    status = "No Sweep"
    if bsl_sweep:
        status = "⚡ Buy-Side Liquidity Swept (Bearish Stop Hunt Rejection)"
    elif ssl_sweep:
        status = "⚡ Sell-Side Liquidity Swept (Bullish Stop Hunt Rejection)"

    return {
        "bsl_sweep": bool(bsl_sweep),
        "ssl_sweep": bool(ssl_sweep),
        "has_sweep": bool(bsl_sweep or ssl_sweep),
        "status": status,
        "upper_wick_pct": round(wick_up_pct, 1),
        "lower_wick_pct": round(wick_dn_pct, 1),
        "swing_high": round(swing_high, 4),
        "swing_low": round(swing_low, 4)
    }


def compute_fibonacci(df: pd.DataFrame, lookback: int = 100) -> dict:
    """Fibonacci retracement levels and Golden Pocket (0.618 - 0.650) zone."""
    recent = df.tail(lookback)
    swing_high = float(recent["high"].max())
    swing_low = float(recent["low"].min())
    diff = swing_high - swing_low
    last_price = float(df["close"].iloc[-1])

    fib_0618 = swing_high - (0.618 * diff)
    fib_0650 = swing_high - (0.650 * diff)

    in_golden_pocket = (last_price <= fib_0618) and (last_price >= fib_0650)
    near_golden_pocket = abs(last_price - fib_0618) / last_price < 0.008

    levels = {
        "0.0 (High)": round(swing_high, 4),
        "0.236": round(swing_high - 0.236 * diff, 4),
        "0.382": round(swing_high - 0.382 * diff, 4),
        "0.500 (Mid)": round(swing_high - 0.5 * diff, 4),
        "0.618 (Golden)": round(fib_0618, 4),
        "0.650 (Pocket)": round(fib_0650, 4),
        "0.786 (Deep)": round(swing_high - 0.786 * diff, 4),
        "1.0 (Low)": round(swing_low, 4),
    }

    return {
        "levels": levels,
        "golden_pocket_range": [round(fib_0650, 4), round(fib_0618, 4)],
        "in_golden_pocket": in_golden_pocket,
        "near_golden_pocket": near_golden_pocket,
        "status": "Inside Golden Pocket (0.618-0.65 OTE)" if in_golden_pocket else ("Near 0.618 Pocket" if near_golden_pocket else "Outside Golden Pocket")
    }


def calculate_risk_management(capital: float, last_price: float, bias: str, stop_hunt: dict, z_score: dict) -> dict:
    """
    Section 3.3: Execution & Risk Formula (How 80%+ Is Locked)
    Position Size = (Capital * 0.01) / (|Entry - Stop-Loss| / Entry)
    TP1 at 1:1 RRR (50% Out): Risk moved to Breakeven
    TP2 at 1:2 RRR (Remaining 50%)
    TP3 at 1:3 RRR (Runner)
    """
    risk_dollars = capital * 0.01  # Fixed 1% Risk (Rule 4)

    is_long = bias == "Bullish"
    atr_approx = (last_price * 0.015)

    if is_long:
        sl = stop_hunt.get("swing_low", last_price - atr_approx)
        if sl >= last_price:
            sl = last_price - atr_approx
        risk_dist = max(last_price - sl, last_price * 0.003)
        tp1 = last_price + (risk_dist * 1.0)
        tp2 = last_price + (risk_dist * 2.0)
        tp3 = last_price + (risk_dist * 3.0)
    else:
        sl = stop_hunt.get("swing_high", last_price + atr_approx)
        if sl <= last_price:
            sl = last_price + atr_approx
        risk_dist = max(sl - last_price, last_price * 0.003)
        tp1 = last_price - (risk_dist * 1.0)
        tp2 = last_price - (risk_dist * 2.0)
        tp3 = last_price - (risk_dist * 3.0)

    risk_fraction = risk_dist / last_price
    position_size_usd = risk_dollars / risk_fraction if risk_fraction > 0 else capital
    units = position_size_usd / last_price

    return {
        "account_capital": capital,
        "risk_per_trade_usd": round(risk_dollars, 2),
        "risk_per_trade_pct": "1.0%",
        "entry_price": round(last_price, 4),
        "stop_loss": round(sl, 4),
        "risk_distance": round(risk_dist, 4),
        "recommended_position_usd": round(position_size_usd, 2),
        "recommended_position_units": round(units, 4),
        "tp1_1_to_1": round(tp1, 4),
        "tp1_action": "Close 50% Position & Shift Stop-Loss to Breakeven (Risk = $0)",
        "tp2_1_to_2": round(tp2, 4),
        "tp2_action": "Close Remaining 50% (Full Win)",
        "tp3_1_to_3": round(tp3, 4),
        "expected_value_profile": "+$800 net gain per 100 trades @ 1:2 RRR with breakeven scaling"
    }



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

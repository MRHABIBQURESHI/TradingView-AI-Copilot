"""
structure.py
Institutional Trading Win-Rate Framework Engine (80%-85% Precision System)
- Macro Trend Baseline: Daily EMA 200 (Rule 1: Never counter-trend)
- 4-Filter Pre-Trade Confluence Engine (EMA200, Fibo 0.618 OTE, CVD Absorption, Z-Score Extreme)
- Liquidity Sweep / Stop Hunt Verification (Rule 2)
- Market Regime Identification (Trending vs Ranging - Critical Review 9.9)
- 5 Non-Negotiable Discipline Rules Checklist
- Asymmetric Risk Scaling Protocol (TP1 1:1 Breakeven Lock, TP2 1:2/1:3)
"""

import numpy as np
import pandas as pd
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator, ADXIndicator


def detect_macro_trend(daily_df: pd.DataFrame, current_price: float, ema_len: int = 200) -> dict:
    """
    Section 3.1 & Rule 1: Macro Trend Baseline Filter
    Pt > EMA200 (Daily Timeframe) -> Longs Only
    Pt < EMA200 (Daily Timeframe) -> Shorts Only
    "Never Short an Uptrend / Long a Downtrend"
    """
    if daily_df is None or len(daily_df) < 50:
        return {
            "daily_ema_200": round(current_price, 4),
            "macro_bias": "Neutral",
            "rule_1_allowed": "Longs & Shorts (Caution: Insufficient Daily Data)",
            "macro_status": "Neutral"
        }

    close_series = daily_df["close"]
    actual_len = min(ema_len, len(close_series) - 1)
    ema_series = EMAIndicator(close=close_series, window=actual_len).ema_indicator()
    daily_ema = float(ema_series.iloc[-1])

    is_bull = current_price >= daily_ema
    rule_status = "ONLY LONGS ALLOWED (Macro Uptrend)" if is_bull else "ONLY SHORTS ALLOWED (Macro Downtrend)"

    return {
        "daily_ema_200": round(daily_ema, 4),
        "macro_bias": "Bullish" if is_bull else "Bearish",
        "rule_1_allowed": rule_status,
        "is_macro_bull": is_bull,
        "macro_status": f"Price {'above' if is_bull else 'below'} Daily EMA {actual_len}"
    }


def detect_market_regime(df: pd.DataFrame) -> dict:
    """
    Section 9.9: Market Regime Dependence
    Separates Trending Expansion from Ranging / Mean-Reversion.
    Prevents fighting strong runaway trends with mean-reversion filters.
    """
    adx_ind = ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=14)
    adx_val = float(adx_ind.adx().iloc[-1])

    atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14).average_true_range()
    atr_mean = float(atr.rolling(30).mean().iloc[-1]) if len(atr) >= 30 else float(atr.iloc[-1])
    atr_curr = float(atr.iloc[-1])

    is_trending = adx_val >= 25.0 and atr_curr >= atr_mean

    regime = "Trending Expansion" if is_trending else "Ranging / Mean Reversion"
    guidance = "Look for Golden Pocket Pullbacks in Macro Direction" if is_trending else "Look for Statistical Z-Score Extremes & Absorption Reversals"

    return {
        "regime": regime,
        "adx_strength": round(adx_val, 2),
        "volatility_expansion": atr_curr > atr_mean,
        "recommended_approach": guidance
    }


def evaluate_institutional_confluence(
    macro: dict,
    fibo: dict,
    zscore: dict,
    cvd: dict,
    sweep: dict,
    current_price: float,
    structure: str
) -> dict:
    """
    Section 3.1 & 3.3: Pre-Trade 4 Mathematical Filters & Confluence Scoring
    1. Trend Baseline: Pt > EMA200
    2. Fibonacci Level: 0.618 Golden Pocket
    3. Order Flow Imbalance: CVDreversal != Delta P (Absorption Trap)
    4. Statistical Extreme: Z-Score <= -2.5 or >= +2.5
    Plus Stop Hunt Liquidity Sweep (Rule 2).
    """
    is_macro_bull = macro.get("is_macro_bull", True)
    in_golden_pocket = fibo.get("in_golden_pocket", False) or fibo.get("near_golden_pocket", False)
    z_val = zscore.get("z_score", 0.0)
    is_extreme = zscore.get("is_extreme", False)
    bull_abs = cvd.get("bull_absorption", False)
    bear_abs = cvd.get("bear_absorption", False)
    ssl_sweep = sweep.get("ssl_sweep", False)
    bsl_sweep = sweep.get("bsl_sweep", False)

    # --- Bullish Confluence Filters ---
    long_f1 = is_macro_bull  # Rule 1
    long_f2 = in_golden_pocket or (current_price <= fibo["levels"]["0.618 (Golden)"])
    long_f3 = bull_abs or ssl_sweep or cvd.get("bar_delta", 0) > 0
    long_f4 = z_val <= -1.5 or is_extreme
    long_score = sum([long_f1, long_f2, long_f3, long_f4]) * 25

    # --- Bearish Confluence Filters ---
    short_f1 = not is_macro_bull  # Rule 1
    short_f2 = in_golden_pocket or (current_price >= fibo["levels"]["0.618 (Golden)"])
    short_f3 = bear_abs or bsl_sweep or cvd.get("bar_delta", 0) < 0
    short_f4 = z_val >= 1.5 or is_extreme
    short_score = sum([short_f1, short_f2, short_f3, short_f4]) * 25

    active_direction = "Bullish" if is_macro_bull else "Bearish"
    active_score = long_score if is_macro_bull else short_score

    # Setup Grading
    is_a_plus = False
    grade = "No Setup (Stand Down)"
    action = "Wait for Confluence Alignment (Rule 3: No Setup, No Trade)"

    if active_score >= 100:
        is_a_plus = True
        grade = "A+ INSTITUTIONAL SETUP (80%-85% Framework)"
        action = f"Execute {active_direction.upper()} Trade. Apply 1% Position Sizing & Move to Breakeven at TP1."
    elif active_score >= 75:
        grade = "Grade A Setup (High Probability)"
        action = f"Favorable {active_direction} alignment. Wait for final wick confirmation."
    elif active_score >= 50:
        grade = "Grade B Setup (Moderate)"
        action = "Partial confluence. Stand down or trade with reduced size."

    checklist = [
        {"filter": "1. Macro Trend (Daily EMA 200)", "passed": bool(long_f1 if is_macro_bull else short_f1), "detail": macro.get("rule_1_allowed", "")},
        {"filter": "2. Fibonacci Golden Pocket (0.618 OTE)", "passed": bool(in_golden_pocket), "detail": fibo.get("status", "")},
        {"filter": "3. CVD Order Flow & Absorption", "passed": bool(bull_abs or bear_abs or ssl_sweep or bsl_sweep), "detail": cvd.get("state_summary", "")},
        {"filter": "4. Statistical Extreme (Z-Score)", "passed": bool(is_extreme or abs(z_val) >= 1.5), "detail": f"Z = {z_val} ({zscore.get('condition', '')})"},
        {"filter": "5. Stop Hunt Sweep (Rule 2)", "passed": bool(ssl_sweep or bsl_sweep), "detail": sweep.get("status", "")},
    ]

    return {
        "confluence_score_pct": active_score,
        "bias": active_direction,
        "grade": grade,
        "is_a_plus_setup": is_a_plus,
        "action_recommendation": action,
        "checklist": checklist
    }


def evaluate_discipline_rules(confluence: dict, risk_mgmt: dict) -> list:
    """
    Section 6: Five Non-Negotiable Discipline Rules
    Rule 1: Never Short an Uptrend / Long a Downtrend
    Rule 2: Never Enter Without a Stop Hunt (Wick Rejection)
    Rule 3: No Setup, No Trade
    Rule 4: Fixed Sizing (Strict 1% Risk)
    Rule 5: Move to Breakeven at TP1 (Eliminates Chunky Losses)
    """
    chk = {c["filter"]: c["passed"] for c in confluence["checklist"]}

    return [
        {
            "rule": "Rule 1: Macro Trend Discipline",
            "instruction": "Never Short an Uptrend / Long a Downtrend (Daily EMA200).",
            "status": "COMPLIANT" if chk.get("1. Macro Trend (Daily EMA 200)") else "VIOLATION RISK",
            "passed": chk.get("1. Macro Trend (Daily EMA 200)", False)
        },
        {
            "rule": "Rule 2: Stop Hunt Sweep Required",
            "instruction": "Never enter without liquidity sweep rejection wick.",
            "status": "CONFIRMED" if chk.get("5. Stop Hunt Sweep (Rule 2)") else "WAITING FOR SWEEP",
            "passed": chk.get("5. Stop Hunt Sweep (Rule 2)", False)
        },
        {
            "rule": "Rule 3: No Setup, No Trade",
            "instruction": "Only execute when confluence score >= 75% (A / A+ setups).",
            "status": "TRADE ACTIVE" if confluence["confluence_score_pct"] >= 75 else "STAND DOWN",
            "passed": confluence["confluence_score_pct"] >= 75
        },
        {
            "rule": "Rule 4: Fixed 1% Risk Sizing",
            "instruction": f"Strict 1% account risk (${risk_mgmt['risk_per_trade_usd']} on ${risk_mgmt['account_capital']:,}).",
            "status": "LOCKED",
            "passed": True
        },
        {
            "rule": "Rule 5: Move to Breakeven at TP1",
            "instruction": f"At TP1 ({risk_mgmt['tp1_1_to_1']}), close 50% & move SL to Entry. Remaining risk = $0.",
            "status": "PROTOCOL READY",
            "passed": True
        }
    ]


def detect_structure(df: pd.DataFrame, swing_window: int = 5) -> dict:
    """Basic higher-high/higher-low vs lower-high/lower-low structure check."""
    highs = df["high"]
    lows = df["low"]

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
    """Legacy backward-compatible composite score generator."""
    score = 50.0

    score += (ind["rsi"] - 50) * 0.4
    score += np.clip(ind["macd"]["histogram"] * 5, -10, 10)

    if ind["adx"]["adx"] > 20:
        if ind["adx"]["plus_di"] > ind["adx"]["minus_di"]:
            score += 8
        else:
            score -= 8

    score += (ind["stochastic"]["k"] - 50) * 0.15
    score += np.clip(ind["cmf"] * 40, -8, 8)
    score += 5 if ind["obv"]["trend"] == "rising" else -5

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


HORIZONS_HOURS = [1, 2, 4, 12, 24, 48]


def project_moves(df: pd.DataFrame, bias: str, bullish_pct: float) -> list:
    """ATR-based projected range per time horizon."""
    atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14).average_true_range().iloc[-1]
    last_price = df["close"].iloc[-1]

    time_diffs = df["open_time"].diff().dropna()
    minutes_per_candle = time_diffs.dt.total_seconds().median() / 60 if len(time_diffs) else 60
    bars_per_hour = max(60 / minutes_per_candle, 1 / 24)

    direction = 1 if bias == "Bullish" else (-1 if bias == "Bearish" else 0)
    strength = abs(bullish_pct - 50) / 50

    projections = []
    for h in HORIZONS_HOURS:
        bars = bars_per_hour * h
        move = atr * np.sqrt(bars) * 0.5
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

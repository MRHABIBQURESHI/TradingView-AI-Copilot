"""
data.py
Fetches live OHLCV candle data from multiple public REST APIs (Kraken, Bybit, Binance).
Supports automatic fallback and normalizes pairs (e.g. BTCUSD <-> BTCUSDT)
so it works reliably even from US cloud hosting (e.g. Vercel) where Binance is geoblocked.
"""

import requests
import pandas as pd

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# --- KRAKEN CONFIG (US-friendly, never geoblocked on Vercel) ---
KRAKEN_BASE = "https://api.kraken.com/0/public/OHLC"
KRAKEN_INTERVAL_MAP = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}

# --- BYBIT CONFIG ---
BYBIT_BASE = "https://api.bybit.com/v5/market/kline"
BYBIT_INTERVAL_MAP = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "1d": "D",
    "1w": "W",
}

# --- BINANCE CONFIG ---
BINANCE_BASE = "https://api.binance.com/api/v3/klines"
BINANCE_INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w",
}


def _fetch_from_kraken(symbol: str, interval: str = "1h") -> pd.DataFrame:
    kraken_interval = KRAKEN_INTERVAL_MAP.get(interval, 60)
    # Normalize pair names: Kraken prefers XBTUSD for BTCUSD
    pair = symbol.upper()
    if pair in ["BTCUSD", "BTCUSDT"]:
        pair = "XBTUSD"

    params = {"pair": pair, "interval": kraken_interval}
    resp = requests.get(KRAKEN_BASE, params=params, headers=HEADERS, timeout=8)
    resp.raise_for_status()
    data = resp.json()

    if data.get("error"):
        # try original symbol
        params["pair"] = symbol.upper()
        resp = requests.get(KRAKEN_BASE, params=params, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise ValueError(f"Kraken error: {data['error']}")

    result = data.get("result", {})
    keys = [k for k in result.keys() if k != "last"]
    if not keys:
        raise ValueError(f"No candle data from Kraken for {symbol}")

    raw = result[keys[0]]
    df = pd.DataFrame(raw, columns=["open_time", "open", "high", "low", "close", "vwap", "volume", "count"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df["open_time"] = pd.to_datetime(df["open_time"].astype(int), unit="s")
    df = df.sort_values("open_time").reset_index(drop=True)
    return df[["open_time", "open", "high", "low", "close", "volume"]]


def _fetch_from_bybit(symbol: str, interval: str = "1h", limit: int = 300) -> pd.DataFrame:
    bybit_interval = BYBIT_INTERVAL_MAP.get(interval, "60")
    # For spot Bybit, if symbol ends with USD convert to USDT
    pair = symbol.upper()
    if pair.endswith("USD") and not pair.endswith("USDT"):
        pair = pair + "T"

    params = {
        "category": "spot",
        "symbol": pair,
        "interval": bybit_interval,
        "limit": limit,
    }
    resp = requests.get(BYBIT_BASE, params=params, headers=HEADERS, timeout=8)
    resp.raise_for_status()
    data = resp.json()

    raw = data.get("result", {}).get("list", [])
    if not raw:
        raise ValueError(f"No data returned from Bybit for {pair}")

    df = pd.DataFrame(raw, columns=["open_time", "open", "high", "low", "close", "volume", "turnover"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df["open_time"] = pd.to_datetime(df["open_time"].astype(int), unit="ms")
    df = df.sort_values("open_time").reset_index(drop=True)
    return df[["open_time", "open", "high", "low", "close", "volume"]]


def _fetch_from_binance(symbol: str, interval: str = "1h", limit: int = 300) -> pd.DataFrame:
    binance_interval = BINANCE_INTERVAL_MAP.get(interval, "1h")
    pair = symbol.upper()
    if pair.endswith("USD") and not pair.endswith("USDT"):
        pair = pair + "T"

    params = {
        "symbol": pair,
        "interval": binance_interval,
        "limit": limit,
    }
    resp = requests.get(BINANCE_BASE, params=params, headers=HEADERS, timeout=8)
    resp.raise_for_status()
    raw = resp.json()

    if not raw or not isinstance(raw, list):
        raise ValueError(f"No data returned from Binance for {pair}")

    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df[["open_time", "open", "high", "low", "close", "volume"]]


def fetch_klines(symbol: str, interval: str = "1h", limit: int = 300) -> pd.DataFrame:
    """
    Fetch recent candles for a symbol.
    Attempts sources in order of reliability on cloud hosting:
    1. Kraken (US-based, works reliably on Vercel without geoblock)
    2. Bybit (with browser User-Agent and USD->USDT normalization)
    3. Binance
    """
    errors = []

    # 1. Try Kraken
    try:
        return _fetch_from_kraken(symbol, interval)
    except Exception as e:
        errors.append(f"Kraken: {e}")

    # 2. Try Bybit
    try:
        return _fetch_from_bybit(symbol, interval, limit)
    except Exception as e:
        errors.append(f"Bybit: {e}")

    # 3. Try Binance
    try:
        return _fetch_from_binance(symbol, interval, limit)
    except Exception as e:
        errors.append(f"Binance: {e}")

    raise RuntimeError(f"All data sources failed for {symbol}: " + " | ".join(errors))

"""
data.py
Fetches live OHLCV candle data from public REST APIs.
Tries Binance first; if geoblocked (e.g. on US cloud hosting like Vercel),
automatically falls back to Bybit.
"""

import requests
import pandas as pd

BINANCE_BASE = "https://api.binance.com/api/v3/klines"
BYBIT_BASE = "https://api.bybit.com/v5/market/kline"

# Map our friendly interval names to Binance's interval codes
BINANCE_INTERVAL_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h",
    "1d": "1d", "1w": "1w",
}

# Map our friendly interval names to Bybit's interval codes
BYBIT_INTERVAL_MAP = {
    "1m": "1", "5m": "5", "15m": "15", "30m": "30",
    "1h": "60", "2h": "120", "4h": "240",
    "1d": "D", "1w": "W",
}


def _fetch_from_binance(symbol: str, interval: str = "1h", limit: int = 300) -> pd.DataFrame:
    binance_interval = BINANCE_INTERVAL_MAP.get(interval, "1h")
    params = {
        "symbol": symbol.upper(),
        "interval": binance_interval,
        "limit": limit,
    }
    resp = requests.get(BINANCE_BASE, params=params, timeout=8)
    resp.raise_for_status()
    raw = resp.json()

    if not raw or not isinstance(raw, list):
        raise ValueError(f"No data returned from Binance for symbol={symbol}")

    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df[["open_time", "open", "high", "low", "close", "volume"]]


def _fetch_from_bybit(symbol: str, interval: str = "1h", limit: int = 300) -> pd.DataFrame:
    bybit_interval = BYBIT_INTERVAL_MAP.get(interval, "60")
    params = {
        "category": "spot",
        "symbol": symbol.upper(),
        "interval": bybit_interval,
        "limit": limit,
    }
    resp = requests.get(BYBIT_BASE, params=params, timeout=8)
    resp.raise_for_status()
    data = resp.json()

    raw = data.get("result", {}).get("list", [])
    if not raw:
        raise ValueError(f"No data returned from Bybit for symbol={symbol}")

    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume", "turnover"
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df["open_time"] = pd.to_datetime(df["open_time"].astype(int), unit="ms")
    # Bybit returns newest to oldest; sort ascending
    df = df.sort_values("open_time").reset_index(drop=True)
    return df[["open_time", "open", "high", "low", "close", "volume"]]


def fetch_klines(symbol: str, interval: str = "1h", limit: int = 300) -> pd.DataFrame:
    """
    Fetch recent candles for a symbol (e.g. 'BTCUSDT').
    Tries Binance first; falls back to Bybit if geoblocked or unavailable.
    """
    try:
        return _fetch_from_binance(symbol, interval, limit)
    except Exception as binance_err:
        try:
            return _fetch_from_bybit(symbol, interval, limit)
        except Exception as bybit_err:
            raise RuntimeError(f"Data fetch failed: Binance ({binance_err}) | Bybit ({bybit_err})")

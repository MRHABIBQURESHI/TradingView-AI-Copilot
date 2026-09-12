"""
data.py
Fetches live OHLCV candle data from Binance's public REST API.
No API key needed for market data (read-only, public endpoint).

If you want to use a different exchange/broker later, you only need to
rewrite `fetch_klines()` below to return a pandas DataFrame with the same
columns: ['open_time','open','high','low','close','volume']
Everything else in the project (indicators, structure, projections) will
keep working unchanged.
"""

import requests
import pandas as pd

BINANCE_BASE = "https://api.binance.com/api/v3/klines"

# Map our friendly interval names to Binance's interval codes
INTERVAL_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h",
    "1d": "1d", "1w": "1w",
}


def fetch_klines(symbol: str, interval: str = "1h", limit: int = 300) -> pd.DataFrame:
    """
    Fetch recent candles for a symbol (e.g. 'BTCUSDT') from Binance.
    Returns a DataFrame sorted oldest -> newest.
    """
    binance_interval = INTERVAL_MAP.get(interval, "1h")
    params = {
        "symbol": symbol.upper(),
        "interval": binance_interval,
        "limit": limit,
    }
    resp = requests.get(BINANCE_BASE, params=params, timeout=10)
    resp.raise_for_status()
    raw = resp.json()

    if not raw:
        raise ValueError(f"No data returned for symbol={symbol}, interval={interval}")

    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df[["open_time", "open", "high", "low", "close", "volume"]]

import ccxt
import pandas as pd
from src.config import EXCHANGE, SYMBOL, TIMEFRAME, API_KEY, API_SECRET

def get_exchange():
    exchange_class = getattr(ccxt, EXCHANGE)
    exchange = exchange_class({
        "apiKey": API_KEY,
        "secret": API_SECRET,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    return exchange

def fetch_ohlcv(limit=500):
    exchange = get_exchange()
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df

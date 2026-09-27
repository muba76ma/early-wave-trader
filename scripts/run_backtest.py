"""
Simple backtest runner (vectorised-style, no external library required).
Usage:
    python scripts/run_backtest.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings
from src.data.fetcher import DataFetcher
from src.strategy.early_wave import EarlyWaveStrategy
from src.execution.broker import PaperBroker
from src.risk.manager import RiskManager


def run_backtest(
    symbol: str = "BTC/USDT",
    timeframe: str = "5m",
    limit: int = 1000,
) -> None:
    print(f"Backtesting {symbol} {timeframe} …")

    fetcher = DataFetcher(exchange=settings.EXCHANGE)
    df = fetcher.fetch_ohlcv(symbol, timeframe, limit=limit)
    print(f"Loaded {len(df)} candles")

    strategy = EarlyWaveStrategy(
        lookback=settings.WAVE_LOOKBACK,
        volume_multiplier=settings.VOLUME_MULTIPLIER,
        min_wave_strength=settings.MIN_WAVE_STRENGTH,
    )
    df = strategy.prepare(df)

    risk = RiskManager(
        equity=10_000.0,
        risk_per_trade=settings.RISK_PER_TRADE,
        max_open_trades=settings.MAX_OPEN_TRADES,
    )
    broker = PaperBroker(starting_equity=10_000.0)

    trades = 0
    for i in range(strategy.lookback + 20, len(df)):
        window = df.iloc[: i + 1]
        signal = strategy.generate_signal(window)

        # Update existing positions with current close
        price = float(df["close"].iloc[i])
        broker.update(price)

        if signal and risk.can_open_trade():
            qty = risk.position_size(signal)
            if qty > 0:
                order = broker.place_order(signal, qty)
                if order:
                    risk.register_trade(signal, qty)
                    trades += 1

    closed = broker.closed_orders()
    wins = [o for o in closed if o.pnl > 0]
    losses = [o for o in closed if o.pnl <= 0]

    print("\n===== BACKTEST RESULTS =====")
    print(f"Total trades      : {len(closed)}")
    print(f"Winning trades    : {len(wins)}")
    print(f"Losing trades     : {len(losses)}")
    if closed:
        winrate = len(wins) / len(closed) * 100
        total_pnl = sum(o.pnl for o in closed)
        print(f"Win rate          : {winrate:.1f}%")
        print(f"Total PnL         : {total_pnl:.2f}")
        print(f"Final equity      : {broker.equity:.2f}")
    print("============================")


if __name__ == "__main__":
    run_backtest()

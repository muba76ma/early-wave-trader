"""
Main entry point for early-wave-trader.
Runs a continuous paper-trading loop (or one-shot signal check).
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# Allow running as script from project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings
from src.data.fetcher import DataFetcher
from src.strategy.early_wave import EarlyWaveStrategy
from src.risk.manager import RiskManager
from src.execution.broker import PaperBroker


def setup_logging() -> None:
    settings.ensure_dirs()
    handlers = [logging.StreamHandler()]
    if settings.LOG_TO_FILE:
        handlers.append(
            logging.FileHandler(settings.LOGS_DIR / "trader.log")
        )

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
    )


def run_once() -> None:
    """Fetch latest data, generate signal, and (paper) execute if valid."""
    logger = logging.getLogger("main")

    fetcher = DataFetcher(exchange=settings.EXCHANGE)
    strategy = EarlyWaveStrategy(
        lookback=settings.WAVE_LOOKBACK,
        volume_multiplier=settings.VOLUME_MULTIPLIER,
        min_wave_strength=settings.MIN_WAVE_STRENGTH,
    )
    risk = RiskManager(
        equity=10_000.0,
        risk_per_trade=settings.RISK_PER_TRADE,
        max_open_trades=settings.MAX_OPEN_TRADES,
        leverage=settings.LEVERAGE,
    )
    broker = PaperBroker(starting_equity=10_000.0)

    logger.info(
        "Starting Early Wave Trader | %s %s | mode=%s",
        settings.SYMBOL,
        settings.TIMEFRAME,
        settings.MODE,
    )

    try:
        df = fetcher.fetch_ohlcv(
            symbol=settings.SYMBOL,
            timeframe=settings.TIMEFRAME,
            limit=300,
        )
        logger.info("Fetched %d candles", len(df))

        df = strategy.prepare(df)
        signal = strategy.generate_signal(df)

        if signal is None:
            logger.info("No signal on latest bar")
            return

        logger.info(
            "SIGNAL → %s | strength=%.2f | %s",
            signal.side.upper(),
            signal.strength,
            signal.reason,
        )

        qty = risk.position_size(signal)
        if qty > 0:
            order = broker.place_order(signal, qty)
            if order:
                risk.register_trade(signal, qty)

        # Simulate price update (in real loop you would feed live ticks)
        last_price = float(df["close"].iloc[-1])
        broker.update(last_price)

        logger.info("Equity: %.2f | Open orders: %d", broker.equity, len(broker.open_orders()))

    except Exception as e:
        logger.exception("Error in run_once: %s", e)


def run_loop(interval_seconds: int = 60) -> None:
    """Simple continuous loop (paper mode)."""
    logger = logging.getLogger("main")
    logger.info("Entering continuous loop (interval=%ds). Ctrl+C to stop.", interval_seconds)
    try:
        while True:
            run_once()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("Stopped by user")


if __name__ == "__main__":
    setup_logging()

    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        run_loop()
    else:
        run_once()

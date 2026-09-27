"""
Central configuration loader.
Loads values from environment variables (.env) with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class Settings:
    # Mode
    MODE: str = os.getenv("MODE", "paper")
    EXCHANGE: str = os.getenv("EXCHANGE", "binance")

    # API
    API_KEY: str = os.getenv("API_KEY", "")
    API_SECRET: str = os.getenv("API_SECRET", "")

    # Trading
    SYMBOL: str = os.getenv("SYMBOL", "BTC/USDT")
    TIMEFRAME: str = os.getenv("TIMEFRAME", "5m")
    RISK_PER_TRADE: float = float(os.getenv("RISK_PER_TRADE", "0.01"))
    MAX_OPEN_TRADES: int = int(os.getenv("MAX_OPEN_TRADES", "3"))
    LEVERAGE: int = int(os.getenv("LEVERAGE", "1"))

    # Strategy parameters
    WAVE_LOOKBACK: int = int(os.getenv("WAVE_LOOKBACK", "20"))
    VOLUME_MULTIPLIER: float = float(os.getenv("VOLUME_MULTIPLIER", "1.8"))
    MIN_WAVE_STRENGTH: float = float(os.getenv("MIN_WAVE_STRENGTH", "0.6"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"

    # Paths
    ROOT: Path = ROOT
    DATA_DIR: Path = ROOT / "data"
    LOGS_DIR: Path = ROOT / "logs"
    RESULTS_DIR: Path = ROOT / "results"

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create required directories if they do not exist."""
        for d in (cls.DATA_DIR, cls.LOGS_DIR, cls.RESULTS_DIR):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()

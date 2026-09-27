"""
Early Wave Strategy
-------------------
Detects the beginning of strong directional moves ("early waves")
using a combination of:
  - Volume surge
  - Price momentum / break of recent range
  - Simple wave strength score

This is intentionally kept simple and transparent so you can
evolve it into full Elliott Wave logic later.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    side: str          # "long" | "short" | "flat"
    strength: float    # 0.0 – 1.0
    reason: str
    entry_price: float
    stop_loss: float
    take_profit: float


class EarlyWaveStrategy:
    def __init__(
        self,
        lookback: int = 20,
        volume_multiplier: float = 1.8,
        min_wave_strength: float = 0.6,
        atr_period: int = 14,
        risk_reward: float = 2.0,
    ):
        self.lookback = lookback
        self.volume_multiplier = volume_multiplier
        self.min_wave_strength = min_wave_strength
        self.atr_period = atr_period
        self.risk_reward = risk_reward

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical columns required by the strategy."""
        df = df.copy()

        # ATR for stops
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = tr.rolling(self.atr_period).mean()

        # Volume metrics
        df["vol_ma"] = df["volume"].rolling(self.lookback).mean()
        df["vol_ratio"] = df["volume"] / df["vol_ma"]

        # Recent range
        df["range_high"] = df["high"].rolling(self.lookback).max()
        df["range_low"] = df["low"].rolling(self.lookback).min()
        df["range_mid"] = (df["range_high"] + df["range_low"]) / 2

        # Simple momentum
        df["roc"] = df["close"].pct_change(self.lookback // 2)

        # Wave strength proxy (0-1)
        # Higher when volume is elevated + price is breaking the range
        vol_score = np.clip((df["vol_ratio"] - 1) / (self.volume_multiplier - 1), 0, 1)
        breakout_up = (df["close"] > df["range_high"].shift(1)).astype(float)
        breakout_dn = (df["close"] < df["range_low"].shift(1)).astype(float)
        df["wave_strength"] = vol_score * (breakout_up + breakout_dn)

        return df

    def generate_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        """
        Look at the latest bar and decide if an early wave is starting.
        Returns a Signal or None.
        """
        if len(df) < self.lookback + self.atr_period + 5:
            return None

        row = df.iloc[-1]
        prev = df.iloc[-2]

        strength = float(row["wave_strength"])
        if strength < self.min_wave_strength:
            return None

        atr = float(row["atr"])
        if atr <= 0 or np.isnan(atr):
            return None

        close = float(row["close"])
        range_high = float(prev["range_high"])
        range_low = float(prev["range_low"])

        # Long early wave: volume surge + close above previous range high
        if close > range_high and row["vol_ratio"] >= self.volume_multiplier:
            stop = close - atr * 1.5
            target = close + atr * 1.5 * self.risk_reward
            return Signal(
                side="long",
                strength=strength,
                reason=f"Early upward wave | vol_ratio={row['vol_ratio']:.2f}",
                entry_price=close,
                stop_loss=stop,
                take_profit=target,
            )

        # Short early wave
        if close < range_low and row["vol_ratio"] >= self.volume_multiplier:
            stop = close + atr * 1.5
            target = close - atr * 1.5 * self.risk_reward
            return Signal(
                side="short",
                strength=strength,
                reason=f"Early downward wave | vol_ratio={row['vol_ratio']:.2f}",
                entry_price=close,
                stop_loss=stop,
                take_profit=target,
            )

        return None

"""
Simple risk management layer.
Controls position size and max open trades.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.strategy.early_wave import Signal

logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(
        self,
        equity: float = 10_000.0,
        risk_per_trade: float = 0.01,
        max_open_trades: int = 3,
        leverage: int = 1,
    ):
        self.equity = equity
        self.risk_per_trade = risk_per_trade
        self.max_open_trades = max_open_trades
        self.leverage = leverage
        self.open_trades: list = []

    def can_open_trade(self) -> bool:
        return len(self.open_trades) < self.max_open_trades

    def position_size(self, signal: Signal) -> float:
        """
        Calculate position size based on risk per trade and stop distance.
        Returns quantity (in base currency units).
        """
        if not self.can_open_trade():
            logger.warning("Max open trades reached")
            return 0.0

        risk_amount = self.equity * self.risk_per_trade
        stop_distance = abs(signal.entry_price - signal.stop_loss)

        if stop_distance <= 0:
            logger.error("Invalid stop distance")
            return 0.0

        # Basic position size (notional / entry)
        qty = (risk_amount / stop_distance) * self.leverage
        return round(qty, 6)

    def register_trade(self, signal: Signal, qty: float) -> None:
        self.open_trades.append(
            {
                "side": signal.side,
                "entry": signal.entry_price,
                "stop": signal.stop_loss,
                "tp": signal.take_profit,
                "qty": qty,
            }
        )
        logger.info(
            "Registered %s trade | qty=%.4f | entry=%.4f",
            signal.side,
            qty,
            signal.entry_price,
        )

    def close_trade(self, index: int = -1) -> None:
        if self.open_trades:
            closed = self.open_trades.pop(index)
            logger.info("Closed trade: %s", closed)

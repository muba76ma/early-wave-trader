"""
Paper trading broker (simulation).
Replace this class later with a real exchange connector (ccxt / alpaca / etc.).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from src.strategy.early_wave import Signal

logger = logging.getLogger(__name__)


@dataclass
class Order:
    id: str
    side: str
    qty: float
    entry: float
    stop: float
    tp: float
    status: str = "open"          # open | closed | cancelled
    exit_price: Optional[float] = None
    pnl: float = 0.0
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None


class PaperBroker:
    def __init__(self, starting_equity: float = 10_000.0):
        self.equity = starting_equity
        self.orders: List[Order] = []
        self._order_counter = 0

    def place_order(self, signal: Signal, qty: float) -> Optional[Order]:
        if qty <= 0:
            logger.warning("Quantity <= 0, order rejected")
            return None

        self._order_counter += 1
        order = Order(
            id=f"paper-{self._order_counter}",
            side=signal.side,
            qty=qty,
            entry=signal.entry_price,
            stop=signal.stop_loss,
            tp=signal.take_profit,
        )
        self.orders.append(order)
        logger.info(
            "PAPER ORDER %s %s qty=%.4f @ %.4f | SL=%.4f TP=%.4f",
            order.id,
            order.side.upper(),
            order.qty,
            order.entry,
            order.stop,
            order.tp,
        )
        return order

    def update(self, current_price: float) -> None:
        """Check open orders against current price and close if SL/TP hit."""
        for order in self.orders:
            if order.status != "open":
                continue

            hit_sl = False
            hit_tp = False

            if order.side == "long":
                if current_price <= order.stop:
                    hit_sl = True
                elif current_price >= order.tp:
                    hit_tp = True
            else:  # short
                if current_price >= order.stop:
                    hit_sl = True
                elif current_price <= order.tp:
                    hit_tp = True

            if hit_sl or hit_tp:
                order.status = "closed"
                order.exit_price = order.stop if hit_sl else order.tp
                order.closed_at = datetime.now(timezone.utc)

                direction = 1 if order.side == "long" else -1
                order.pnl = direction * (order.exit_price - order.entry) * order.qty
                self.equity += order.pnl

                reason = "SL" if hit_sl else "TP"
                logger.info(
                    "CLOSED %s %s | exit=%.4f | PnL=%.2f | equity=%.2f",
                    order.id,
                    reason,
                    order.exit_price,
                    order.pnl,
                    self.equity,
                )

    def open_orders(self) -> List[Order]:
        return [o for o in self.orders if o.status == "open"]

    def closed_orders(self) -> List[Order]:
        return [o for o in self.orders if o.status == "closed"]

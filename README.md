# early-wave-trader

**Early Wave Trader** – a clean, modular Python trading bot that detects the *start* of strong directional moves (“early waves”) using volume surge + range breakout logic.

Designed to be simple, transparent and easy to extend (you can later replace the strategy with full Elliott Wave counting, order-flow, etc.).

---

## Features

- Unified data layer (ccxt for crypto + yfinance for stocks)
- Early-wave detection strategy (volume + breakout + ATR stops)
- Risk manager (position sizing by % risk + max open trades)
- Paper broker for safe testing
- One-shot run or continuous loop
- Basic backtester
- Clean project structure ready for real exchange integration

---

## Quick Start


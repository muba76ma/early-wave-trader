"""Basic unit tests for the EarlyWaveStrategy."""

import numpy as np
import pandas as pd
import pytest

from src.strategy.early_wave import EarlyWaveStrategy, Signal


def make_sample_df(n: int = 100) -> pd.DataFrame:
    """Generate a synthetic OHLCV dataframe with an upward breakout at the end."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="5min", tz="UTC")

    close = 100 + np.cumsum(rng.normal(0, 0.3, n))
    high = close + rng.uniform(0.1, 0.8, n)
    low = close - rng.uniform(0.1, 0.8, n)
    open_ = close + rng.normal(0, 0.2, n)
    volume = rng.uniform(1000, 3000, n)

    # Force a volume spike + breakout on the last bar
    volume[-1] = volume[-20:].mean() * 3.0
    high[-1] = high[-20:-1].max() + 1.5
    close[-1] = high[-1] - 0.2

    df = pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=dates,
    )
    return df


def test_prepare_adds_columns():
    df = make_sample_df()
    strategy = EarlyWaveStrategy(lookback=20)
    prepared = strategy.prepare(df)

    expected = {"atr", "vol_ma", "vol_ratio", "range_high", "range_low", "wave_strength"}
    assert expected.issubset(prepared.columns)


def test_generate_signal_on_breakout():
    df = make_sample_df()
    strategy = EarlyWaveStrategy(
        lookback=20,
        volume_multiplier=1.5,
        min_wave_strength=0.3,
    )
    prepared = strategy.prepare(df)
    signal = strategy.generate_signal(prepared)

    assert signal is not None
    assert isinstance(signal, Signal)
    assert signal.side in ("long", "short")
    assert 0.0 <= signal.strength <= 1.0
    assert signal.stop_loss != signal.entry_price


def test_no_signal_when_quiet():
    df = make_sample_df()
    # Remove the forced breakout
    df.loc[df.index[-1], "volume"] = df["volume"].mean()
    df.loc[df.index[-1], "high"] = df["high"].iloc[-20:-1].max() - 0.5
    df.loc[df.index[-1], "close"] = df["close"].iloc[-2]

    strategy = EarlyWaveStrategy(lookback=20, volume_multiplier=2.5, min_wave_strength=0.8)
    prepared = strategy.prepare(df)
    signal = strategy.generate_signal(prepared)

    assert signal is None

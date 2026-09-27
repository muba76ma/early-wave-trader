import numpy as np
import pandas as pd
from scipy.signal import find_peaks

def find_swings(df: pd.DataFrame, order: int = 5):
    highs, _ = find_peaks(df["high"].values, distance=order)
    lows, _ = find_peaks(-df["low"].values, distance=order)
    return highs, lows

def score_early_wave(df: pd.DataFrame) -> float:
    if len(df) < 50:
        return 0.0
    highs, lows = find_swings(df, order=5)
    if len(highs) < 2 or len(lows) < 2:
        return 0.0
    last_high = highs[-1]
    last_low = lows[-1]
    prev_high = highs[-2]
    prev_low = lows[-2]
    recent = df.iloc[-20:]
    momentum = (recent["close"].iloc[-1] - recent["close"].iloc[0]) / recent["close"].iloc[0]
    vol_ratio = recent["volume"].mean() / df["volume"].rolling(50).mean().iloc[-1]
    score = 0.0
    if last_high > prev_high and last_low > prev_low:
        score += 0.4
    if momentum > 0.01:
        score += 0.3
    if vol_ratio > 1.2:
        score += 0.3
    return min(max(score, 0.0), 1.0)

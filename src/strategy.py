from src.config import MIN_SCORE, RISK_PER_TRADE
from src.wave import score_early_wave

def generate_signal(df):
    score = score_early_wave(df)
    if score >= MIN_SCORE:
        return {
            "side": "buy",
            "score": score,
            "risk": RISK_PER_TRADE,
            "reason": f"Early wave score {score:.2f}",
        }
    return None

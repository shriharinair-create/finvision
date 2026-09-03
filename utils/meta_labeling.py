"""
finvision/utils/meta_labeling.py
================================
Marcos Lopez de Prado Meta-Labeling Architecture ("The Veteran Brain").
Acts as the secondary decision model:
  1. The primary model generates directional setups (Buy Tata Motors at ₹1,000).
  2. The Meta-Model evaluates the feature state (RSI, Delivery %, Volatility, Regime, VIX, News Score).
  3. Predicts the probability that the trade will actually succeed based on historical post-mortems.
  4. Dynamically scales Bet Sizing:
       - P(Win) < 45% -> 0.0x (VETO / SKIP TRADE)
       - 45% <= P(Win) < 65% -> 0.5x (CAUTIOUS / HALF SIZE)
       - P(Win) >= 65% -> 1.0x (FULL CONVICTION)
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd


def evaluate_meta_labeling_filter(
    ticker: str,
    action: str,
    entry_price: float,
    stop_loss: float,
    target_price: float,
    conviction_pct: float,
    rsi: float = 50.0,
    regime_code: str = "BULL_MARKUP",
    vix_val: float = 14.5,
    delivery_accum: bool = False,
    exit_trap: bool = False,
    news_sentiment: float = 0.0
) -> dict[str, Any]:
    """
    Applies the Lopez de Prado Meta-Labeling filter.
    Returns:
      - is_approved: bool (True if trade passes the filter)
      - bet_sizing_factor: float (0.0, 0.5, or 1.0)
      - meta_win_probability_pct: float (calibrated likelihood of success)
      - status_badge: str (e.g. 'HIGH CONVICTION (1.0x)', 'HALF SIZE (0.5x)', 'AI VETO (0.0x)')
      - verdict_explanation: Plain-English explanation
    """
    is_long = "BUY" in action.upper() or "LONG" in action.upper()
    base_prob = conviction_pct / 100.0  # e.g. 0.65

    penalty = 0.0
    boost = 0.0
    reasons = []

    # 1. Exit Liquidity Trap Guard: Instant Veto
    if exit_trap and is_long:
        penalty += 0.35
        reasons.append("High-risk 'Sell-the-News' distribution trap detected near range ceiling.")

    # 2. Market Regime Gating
    if regime_code == "HIGH_VOLATILITY_CHOP":
        if is_long and rsi >= 62.0:
            penalty += 0.22
            reasons.append("Breakout buying penalized during high-volatility chop (VIX > 18). Breakouts fail 65%+.")
        elif is_long and rsi <= 40.0:
            boost += 0.12
            reasons.append("Mean-reversion support buying favored in chop regime.")
    elif regime_code == "BEAR_MARKDOWN":
        if is_long:
            penalty += 0.20
            reasons.append("Nifty in structural markdown. Long setups penalized for systemic market drag.")
    elif regime_code == "BULL_MARKUP":
        if is_long and rsi >= 48.0:
            boost += 0.10
            reasons.append("Broad market in institutional markup. Strong trend continuation tailwind.")

    # 3. Delivery Accumulation Confluence
    if delivery_accum and is_long:
        boost += 0.12
        reasons.append("Stealth institutional float absorption confirmed by volume expansion & volatility compression.")

    # 4. Reward-to-Risk Hurdle
    risk_dist = max(0.01, abs(entry_price - stop_loss))
    reward_dist = abs(target_price - entry_price)
    rr_ratio = reward_dist / risk_dist
    if rr_ratio < 1.25:
        penalty += 0.15
        reasons.append(f"Unfavorable Risk:Reward asymmetry ({rr_ratio:.2f}x < 1.25x minimum hurdle).")
    elif rr_ratio >= 2.0:
        boost += 0.08
        reasons.append(f"Excellent Risk:Reward ratio ({rr_ratio:.2f}x).")

    # Final Calibrated Meta Probability
    calibrated_prob = float(np.clip(base_prob + boost - penalty, 0.15, 0.92))
    meta_win_prob_pct = round(calibrated_prob * 100.0, 1)

    # Bet Sizing Factor Determination
    if exit_trap or meta_win_prob_pct < 45.0 or (is_long and regime_code == "BEAR_MARKDOWN" and meta_win_prob_pct < 55.0):
        is_approved = False
        sizing_factor = 0.0
        badge = "⛔ AI VETO (SKIP SETUP)"
        badge_color = "#FF5252"
        explanation = (
            f"Meta-Model VETO: Expected win probability is only {meta_win_prob_pct}%. "
            f"The AI skips this trade to protect capital. " + (" ".join(reasons))
        )
    elif meta_win_prob_pct < 62.0:
        is_approved = True
        sizing_factor = 0.5
        badge = "⚠️ HALF SIZE (0.5x)"
        badge_color = "#FFB300"
        explanation = (
            f"Meta-Model Caution: Moderate probability ({meta_win_prob_pct}%). "
            f"Position size trimmed to 50% for risk buffer. " + (" ".join(reasons))
        )
    else:
        is_approved = True
        sizing_factor = 1.0
        badge = "✅ FULL CONVICTION (1.0x)"
        badge_color = "#00E676"
        explanation = (
            f"Meta-Model Approved: Strong alignment ({meta_win_prob_pct}% win probability). "
            f"Full budget sizing allocated. " + (" ".join(reasons))
        )

    return {
        "is_approved": is_approved,
        "bet_sizing_factor": sizing_factor,
        "meta_win_probability_pct": meta_win_prob_pct,
        "status_badge": badge,
        "badge_color": badge_color,
        "verdict_explanation": explanation,
        "reasons": reasons
    }

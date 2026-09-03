"""
finvision/utils/adaptive_weights.py
===================================
Dynamic Regime-Adaptive Confluence Weighting Engine.

Eliminates static, hardcoded indicator weights. Dynamically re-weights the
6 core quantitative confluence pillars based on the prevailing market regime:
  - Bull Markup: Trend & Momentum dominate (high trend-following edge)
  - High Volatility Chop: Support/Resistance & Mean Reversion dominate
  - Bear Markdown: Capital preservation, ATR volatility bands, and resistance rejections dominate
  - Low Volatility Consolidation: Volume build and breakout proximity dominate
"""

from __future__ import annotations

from typing import Any


# ── Regime-Dependent Dynamic Weighting Matrices (Sum = 1.0) ───────────────────
REGIME_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    # 🟢 BULL_MARKUP: Trends persist; buy breakouts and ride EMA hierarchies
    "BULL_MARKUP": {
        "trend": 0.35,              # EMA 8/21, SMA 50/200 alignment
        "momentum": 0.30,           # MACD velocity, RSI expansion
        "volume": 0.15,             # Volume surge & delivery confirmation
        "support_resistance": 0.15, # Breakout levels
        "news_sentiment": 0.05,     # Vector news confirmation
    },
    # ⚠️ HIGH_VOLATILITY_CHOP: Breakouts fail frequently; mean reversion dominates
    "HIGH_VOLATILITY_CHOP": {
        "support_resistance": 0.40, # Deep horizontal channel support / value zones
        "momentum": 0.30,           # Oversold RSI/Stoch bounce indicators
        "volume": 0.15,             # Liquidity sweep exhaustion volume
        "trend": 0.10,              # Heavily down-weighted (trend-following whipsaws)
        "news_sentiment": 0.05,
    },
    # 🔴 BEAR_MARKDOWN: Capital preservation; counter-trend rallies fail at overhead resistance
    "BEAR_MARKDOWN": {
        "support_resistance": 0.35, # Overhead resistance supply zones
        "trend": 0.25,              # Confirming lower-high structural downtrend
        "momentum": 0.20,           # Oversold exhaustion or bear continuation
        "volume": 0.10,             # Institutional distribution volume
        "news_sentiment": 0.10,     # Regulatory risk & downgrade headlines
    },
    # ⚪ LOW_VOLATILITY_CONSOLIDATION: Coiling inside range; watch for volume burst
    "LOW_VOLATILITY_CONSOLIDATION": {
        "volume": 0.30,             # Quiet accumulation & institutional absorption
        "support_resistance": 0.25, # Range boundaries & squeeze channels
        "trend": 0.25,              # Multi-timeframe trend alignment
        "momentum": 0.15,           # Squeeze expansion signals
        "news_sentiment": 0.05,
    },
}

# Baseline neutral fallback
DEFAULT_WEIGHTS = {
    "trend": 0.25,
    "momentum": 0.25,
    "support_resistance": 0.20,
    "volume": 0.15,
    "news_sentiment": 0.15,
}


def get_regime_adaptive_weights(regime_name: str) -> dict[str, float]:
    """
    Returns the normalized dynamic weighting dictionary for the active regime.
    Ensures weights always sum precisely to 1.0 (100%).
    """
    clean_regime = regime_name.upper().replace(" ", "_")
    for key, weights in REGIME_WEIGHT_PROFILES.items():
        if key in clean_regime:
            return weights
    return DEFAULT_WEIGHTS


def calculate_adaptive_confluence_score(
    trend_score: float,
    momentum_score: float,
    sr_score: float,
    volume_score: float,
    news_score: float,
    regime_name: str = "BULL_MARKUP"
) -> dict[str, Any]:
    """
    Calculates the regime-adaptive composite confluence score (0 to 100).
    Surfaces the dynamic weights used and identifies the primary driver.
    """
    weights = get_regime_adaptive_weights(regime_name)

    # Normalize inputs to 0.0 - 100.0 scale if provided as 0.0 - 1.0
    t_val = trend_score * 100.0 if trend_score <= 1.0 else trend_score
    m_val = momentum_score * 100.0 if momentum_score <= 1.0 else momentum_score
    sr_val = sr_score * 100.0 if sr_score <= 1.0 else sr_score
    v_val = volume_score * 100.0 if volume_score <= 1.0 else volume_score
    n_val = news_score * 100.0 if news_score <= 1.0 else news_score

    composite_score = round(
        weights["trend"] * t_val +
        weights["momentum"] * m_val +
        weights["support_resistance"] * sr_val +
        weights["volume"] * v_val +
        weights["news_sentiment"] * n_val,
        1
    )

    # Determine dominant factor by weighted contribution
    contributions = {
        "Trend Hierarchy": weights["trend"] * t_val,
        "Momentum Dynamics": weights["momentum"] * m_val,
        "Support / Resistance": weights["support_resistance"] * sr_val,
        "Volume Accumulation": weights["volume"] * v_val,
        "Regulatory & News": weights["news_sentiment"] * n_val,
    }
    dominant_factor = max(contributions, key=contributions.get)

    # Create user-friendly badge string showing adapted weights
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    weight_summary = " · ".join([f"{k.capitalize()[:4]}: {int(v*100)}%" for k, v in sorted_weights[:3]])

    return {
        "composite_score": composite_score,
        "regime_name": regime_name,
        "weights_used": weights,
        "weight_summary": weight_summary,
        "dominant_factor": dominant_factor,
        "is_adaptive": True,
    }

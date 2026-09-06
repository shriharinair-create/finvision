"""
finvision/utils/adaptive_weights.py
===================================
Dynamic Regime-Adaptive Confluence Weighting Engine (Single Source of Truth).

Eliminates static, hardcoded indicator weights and duplicate weighting engines.
Dynamically re-weights the core quantitative confluence pillars based on the
prevailing market regime:
  - Bull Markup: Trend & Momentum dominate (high trend-following edge)
  - High Volatility Chop: Support/Resistance & Mean Reversion dominate
  - Bear Markdown: Capital preservation, ATR volatility bands, and resistance rejections dominate
  - Low Volatility Consolidation: Volume build and breakout proximity dominate
"""

from __future__ import annotations

from typing import Any


# Canonical Baseline Regime Weighting Priors (Heuristic starting points before empirical fitting)
STATIC_REGIME_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    # 🟢 BULL_MARKUP: Trends persist; buy breakouts and ride EMA hierarchies
    "BULL_MARKUP": {
        "trend": 0.35,              # EMA 8/21, SMA 50/200 alignment
        "momentum": 0.25,           # MACD velocity, RSI expansion
        "volume": 0.15,             # Volume surge & delivery confirmation
        "support_resistance": 0.10, # Breakout levels
        "regime": 0.10,             # Benchmark beta & market tailwind
        "news_sentiment": 0.05,     # Vector news confirmation
    },
    # ⚠️ HIGH_VOLATILITY_CHOP: Breakouts fail frequently; mean reversion dominates
    "HIGH_VOLATILITY_CHOP": {
        "trend": 0.10,              # Heavily down-weighted (trend-following whipsaws)
        "momentum": 0.30,           # Oversold RSI/Stoch bounce indicators
        "support_resistance": 0.25, # Deep horizontal channel support / value zones
        "volume": 0.15,             # Liquidity sweep exhaustion volume
        "regime": 0.15,             # Regime sensitivity
        "news_sentiment": 0.05,
    },
    # 🔴 BEAR_MARKDOWN: Capital preservation; counter-trend rallies fail at overhead resistance
    "BEAR_MARKDOWN": {
        "support_resistance": 0.25, # Overhead resistance supply zones
        "trend": 0.15,              # Confirming lower-high structural downtrend
        "momentum": 0.15,           # Oversold exhaustion or bear continuation
        "volume": 0.10,             # Institutional distribution volume
        "regime": 0.25,             # Market systemic drag & macro headwinds
        "news_sentiment": 0.10,     # Regulatory risk & downgrade headlines
    },
    # ⚪ QUIET_ACCUMULATION / LOW_VOLATILITY_CONSOLIDATION: Coiling inside range; watch for volume burst
    "QUIET_ACCUMULATION": {
        "volume": 0.25,             # Quiet accumulation & institutional absorption
        "support_resistance": 0.25, # Range boundaries & squeeze channels
        "trend": 0.20,              # Multi-timeframe trend alignment
        "momentum": 0.15,           # Squeeze expansion signals
        "regime": 0.10,             # General market context
        "news_sentiment": 0.05,
    },
    "LOW_VOLATILITY_CONSOLIDATION": {
        "volume": 0.25,
        "support_resistance": 0.25,
        "trend": 0.20,
        "momentum": 0.15,
        "regime": 0.10,
        "news_sentiment": 0.05,
    },
    # 🔵 NORMAL_BALANCED: Balanced consolidation around key EMAs
    "NORMAL_BALANCED": {
        "trend": 0.25,
        "momentum": 0.25,
        "support_resistance": 0.20,
        "volume": 0.15,
        "regime": 0.10,
        "news_sentiment": 0.05,
    },
    # 🛡️ DATA_UNAVAILABLE: Defensive capital preservation weights
    "DATA_UNAVAILABLE": {
        "trend": 0.10,
        "momentum": 0.10,
        "support_resistance": 0.35,
        "volume": 0.15,
        "regime": 0.25,
        "news_sentiment": 0.05,
    },
}

REGIME_WEIGHT_PROFILES = STATIC_REGIME_WEIGHT_PROFILES

# Baseline neutral fallback
DEFAULT_WEIGHTS: dict[str, float] = {
    "trend": 0.25,
    "momentum": 0.25,
    "support_resistance": 0.15,
    "volume": 0.15,
    "regime": 0.10,
    "news_sentiment": 0.10,
}


def get_regime_adaptive_weights(regime_name: str) -> dict[str, float]:
    """
    Returns the normalized dynamic weighting dictionary for the active regime.
    Ensures weights always sum precisely to 1.0 (100%).
    """
    clean_regime = regime_name.upper().replace(" ", "_")
    if clean_regime in REGIME_WEIGHT_PROFILES:
        return REGIME_WEIGHT_PROFILES[clean_regime]
    for key, weights in REGIME_WEIGHT_PROFILES.items():
        if key in clean_regime:
            return weights
    return DEFAULT_WEIGHTS


def get_forecasting_regime_weights(
    regime_score: float,
    catalyst_intensity: float = 0.0
) -> dict[str, Any]:
    """
    Unified Single Source of Truth for Quantitative Confluence Forecasting.
    Maps quantitative regime_score to the canonical REGIME_WEIGHT_PROFILES,
    dynamically scaling news/catalyst weighting and returning:
      - w_trend: float
      - w_mom: float
      - w_flow: float (volume + support_resistance combined)
      - w_regime: float
      - w_news: float
      - regime_label: str
      - base_regime: str
    """
    if regime_score > 0.20:
        base_regime = "BULL_MARKUP"
        regime_label = "Trending Expansion (Markup)"
    elif regime_score < -0.20:
        base_regime = "BEAR_MARKDOWN"
        regime_label = "Bear Correction (Defensive Markdown)"
    else:
        base_regime = "LOW_VOLATILITY_CONSOLIDATION"
        regime_label = "Consolidation Range (Mean-Reverting)"

    profile = get_regime_adaptive_weights(base_regime)

    # Catalyst dynamic allocation
    if catalyst_intensity >= 0.25:
        w_news = min(0.35, 0.18 + 0.25 * (catalyst_intensity - 0.20))
        w_core = 1.0 - w_news
    else:
        w_news = profile.get("news_sentiment", 0.08)
        w_core = 1.0 - w_news

    # Core weights scaled to remaining core budget
    core_sum = (
        profile.get("trend", 0.25) +
        profile.get("momentum", 0.25) +
        profile.get("volume", 0.15) +
        profile.get("support_resistance", 0.15) +
        profile.get("regime", 0.12)
    )
    scale = w_core / (core_sum if core_sum > 0 else 1.0)

    w_trend = profile.get("trend", 0.25) * scale
    w_mom = profile.get("momentum", 0.25) * scale
    w_flow = (profile.get("volume", 0.15) + profile.get("support_resistance", 0.15)) * scale
    w_regime = profile.get("regime", 0.12) * scale

    return {
        "w_trend": float(w_trend),
        "w_mom": float(w_mom),
        "w_flow": float(w_flow),
        "w_regime": float(w_regime),
        "w_news": float(w_news),
        "regime_label": regime_label,
        "base_regime": base_regime,
        "raw_profile": profile,
    }


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
    Ensures weights used sum precisely to 1.0 across the 5 input pillars.
    """
    weights = get_regime_adaptive_weights(regime_name)

    # Normalize inputs to 0.0 - 100.0 scale if provided as 0.0 - 1.0
    t_val = trend_score * 100.0 if trend_score <= 1.0 else trend_score
    m_val = momentum_score * 100.0 if momentum_score <= 1.0 else momentum_score
    sr_val = sr_score * 100.0 if sr_score <= 1.0 else sr_score
    v_val = volume_score * 100.0 if volume_score <= 1.0 else volume_score
    n_val = news_score * 100.0 if news_score <= 1.0 else news_score

    # Normalize 5 pillars used in mode0 to sum to 1.0
    mode0_sum = (
        weights.get("trend", 0.25) +
        weights.get("momentum", 0.25) +
        weights.get("support_resistance", 0.15) +
        weights.get("volume", 0.15) +
        weights.get("news_sentiment", 0.08)
    )
    scale = 1.0 / (mode0_sum if mode0_sum > 0 else 1.0)
    w_t = weights.get("trend", 0.25) * scale
    w_m = weights.get("momentum", 0.25) * scale
    w_sr = weights.get("support_resistance", 0.15) * scale
    w_v = weights.get("volume", 0.15) * scale
    w_n = weights.get("news_sentiment", 0.08) * scale

    composite_score = round(
        w_t * t_val +
        w_m * m_val +
        w_sr * sr_val +
        w_v * v_val +
        w_n * n_val,
        1
    )

    # Determine dominant factor by weighted contribution
    contributions = {
        "Trend Hierarchy": w_t * t_val,
        "Momentum Dynamics": w_m * m_val,
        "Support / Resistance": w_sr * sr_val,
        "Volume Accumulation": w_v * v_val,
        "Regulatory & News": w_n * n_val,
    }
    dominant_factor = max(contributions, key=contributions.get)

    display_weights = {
        "trend": w_t,
        "momentum": w_m,
        "support_resistance": w_sr,
        "volume": w_v,
        "news_sentiment": w_n,
    }

    # Create user-friendly badge string showing adapted weights
    sorted_weights = sorted(display_weights.items(), key=lambda x: x[1], reverse=True)
    weight_summary = " · ".join([f"{k.capitalize()[:4]}: {int(v*100)}%" for k, v in sorted_weights[:3]])

    return {
        "composite_score": composite_score,
        "regime_name": regime_name,
        "weights_used": display_weights,
        "weight_summary": weight_summary,
        "dominant_factor": dominant_factor,
        "is_adaptive": True,
    }


def fit_regime_weights_from_history(
    pillar_scores: list[dict[str, float]],
    forward_returns: list[float],
    min_samples: int = 100,
) -> dict[str, float] | None:
    """
    Fits empirical pillar weights from historical realized returns via regularized non-negative Ridge regression.
    Requires at least 100 observations; falls back to static prior profiles if sample size is insufficient (Finding 10).
    """
    if len(pillar_scores) < min_samples or len(pillar_scores) != len(forward_returns):
        return None

    try:
        import numpy as np
        import pandas as pd
        from sklearn.linear_model import Ridge

        df_pillars = pd.DataFrame(pillar_scores)
        y = np.array(forward_returns)
        
        # Ridge with positive coefficients constraint
        model = Ridge(alpha=1.0, positive=True).fit(df_pillars, y)
        raw_weights = np.clip(model.coef_, 0.0, None)
        
        if raw_weights.sum() <= 0:
            return None
            
        normalized_weights = raw_weights / raw_weights.sum()
        return dict(zip(df_pillars.columns, [round(float(w), 3) for w in normalized_weights]))
    except Exception:
        return None

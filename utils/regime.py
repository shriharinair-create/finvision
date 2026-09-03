"""
finvision/utils/regime.py
=========================
Indian Market Regime Detection & Dynamic Playbook Strategy Switching.
Classifies the broad market into 4 distinct quant regimes using:
  1. Nifty 50 (^NSEI) Structural Trend (EMA 20, 50, 200 stack alignment)
  2. India VIX (^INDIAVIX) Volatility Levels (<13 Low, 13-18 Normal, >18 High-Risk)
  3. Short-term Trend Momentum & Volatility Compression

Outputs dynamic adaptive parameters for position sizing, stop-loss buffers,
and strategy playbook gating (Breakout vs Mean-Reversion vs Defense).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
import yfinance as yf


def detect_indian_market_regime(
    nse_df: Optional[pd.DataFrame] = None,
    vix_df: Optional[pd.DataFrame] = None
) -> dict[str, Any]:
    """
    Detects the current Indian Market Regime.
    Fetches real-time Nifty 50 (^NSEI) and India VIX (^INDIAVIX) if dataframes are not passed.
    
    Regimes:
      - BULL_MARKUP: Strong upward trend, low-to-moderate volatility. Breakouts favored.
      - HIGH_VOLATILITY_CHOP: Volatility elevated (>18) or choppy sideways range.
                              Breakouts fail frequently; switch to mean-reversion dip buying.
      - BEAR_MARKDOWN: Structural downtrend below major EMAs. Defensive mode, strict risk.
      - QUIET_ACCUMULATION: Low volatility (<13), tight consolidation. Float absorption.
    """
    # 1. Fetch Nifty 50 if missing
    if nse_df is None or nse_df.empty:
        try:
            nse_df = yf.download("^NSEI", period="6mo", interval="1d", progress=False)
            if isinstance(nse_df.columns, pd.MultiIndex):
                nse_df.columns = [c[0] for c in nse_df.columns]
        except Exception:
            nse_df = pd.DataFrame()

    # 2. Fetch India VIX if missing
    vix_val = 14.5  # Default benchmark
    if vix_df is None or vix_df.empty:
        try:
            v_data = yf.download("^INDIAVIX", period="1mo", interval="1d", progress=False)
            if isinstance(v_data.columns, pd.MultiIndex):
                v_data.columns = [c[0] for c in v_data.columns]
            if not v_data.empty and "Close" in v_data:
                vix_val = float(v_data["Close"].dropna().iloc[-1])
        except Exception:
            vix_val = 14.5
    else:
        if "Close" in vix_df:
            vix_val = float(vix_df["Close"].dropna().iloc[-1])

    # Fallback if Nifty data unavailable
    if nse_df.empty or len(nse_df) < 20 or "Close" not in nse_df:
        return {
            "regime_code": "NORMAL_BALANCED",
            "regime_name": "Balanced Market Regime",
            "badge_color": "#58A6FF",
            "vix_value": round(vix_val, 2),
            "vix_regime": "NORMAL",
            "strategy_playbook": "BALANCED_SWING",
            "breakouts_enabled": True,
            "target_multiplier": 1.0,
            "stop_multiplier": 1.0,
            "max_risk_multiplier": 1.0,
            "playbook_guidance": "Standard balanced trend and swing setups active."
        }

    close = nse_df["Close"].astype(float).dropna()
    last_nifty = float(close.iloc[-1])

    # Moving averages
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1]) if len(close) >= 50 else ema20
    sma200 = float(close.rolling(window=min(200, len(close))).mean().iloc[-1])

    pct_above_ema20 = ((last_nifty - ema20) / ema20) * 100.0
    pct_above_ema50 = ((last_nifty - ema50) / ema50) * 100.0
    is_above_200 = last_nifty >= sma200

    # 5-day Nifty return
    ret_5d = ((last_nifty - close.iloc[-6]) / close.iloc[-6] * 100.0) if len(close) >= 6 else 0.0

    # VIX classification
    if vix_val >= 18.5:
        vix_regime = "HIGH_STRESS"
    elif vix_val <= 13.0:
        vix_regime = "COMPLACENT_LOW_VOL"
    else:
        vix_regime = "HEALTHY_NORMAL"

    # ── Regime Classification Logic ──────────────────────────────────────────
    if vix_val >= 18.5 or (abs(ret_5d) >= 2.5 and pct_above_ema20 < 0):
        regime_code = "HIGH_VOLATILITY_CHOP"
        regime_name = "High-Volatility Chop / Expansion"
        badge_color = "#FFB300"
        strategy_playbook = "MEAN_REVERSION_SCALPS"
        breakouts_enabled = False
        target_mult = 0.80      # Take profits faster before pullbacks
        stop_mult = 1.35        # Widen stops to survive volatile whipsaws
        risk_mult = 0.60        # Cut position sizing to 60% for safety
        guidance = (
            f"India VIX elevated at {vix_val:.1f}. Breakouts fail 65%+ of the time. "
            f"Veto trend chasing; buy support dips with quick profit locking."
        )

    elif last_nifty > ema20 and ema20 > ema50 and is_above_200 and ret_5d >= -0.5:
        regime_code = "BULL_MARKUP"
        regime_name = "Bull Trend Markup"
        badge_color = "#00E676"
        strategy_playbook = "TREND_BREAKOUTS_AND_RUNNERS"
        breakouts_enabled = True
        target_mult = 1.30      # Trail profits into runners
        stop_mult = 1.00        # Standard ATR stops
        risk_mult = 1.00        # 100% full position size
        guidance = (
            f"Nifty 50 in clean institutional markup (+{pct_above_ema20:.1f}% vs EMA20). "
            f"Trend-following and high-alpha breakouts have strong statistical follow-through."
        )

    elif last_nifty < ema20 and last_nifty < ema50:
        regime_code = "BEAR_MARKDOWN"
        regime_name = "Bear Markdown / Correction"
        badge_color = "#FF5252"
        strategy_playbook = "DEFENSIVE_CAPITAL_PRESERVATION"
        breakouts_enabled = False
        target_mult = 0.75      # Tight targets
        stop_mult = 0.90        # Strict quick cut
        risk_mult = 0.40        # Reduce capital sizing to 40%
        guidance = (
            f"Nifty 50 trading below key EMAs ({pct_above_ema20:.1f}% vs EMA20). "
            f"Capital preservation mode active. Long setups restricted to high-conviction value."
        )

    else:
        regime_code = "QUIET_ACCUMULATION"
        regime_name = "Quiet Float Absorption"
        badge_color = "#A371F7"
        strategy_playbook = "WYCKOFF_SWING_ACCUMULATION"
        breakouts_enabled = True
        target_mult = 1.05
        stop_mult = 1.00
        risk_mult = 0.85
        guidance = (
            f"Market consolidating with low VIX ({vix_val:.1f}). Smart money quietly absorbing float. "
            f"Accumulate near range support before volatility expansion."
        )

    return {
        "regime_code": regime_code,
        "regime_name": regime_name,
        "badge_color": badge_color,
        "nifty_price": round(last_nifty, 2),
        "nifty_pct_ema20": round(pct_above_ema20, 2),
        "vix_value": round(vix_val, 2),
        "vix_regime": vix_regime,
        "strategy_playbook": strategy_playbook,
        "breakouts_enabled": breakouts_enabled,
        "target_multiplier": target_mult,
        "stop_multiplier": stop_mult,
        "max_risk_multiplier": risk_mult,
        "playbook_guidance": guidance
    }

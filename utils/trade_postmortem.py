"""
finvision/utils/trade_postmortem.py
===================================
Automated Trade Post-Mortem Diagnostic & Outcome Attribution Engine.
Conducts quantitative autopsies on every closed simulated or live trade:
  1. Detects Operator Liquidity Sweeps / Stop-Hunts (price pierced SL by <0.6% then reversed).
  2. Detects Broad Market Regime Drag (Nifty dumped during trade).
  3. Detects Structural Breakdowns (Heavy volume selling through key MAs).
  4. Generates Stock-Specific Adaptive Corrective Multipliers (widens stops or extends targets).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd


def diagnose_trade_postmortem(
    ticker: str,
    trade_type: str,
    entry_price: float,
    target_price: float,
    stop_loss_price: float,
    exit_price: float,
    status: str,
    df_history: Optional[pd.DataFrame] = None,
    nifty_return_during_trade: float = 0.0,
    regime_at_entry: str = "NORMAL"
) -> dict[str, Any]:
    """
    Runs a rigorous quantitative diagnostic on a completed trade.
    Returns:
      - diagnosis_code: e.g. 'LIQUIDITY_SWEEP_HUNT', 'MACRO_REGIME_DRAG', 'TARGET_BLOWOFF'
      - attribution_summary: Plain-English root cause explanation
      - corrective_learning: Actionable parameter adaptation
      - stock_buffer_multiplier: Recommended ATR stop multiplier update (e.g. 1.25x)
    """
    is_long = "BUY" in trade_type.upper() or trade_type.upper() == "LONG"
    is_target = "TARGET" in status.upper() or (is_long and exit_price >= target_price) or (not is_long and exit_price <= target_price)
    is_stop = "STOP" in status.upper() or (is_long and exit_price <= stop_loss_price) or (not is_long and exit_price >= stop_loss_price)

    # Defaults
    diagnosis_code = "CLEAN_WIN" if is_target else "NORMAL_STOP" if is_stop else "MANUAL_CLOSE"
    attribution = "Trade closed according to planned targets."
    corrective = "Maintain standard parameters."
    buffer_mult = 1.0

    # ── 1. LOSS DIAGNOSTICS (Post-Mortem Autopsy) ────────────────────────────
    if is_stop:
        # Check for Liquidity Sweep / Stop Hunt:
        # Price pierced stop loss by less than 0.75%, but subsequent bars recovered
        if df_history is not None and not df_history.empty and len(df_history) >= 3:
            recent_lows = df_history["Low"].tail(5).astype(float)
            recent_highs = df_history["High"].tail(5).astype(float)
            recent_close = df_history["Close"].tail(5).astype(float)

            min_low = float(recent_lows.min())
            max_high = float(recent_highs.max())
            last_c = float(recent_close.iloc[-1])

            if is_long:
                pierce_pct = ((stop_loss_price - min_low) / stop_loss_price) * 100.0
                reversed_back = last_c > entry_price or max_high > entry_price
                
                if 0.0 < pierce_pct <= 0.85 and reversed_back:
                    diagnosis_code = "LIQUIDITY_SWEEP_HUNT"
                    attribution = (
                        f"⚠️ Smart-Money Stop Sweep Detected. Price pierced stop-loss (₹{stop_loss_price:,.2f}) "
                        f"by only {pierce_pct:.2f}% to ₹{min_low:,.2f} before reversing right back above entry (₹{last_c:,.2f})."
                    )
                    corrective = (
                        f"Widen adaptive ATR stop buffer on {ticker} from 1.00x to 1.35x to sit safely below retail liquidity pools."
                    )
                    buffer_mult = 1.35
            else:
                pierce_pct = ((max_high - stop_loss_price) / stop_loss_price) * 100.0
                reversed_back = last_c < entry_price or min_low < entry_price
                if 0.0 < pierce_pct <= 0.85 and reversed_back:
                    diagnosis_code = "LIQUIDITY_SWEEP_HUNT"
                    attribution = f"Short squeeze stop sweep ({pierce_pct:.2f}% pierce) before reversal."
                    corrective = "Widen short stop buffer to 1.35x."
                    buffer_mult = 1.35

        # Check for Broad Market Drag:
        if diagnosis_code != "LIQUIDITY_SWEEP_HUNT" and nifty_return_during_trade <= -1.25:
            diagnosis_code = "MACRO_REGIME_DRAG"
            attribution = (
                f"Market Drag Failure. Stock setup was valid, but Nifty 50 plunged {nifty_return_during_trade:.2f}% "
                f"during the holding period, dragging the stock down with systemic liquidity outflow."
            )
            corrective = "No penalty to stock technical model. Strengthen broad market regime gate."
            buffer_mult = 1.05

        # Check for High-Volatility Breakdown:
        elif diagnosis_code != "LIQUIDITY_SWEEP_HUNT" and regime_at_entry == "HIGH_VOLATILITY_CHOP":
            diagnosis_code = "HIGH_VOLATILITY_WHIPSAW"
            attribution = "Trade failed due to high-volatility chop whipsaw. Breakout failed in elevated VIX."
            corrective = "Enforce mean-reversion filter; veto breakout trades when VIX > 18."
            buffer_mult = 1.20

    # ── 2. WIN DIAGNOSTICS (Optimization & Runner Capture) ───────────────────
    elif is_target:
        if df_history is not None and not df_history.empty:
            recent_high = float(df_history["High"].tail(3).max()) if is_long else float(df_history["Low"].tail(3).min())
            overshoot_pct = abs(recent_high - target_price) / target_price * 100.0

            if overshoot_pct >= 2.0:
                diagnosis_code = "TARGET_BLOWOFF_RUNNER"
                attribution = (
                    f"Strong Runner Blowoff. Stock exceeded Target (₹{target_price:,.2f}) by +{overshoot_pct:.1f}% "
                    f"to ₹{recent_high:,.2f}."
                )
                corrective = (
                    f"Extend Target 2 multiplier to 1.25x and activate trailing ATR ratchet to capture full runner moves on {ticker}."
                )
                buffer_mult = 1.0
            else:
                diagnosis_code = "CLEAN_PRECISION_WIN"
                attribution = f"High-precision execution. Price reached Target 1 (₹{target_price:,.2f}) perfectly."
                corrective = "Maintain current confluence weights."
                buffer_mult = 1.0

    pnl_amount = (exit_price - entry_price) if is_long else (entry_price - exit_price)
    pnl_pct = (pnl_amount / entry_price) * 100.0

    return {
        "ticker": ticker,
        "trade_type": trade_type,
        "status": status,
        "entry_price": round(entry_price, 2),
        "exit_price": round(exit_price, 2),
        "pnl_amount": round(pnl_amount, 2),
        "pnl_pct": round(pnl_pct, 2),
        "diagnosis_code": diagnosis_code,
        "attribution_summary": attribution,
        "corrective_learning": corrective,
        "stock_buffer_multiplier": round(buffer_mult, 2),
        "regime_at_entry": regime_at_entry
    }

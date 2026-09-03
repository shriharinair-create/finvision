"""
Risk management utilities: position sizing and broad-market regime gating.

These were the two genuinely useful ideas in the Gemini-generated app:
  1. Position sizing from a risk-tolerance % and stop distance, so the user
     gets a concrete share count instead of just price levels.
  2. A broad-market health gate (is the index itself in an uptrend?) so a
     stock's individual setup is read in context, not in isolation.

Both are implemented here defensively — capped, bounds-checked, and with
honest fallbacks when data is unavailable, rather than blowing up or
silently returning nonsense.
"""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st


# ══════════════════════════════════════════════════════════════════════════
# Position sizing
# ══════════════════════════════════════════════════════════════════════════

def compute_position_size(
    total_capital: float,
    risk_pct: float,
    entry_price: float,
    stop_price: float,
    max_position_pct_of_capital: float = 0.25,
) -> dict:
    """
    Computes how many shares to buy given a fixed-fractional risk model:
    risk only `risk_pct` of total capital on this single trade, sized by
    the distance between entry and stop.

    Also caps the position so a single trade can't consume more than
    `max_position_pct_of_capital` of total capital regardless of how tight
    the stop is — a tiny stop on a volatile stock can otherwise produce an
    absurdly large share count that's technically "risk-sized" but
    practically reckless (concentration risk, slippage risk).

    Returns {
        'shares': int,
        'cash_at_risk': float,
        'position_value': float,
        'position_pct_of_capital': float,
        'capped_by_concentration_limit': bool,
        'warning': str | None,
    }
    """
    if total_capital <= 0 or risk_pct <= 0 or entry_price <= 0:
        return {
            "shares": 0, "cash_at_risk": 0.0, "position_value": 0.0,
            "position_pct_of_capital": 0.0, "capped_by_concentration_limit": False,
            "warning": "Invalid inputs — capital, risk %, and entry price must all be positive.",
        }

    per_share_risk = entry_price - stop_price
    if per_share_risk <= 0:
        return {
            "shares": 0, "cash_at_risk": 0.0, "position_value": 0.0,
            "position_pct_of_capital": 0.0, "capped_by_concentration_limit": False,
            "warning": "Stop price must be below entry price for a long position — can't size risk.",
        }

    cash_to_risk = total_capital * risk_pct
    raw_shares = math.floor(cash_to_risk / per_share_risk)

    max_position_value = total_capital * max_position_pct_of_capital
    max_shares_by_concentration = math.floor(max_position_value / entry_price)

    capped = raw_shares > max_shares_by_concentration
    shares = min(raw_shares, max_shares_by_concentration)
    shares = max(0, shares)

    position_value = shares * entry_price
    actual_cash_at_risk = shares * per_share_risk
    position_pct = position_value / total_capital if total_capital > 0 else 0.0

    warning = None
    if capped:
        warning = (
            f"Risk-based sizing suggested {raw_shares:,} shares, but that would put "
            f"{raw_shares*entry_price/total_capital*100:.0f}% of your capital in one "
            f"position. Capped at {max_position_pct_of_capital*100:.0f}% concentration "
            f"limit ({shares:,} shares) — your stop is unusually tight relative to "
            f"this stock's price."
        )
    elif shares == 0:
        warning = "Position sizing rounds to 0 shares — risk budget is too small for this stop distance at this price."

    return {
        "shares": shares,
        "cash_at_risk": round(actual_cash_at_risk, 2),
        "position_value": round(position_value, 2),
        "position_pct_of_capital": round(position_pct * 100, 1),
        "capped_by_concentration_limit": capped,
        "warning": warning,
    }


# ══════════════════════════════════════════════════════════════════════════
# Broad-market regime gate
# ══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800, show_spinner=False)
def check_broad_market_health(index_ticker: str = "^NSEI") -> dict:
    """
    Checks whether the broad market index itself is in a healthy trend,
    using price vs EMA20 as a simple regime filter — the same idea the
    Gemini app used, but with graceful fallback instead of silently
    defaulting to "healthy" on any error (which hides exactly the kind of
    risk this check exists to catch).

    Returns {
        'available': bool,
        'healthy': bool | None,
        'index_price': float | None,
        'index_ema20': float | None,
        'pct_above_ema': float | None,
    }
    """
    try:
        import yfinance as yf
        idx = yf.Ticker(index_ticker)
        df = idx.history(period="60d", interval="1d")
        if df is None or df.empty or len(df) < 20:
            return {
                "available": False, "healthy": None,
                "index_price": None, "index_ema20": None, "pct_above_ema": None,
                "reason": "Insufficient index history returned.",
            }
        close = df["Close"].astype(float)
        price = float(close.iloc[-1])
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        pct_above = (price - ema20) / ema20 * 100
        return {
            "available": True,
            "healthy": price >= ema20,
            "index_price": round(price, 2),
            "index_ema20": round(ema20, 2),
            "pct_above_ema": round(pct_above, 2),
        }
    except Exception as exc:
        return {
            "available": False, "healthy": None,
            "index_price": None, "index_ema20": None, "pct_above_ema": None,
            "reason": f"Could not fetch index data: {exc}",
        }

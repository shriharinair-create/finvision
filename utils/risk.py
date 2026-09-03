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
from typing import Any

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

    per_share_risk = abs(entry_price - stop_price)
    if per_share_risk <= 0.001:
        return {
            "shares": 0, "cash_at_risk": 0.0, "position_value": 0.0,
            "position_pct_of_capital": 0.0, "capped_by_concentration_limit": False,
            "warning": "Stop price must be different from entry price — can't size risk.",
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


# ══════════════════════════════════════════════════════════════════════════
# Institutional Risk: Value-at-Risk (VaR) & Expected Shortfall (CVaR)
# ══════════════════════════════════════════════════════════════════════════

import numpy as np


def compute_institutional_var_cvar(
    returns: pd.Series | list[float] | np.ndarray,
    position_value: float,
    confidence_level: float = 0.95,
    horizon_days: int = 1,
) -> dict[str, Any]:
    """
    Computes institutional tail-risk measures:
      1. Historical Value-at-Risk (VaR): Maximum expected loss at specified confidence level.
      2. Parametric Gaussian VaR: Analytical VaR based on mean and volatility.
      3. Conditional Value-at-Risk (CVaR / Expected Shortfall): Expected loss *if* the
         VaR threshold is breached (answering 'how bad does it get in a tail shock?').

    Returns percentages and absolute Rupee values sized to position_value.
    """
    if position_value <= 0:
        return {
            "available": False,
            "var_95_pct": 0.0, "var_95_inr": 0.0,
            "var_99_pct": 0.0, "var_99_inr": 0.0,
            "cvar_95_pct": 0.0, "cvar_95_inr": 0.0,
            "parametric_var_pct": 0.0, "parametric_var_inr": 0.0,
            "horizon_days": horizon_days,
            "tail_risk_grade": "LOW",
        }

    s = pd.Series(returns).dropna().astype(float)
    # If returns are given in percentage points (e.g. -2.5 rather than -0.025), normalize to decimal
    if not s.empty and s.abs().max() > 1.0:
        s = s / 100.0

    if len(s) < 15:
        # Default proxy based on typical 1.5% daily volatility
        std_proxy = 0.018 * math.sqrt(horizon_days)
        var_95_proxy = std_proxy * 1.645
        var_99_proxy = std_proxy * 2.326
        cvar_proxy = std_proxy * 2.06
        return {
            "available": True,
            "is_proxy": True,
            "var_95_pct": round(var_95_proxy * 100, 2),
            "var_95_inr": round(var_95_proxy * position_value, 2),
            "var_99_pct": round(var_99_proxy * 100, 2),
            "var_99_inr": round(var_99_proxy * position_value, 2),
            "cvar_95_pct": round(cvar_proxy * 100, 2),
            "cvar_95_inr": round(cvar_proxy * position_value, 2),
            "parametric_var_pct": round(var_95_proxy * 100, 2),
            "parametric_var_inr": round(var_95_proxy * position_value, 2),
            "horizon_days": horizon_days,
            "tail_risk_grade": "MODERATE",
        }

    scale = math.sqrt(max(1, horizon_days))

    # 1. Historical 95% & 99% VaR
    var_95_quant = float(np.percentile(s, (1 - 0.95) * 100))
    var_99_quant = float(np.percentile(s, (1 - 0.99) * 100))

    var_95_pct = abs(min(0.0, var_95_quant)) * scale
    var_99_pct = abs(min(0.0, var_99_quant)) * scale

    # 2. Expected Shortfall / CVaR (mean of losses exceeding 95% quantile)
    tail_losses = s[s <= var_95_quant]
    if not tail_losses.empty:
        cvar_quant = float(tail_losses.mean())
    else:
        cvar_quant = var_95_quant * 1.25
    cvar_95_pct = abs(min(0.0, cvar_quant)) * scale

    # 3. Parametric Gaussian VaR
    mu = float(s.mean())
    sigma = float(s.std())
    param_var_pct = abs(min(0.0, (mu - 1.645 * sigma))) * scale

    # Rupee equivalents
    var_95_inr = round(var_95_pct * position_value, 2)
    var_99_inr = round(var_99_pct * position_value, 2)
    cvar_95_inr = round(cvar_95_pct * position_value, 2)
    param_inr = round(param_var_pct * position_value, 2)

    # Tail risk severity grade
    if var_95_pct > 0.035:
        grade = "HIGH_VOLATILITY"
    elif var_95_pct > 0.018:
        grade = "NORMAL_BALANCED"
    else:
        grade = "LOW_TAIL_RISK"

    return {
        "available": True,
        "is_proxy": False,
        "var_95_pct": round(var_95_pct * 100, 2),
        "var_95_inr": var_95_inr,
        "var_99_pct": round(var_99_pct * 100, 2),
        "var_99_inr": var_99_inr,
        "cvar_95_pct": round(cvar_95_pct * 100, 2),
        "cvar_95_inr": cvar_95_inr,
        "parametric_var_pct": round(param_var_pct * 100, 2),
        "parametric_var_inr": param_inr,
        "horizon_days": horizon_days,
        "tail_risk_grade": grade,
    }


def compute_portfolio_stress_test(
    positions: list[dict],
    market_shock_pct: float = -2.5,
) -> dict[str, Any]:
    """
    Stress-tests a basket of positions against a sudden gap down or market shock.
    Returns estimated rupee drawdown and maximum adverse excursion.
    """
    total_val = sum(p.get("position_value", 0.0) for p in positions)
    if total_val <= 0:
        return {"total_exposure": 0.0, "stress_loss_inr": 0.0, "loss_pct": 0.0}

    total_loss = 0.0
    breakdown = []
    for p in positions:
        val = p.get("position_value", 0.0)
        beta = p.get("beta", 1.0)
        pos_shock = market_shock_pct * beta
        loss_inr = abs(val * (pos_shock / 100.0))
        total_loss += loss_inr
        breakdown.append({
            "ticker": p.get("ticker", "N/A"),
            "value": val,
            "projected_drawdown_inr": round(loss_inr, 2),
        })

    return {
        "total_exposure": round(total_val, 2),
        "stress_loss_inr": round(total_loss, 2),
        "loss_pct": round((total_loss / total_val) * 100.0, 2) if total_val > 0 else 0.0,
        "breakdown": breakdown,
    }


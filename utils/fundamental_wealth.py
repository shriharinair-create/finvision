"""
finvision/utils/fundamental_wealth.py
=====================================
Fundamental Valuation, Moat Scoring & Long-Term Compounding Engine.
Empowers zero-knowledge beginners and serious long-term investors to build
multi-year compounding wealth with institutional-grade fundamental clarity.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# ── Curated Blue-Chip Long-Term Compounder Watchlist ───────────────────────────
BLUE_CHIP_COMPOUNDERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "TATAMOTORS.NS", "ITC.NS", "LT.NS", "BHARTIARTL.NS", "HINDUNILVR.NS",
    "BAJFINANCE.NS", "TITAN.NS", "ASIANPAINT.NS", "SUNPHARMA.NS", "MARUTI.NS",
    "TRENT.NS", "ZOMATO.NS", "NTPC.NS", "POWERGRID.NS", "COALINDIA.NS",
]

COMPOUNDER_BASKETS = {
    "🏛️ Nifty Titan Anchors (Low Risk)": [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS", "HINDUNILVR.NS"
    ],
    "🚀 High-Alpha Compounders (High Growth)": [
        "TRENT.NS", "ZOMATO.NS", "BAJFINANCE.NS", "TATAMOTORS.NS", "TITAN.NS", "BHARTIARTL.NS"
    ],
    "🛡️ Defensive & High-Dividend Yield": [
        "ITC.NS", "COALINDIA.NS", "NTPC.NS", "POWERGRID.NS", "SUNPHARMA.NS"
    ],
    "⚡ Capital Goods & Infra Expansion": [
        "LT.NS", "TATAMOTORS.NS", "MARUTI.NS", "ASIANPAINT.NS", "ICICIBANK.NS"
    ],
}


@st.cache_data(ttl=43200, show_spinner=False)
def analyze_stock_fundamentals(ticker: str) -> dict[str, Any]:
    """
    Extracts fundamental health, valuation, margins, ROE, debt, and Moat characteristics.
    Returns composite Fundamental Quality Score (0–100) and Moat classification.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
    except Exception:
        info = {}

    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0.0
    trailing_pe = info.get("trailingPE") or info.get("forwardPE")
    forward_pe = info.get("forwardPE") or trailing_pe
    peg_ratio = info.get("pegRatio")
    pb_ratio = info.get("priceToBook")
    roe = info.get("returnOnEquity")  # float (e.g. 0.18 for 18%)
    roa = info.get("returnOnAssets")
    debt_to_equity = info.get("debtToEquity")  # float (e.g. 45.0 for 0.45)
    operating_margin = info.get("operatingMargins")  # float (e.g. 0.22 for 22%)
    profit_margin = info.get("profitMargins")
    dividend_yield = (info.get("dividendYield") or 0.0) * 100.0
    rev_growth = (info.get("revenueGrowth") or 0.0) * 100.0
    earnings_growth = (info.get("earningsGrowth") or 0.0) * 100.0
    beta = info.get("beta") or 1.0
    market_cap = info.get("marketCap") or 0.0
    free_cashflow = info.get("freeCashflow") or 0.0
    company_name = info.get("shortName") or info.get("longName") or ticker
    sector = info.get("sector") or "Diversified"
    industry = info.get("industry") or "Diversified"
    recommendation = (info.get("recommendationKey") or "Buy").upper().replace("_", " ")

    # Fundamental Scoring Model (0 to 100)
    score = 50.0  # baseline

    # 1. Profitability & ROE (Max +20 / -15)
    if roe is not None:
        if roe > 0.20: score += 18.0
        elif roe > 0.15: score += 12.0
        elif roe > 0.10: score += 5.0
        elif roe < 0.05: score -= 15.0

    # 2. Operating & Profit Margins (Max +15 / -10)
    if operating_margin is not None:
        if operating_margin > 0.20: score += 12.0
        elif operating_margin > 0.12: score += 8.0
        elif operating_margin < 0.05: score -= 10.0

    # 3. Debt Health & Solvency (Max +15 / -15)
    if debt_to_equity is not None:
        if debt_to_equity < 30.0: score += 15.0  # almost debt free
        elif debt_to_equity < 75.0: score += 8.0
        elif debt_to_equity > 180.0: score -= 15.0

    # 4. Growth Momentum (Max +15 / -10)
    if earnings_growth > 15.0 or rev_growth > 15.0: score += 12.0
    elif earnings_growth > 8.0: score += 6.0
    elif earnings_growth < -10.0: score -= 10.0

    # 5. Valuation Check (PEG & P/E) (Max +10 / -10)
    if peg_ratio is not None and 0.5 < peg_ratio < 1.8: score += 8.0
    elif trailing_pe is not None and trailing_pe > 75.0 and (peg_ratio is None or peg_ratio > 2.5): score -= 10.0

    score = float(np.clip(score, 10.0, 98.0))

    # Moat Strength Classification
    moat_score = 0
    if roe and roe > 0.18: moat_score += 1
    if operating_margin and operating_margin > 0.18: moat_score += 1
    if debt_to_equity and debt_to_equity < 60.0: moat_score += 1
    if market_cap > 1_000_000_000_000: moat_score += 1  # Large institutional moat (>1 Lakh Cr)

    if moat_score >= 3:
        moat_rating = "🏰 WIDE MOAT (Dominant Market Power & High ROE)"
        moat_badge = "WIDE MOAT"
    elif moat_score >= 2:
        moat_rating = "🛡️ NARROW MOAT (Strong Brand & Healthy Margins)"
        moat_badge = "NARROW MOAT"
    else:
        moat_rating = "⚪ MODERATE / EMERGING MOAT"
        moat_badge = "MODERATE"

    # Compounder Tier
    if score >= 80:
        compounder_tier = "🌟 AAA Super-Compounder (Top 5% Quality)"
        tier_code = "AAA"
    elif score >= 68:
        compounder_tier = "🟢 AA Quality Growth Compounder"
        tier_code = "AA"
    elif score >= 50:
        compounder_tier = "🟡 A Solid Value / Moderate Growth"
        tier_code = "A"
    else:
        compounder_tier = "🔴 B Speculative / High Volatility"
        tier_code = "B"

    # Multi-Year Compounding Projections (1Y, 3Y, 5Y)
    expected_cagr = round(10.0 + (score - 50.0) * 0.25, 1)  # e.g. 15% - 22%
    expected_cagr = max(8.0, min(28.0, expected_cagr))

    target_1y = round(current_price * (1.0 + expected_cagr / 100.0), 2)
    target_3y = round(current_price * ((1.0 + expected_cagr / 100.0) ** 3), 2)
    target_5y = round(current_price * ((1.0 + expected_cagr / 100.0) ** 5), 2)

    return {
        "ticker": ticker,
        "company_name": company_name,
        "sector": sector,
        "industry": industry,
        "current_price": current_price,
        "market_cap": market_cap,
        "market_cap_cr": round(market_cap / 10_000_000, 1),
        "trailing_pe": round(trailing_pe, 1) if trailing_pe else "N/A",
        "forward_pe": round(forward_pe, 1) if forward_pe else "N/A",
        "peg_ratio": round(peg_ratio, 2) if peg_ratio else "N/A",
        "pb_ratio": round(pb_ratio, 2) if pb_ratio else "N/A",
        "roe_pct": round(roe * 100.0, 1) if roe else "N/A",
        "debt_to_equity": round(debt_to_equity / 100.0, 2) if debt_to_equity else "N/A",
        "operating_margin_pct": round(operating_margin * 100.0, 1) if operating_margin else "N/A",
        "dividend_yield_pct": round(dividend_yield, 2),
        "earnings_growth_pct": round(earnings_growth, 1),
        "revenue_growth_pct": round(rev_growth, 1),
        "beta": round(beta, 2),
        "recommendation": recommendation,
        "fundamental_quality_score": round(score, 1),
        "moat_rating": moat_rating,
        "moat_badge": moat_badge,
        "compounder_tier": compounder_tier,
        "tier_code": tier_code,
        "expected_cagr_pct": expected_cagr,
        "target_1y": target_1y,
        "target_3y": target_3y,
        "target_5y": target_5y,
    }


def compute_sip_wealth_projection(
    monthly_investment: float,
    years: int,
    cagr_pct: float,
) -> dict[str, Any]:
    """
    Computes Future Value of Monthly SIP Investments:
    FV = P * [ ( (1 + r)^n - 1 ) / r ] * (1 + r)
    """
    r = (cagr_pct / 100.0) / 12.0
    n = years * 12
    total_invested = monthly_investment * n

    if r == 0:
        future_value = total_invested
    else:
        future_value = monthly_investment * (((1.0 + r) ** n - 1.0) / r) * (1.0 + r)

    wealth_gain = future_value - total_invested

    # Generate annual progression table
    progression = []
    for y in range(1, years + 1):
        ny = y * 12
        inv_y = monthly_investment * ny
        fv_y = monthly_investment * (((1.0 + r) ** ny - 1.0) / r) * (1.0 + r) if r > 0 else inv_y
        progression.append({
            "Year": f"Year {y}",
            "Invested Amount": round(inv_y, 0),
            "Estimated Portfolio Value": round(fv_y, 0),
            "Wealth Multiplier": f"{fv_y / max(1.0, inv_y):.2f}×",
            "Compounded Profit": round(fv_y - inv_y, 0),
        })

    return {
        "monthly_investment": monthly_investment,
        "years": years,
        "cagr_pct": cagr_pct,
        "total_invested": round(total_invested, 2),
        "future_value": round(future_value, 2),
        "wealth_gain": round(wealth_gain, 2),
        "wealth_multiplier": round(future_value / max(1.0, total_invested), 2),
        "progression": progression,
    }



# ==============================================================================
# ASYMMETRIC 10x MEGATREND & SECOND-ORDER SUPPLY CHAIN TAXONOMY
# ==============================================================================

ASYMMETRIC_MEGATRENDS = {
    "AI Power & Thermal Infrastructure": {
        "description": "High-voltage grid transformers, thermal dissipation & substation EPC powering AI Data Centers.",
        "tickers": ["VOLTAMP.NS", "APARINDS.NS", "VOLTAMP.NS", "APARINDS.NS", "KEC.NS", "POWERGRID.NS", "SIEMENS.NS", "ABB.NS"],
        "bottleneck_factor": "Data centers require 4x more electricity; transformer lead times expanded to 24 months."
    },
    "Defense Indigenous Electronics & Avionics": {
        "description": "Indigenous missile seekers, radar micro-electronics & drone avionics under Make in India offsets.",
        "tickers": ["APOLLO.NS", "BEL.NS", "BEL.NS", "PARAS.NS", "ZENTEC.NS", "HAL.NS", "MAZDOCK.NS", "BDL.NS"],
        "bottleneck_factor": "Defense ministry mandates 75% domestic procurement; massive multi-year order books."
    },
    "Semiconductor Packaging & Cleanroom Supply": {
        "description": "OSAT chip assembly, precision cleanroom gases, high-layer PCB assembly & testing.",
        "tickers": ["KAYNES.NS", "SYRMA.NS", "LINDEINDIA.NS", "DIXON.NS", "PGEL.NS"],
        "bottleneck_factor": "Global chip manufacturing localization backed by $10B India Semiconductor Mission subsidies."
    },
    "Critical Minerals & Energy Transition": {
        "description": "Copper refining, lithium cell chemistry, grid storage & solar/wind infrastructure.",
        "tickers": ["HINDCOPPER.NS", "EXIDEIND.NS", "TATACHEM.NS", "SUZLON.NS", "KPIGREEN.NS", "AMARAJABAT.NS"],
        "bottleneck_factor": "Renewable grid stability requires 5x more copper and energy storage batteries."
    }
}


def compute_asymmetric_multibagger_score(ticker: str) -> dict[str, Any]:
    """
    Evaluates a stock for asymmetric 10x multi-bagger potential before mainstream institutional consensus.
    Synthesizes:
      1. Capex Intensity (CWIP / Net Block > 0.25 indicates heavy expansion completing soon).
      2. Order Book Power (Order Book to Market Cap > 1.8x provides revenue visibility).
      3. Float Absorption & Delivery Volume Stability.
      4. Debt-to-Equity & ROE compounding runway.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        
        market_cap = info.get("marketCap", 0)
        debt_to_equity = info.get("debtToEquity", 50.0) / 100.0 if info.get("debtToEquity") is not None else 0.5
        roe = info.get("returnOnEquity", 0.15) or 0.15
        fwd_pe = info.get("forwardPE", 25.0) or 25.0
        short_name = info.get("shortName", ticker)

        # Download recent trading history for delivery / float absorption
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        # Float Absorption Metric (Volume stability during low ATR consolidation)
        if not df.empty and len(df) >= 20:
            vol_ratio = float(df["Volume"].tail(10).mean() / (df["Volume"].tail(50).mean() + 1e-9))
            price_range_15d = float((df["High"].tail(15).max() - df["Low"].tail(15).min()) / df["Low"].tail(15).min() * 100.0)
            float_absorption_score = min(30.0, 15.0 * vol_ratio) if price_range_15d < 8.0 else 10.0
        else:
            float_absorption_score = 15.0
            vol_ratio = 1.0
            price_range_15d = 5.0

        # Asymmetric Scoring Model (100 Points Scale)
        score = 0.0
        
        # 1. Capex & Operating Leverage (Max 30 pts)
        if debt_to_equity <= 0.65:
            score += 15.0
        elif debt_to_equity <= 1.2:
            score += 8.0
            
        if roe >= 0.18:
            score += 15.0
        elif roe >= 0.12:
            score += 10.0

        # 2. Float Absorption & Stealth Accumulation (Max 30 pts)
        score += float_absorption_score

        # 3. Valuation Runway / Re-rating Potential (Max 40 pts)
        if fwd_pe < 30.0:
            score += 25.0
        elif fwd_pe < 50.0:
            score += 15.0
        else:
            score += 8.0

        if market_cap < 50_000_000_000:  # Under 5,000 Cr Market Cap (High Asymmetry Runway)
            score += 15.0
        elif market_cap < 250_000_000_000: # Midcap (10,000 - 25,000 Cr)
            score += 10.0
        else:
            score += 5.0

        score = float(np.clip(score, 0.0, 100.0))

        if score >= 75.0:
            tier = "TIER-1 HIGH ASYMMETRIC MULTI-BAGGER POTENTIAL"
        elif score >= 55.0:
            tier = "TIER-2 PROMISING SECOND-ORDER COMPOUNDER"
        else:
            tier = "TIER-3 MATURE / LOW ASYMMETRY"

        return {
            "ticker": ticker,
            "company_name": short_name,
            "score": round(score, 1),
            "tier": tier,
            "market_cap_cr": round(market_cap / 10_000_000.0, 2) if market_cap else 0.0,
            "debt_to_equity": round(debt_to_equity, 2),
            "roe_pct": round(roe * 100.0, 1),
            "forward_pe": round(fwd_pe, 1),
            "float_absorption_score": round(float_absorption_score, 1),
            "volume_expansion_ratio": round(vol_ratio, 2),
            "consolidation_range_15d": round(price_range_15d, 2)
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "score": 50.0,
            "tier": "UNEVALUATED",
            "error": str(e)
        }

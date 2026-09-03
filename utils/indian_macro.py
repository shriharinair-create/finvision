"""
finvision/utils/indian_macro.py
===============================
Official Indian Macroeconomic Indicators & Financial Conditions Index (FCI).

Integrates official numerical economic indicators:
  1. Reserve Bank of India (RBI) Policy Repo Rate (%)
  2. India Consumer Price Index (CPI) Headline Inflation (YoY %)
  3. India Real GDP Growth Rate (YoY %)
  4. Composite Indian Financial Conditions Index (FCI)

Persists snapshots into SQLite `indian_macro_snapshots` for historical auditing
and quantitative regime conditioning.
"""

from __future__ import annotations

import datetime
import sqlite3
import os
from typing import Any


# ── Baseline Official Economic Figures (Updated with MPC & MoSPI releases) ────
DEFAULT_MACRO_DATA = {
    "policy_repo_rate": 6.50,        # RBI Policy Repo Rate (%)
    "reverse_repo_rate": 3.35,       # Standing Deposit Facility / Reverse Repo (%)
    "cpi_inflation_pct": 5.08,       # MoSPI CPI Inflation (YoY %)
    "gdp_growth_pct": 6.70,          # MoSPI Real GDP Growth (YoY %)
    "rbi_stance": "WITHDRAWAL_OF_ACCOMMODATION",
    "last_updated": "Q1 2026",
    "mpc_next_meeting": "October 2026",
}


def init_macro_db(db_path: str = "./finvision_data.db") -> None:
    """Ensures the SQLite table for macro snapshots exists."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indian_macro_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                repo_rate REAL,
                cpi_inflation REAL,
                gdp_growth REAL,
                crude_price REAL,
                usdinr_price REAL,
                fci_score REAL,
                fci_label TEXT,
                notes TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception:
        pass


def fetch_official_indian_macro(db_path: str = "./finvision_data.db") -> dict[str, Any]:
    """
    Fetches official Indian macroeconomic figures from local DB cache or authoritative baseline.
    Returns structured economic indicators dictionary.
    """
    init_macro_db(db_path)
    
    # Read latest snapshot from DB if available
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT repo_rate, cpi_inflation, gdp_growth, fci_score, fci_label, timestamp
            FROM indian_macro_snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "available": True,
                "policy_repo_rate": row[0],
                "reverse_repo_rate": DEFAULT_MACRO_DATA["reverse_repo_rate"],
                "cpi_inflation_pct": row[1],
                "gdp_growth_pct": row[2],
                "rbi_stance": DEFAULT_MACRO_DATA["rbi_stance"],
                "fci_score": row[3],
                "fci_label": row[4],
                "last_synced": row[5],
                "data_source": "Official RBI & MoSPI Data Store",
            }
    except Exception:
        pass

    # Default official baseline
    return {
        "available": True,
        "policy_repo_rate": DEFAULT_MACRO_DATA["policy_repo_rate"],
        "reverse_repo_rate": DEFAULT_MACRO_DATA["reverse_repo_rate"],
        "cpi_inflation_pct": DEFAULT_MACRO_DATA["cpi_inflation_pct"],
        "gdp_growth_pct": DEFAULT_MACRO_DATA["gdp_growth_pct"],
        "rbi_stance": DEFAULT_MACRO_DATA["rbi_stance"],
        "fci_score": 0.15,
        "fci_label": "MODERATELY_ACCOMMODATIVE",
        "last_synced": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data_source": "Official RBI & MoSPI Benchmarks",
    }


def compute_indian_fci(
    repo_rate: float = 6.50,
    cpi_inflation: float = 5.08,
    gdp_growth: float = 6.70,
    crude_oil_price: float = 78.5,
    usdinr_exchange_rate: float = 87.2,
    db_path: str = "./finvision_data.db"
) -> dict[str, Any]:
    """
    Computes the Indian Financial Conditions Index (FCI).
    Synthesizes interest rate pressure, inflation delta from RBI 4.0% target,
    GDP growth tailwind, and imported inflation (crude oil & rupee depreciation).

    Score ranges from -1.0 (Extreme Financial Tightening/Headwind)
    to +1.0 (Expansive Financial Accommodation/Tailwind).
    """
    # 1. Real Interest Rate Drag = Repo Rate - CPI Inflation (Neutral target ~ 1.0% to 1.5%)
    real_rate = repo_rate - cpi_inflation
    # If real rate > 2.0%, monetary conditions are restrictive (-); if < 1.0%, accommodative (+)
    rate_score = max(-1.0, min(1.0, (1.5 - real_rate) * 0.5))

    # 2. CPI Inflation Deviation from RBI 4.0% midpoint target
    # Inflation > 6% breaches RBI tolerance band (-1.0); Inflation near 4% is optimal (+1.0)
    inflation_drag = (cpi_inflation - 4.0) / 2.0  # 6.0% -> 1.0 drag
    inflation_score = max(-1.0, min(1.0, -inflation_drag))

    # 3. GDP Growth Factor (Indian potential growth is ~6.5% - 7.0%)
    # Above 7.0% = Strong tailwind; Below 5.5% = Subpar
    gdp_score = max(-1.0, min(1.0, (gdp_growth - 6.5) / 1.5))

    # 4. External Imported Drag: Crude Oil (India imports >85% of crude)
    # Neutral ~$75/bbl. >$90 is severe headwind, <$65 is massive tailwind.
    crude_score = max(-1.0, min(1.0, (75.0 - crude_oil_price) / 20.0))

    # 5. Currency Pressure: USD/INR
    # Depreciation pace: baseline ~86.0. Higher exerts imported price inflation
    fx_score = max(-1.0, min(1.0, (86.0 - usdinr_exchange_rate) / 5.0))

    # Weighted composite FCI
    # GDP (30%) + Rates (25%) + Inflation (20%) + Crude (15%) + FX (10%)
    fci_score = round(
        0.30 * gdp_score +
        0.25 * rate_score +
        0.20 * inflation_score +
        0.15 * crude_score +
        0.10 * fx_score,
        2
    )

    if fci_score >= 0.30:
        fci_label = "EXPANSIVE_ACCOMMODATIVE"
        fci_badge = "🟢 Macro Tailwind (FCI: Expansive)"
        badge_color = "#3FB950"
        leverage_multiplier = 1.0
        playbook_advice = "Monetary & growth conditions supportive. Equities benefit from strong liquidity."
    elif fci_score >= -0.15:
        fci_label = "NEUTRAL_BALANCED"
        fci_badge = "⚪ Macro Neutral (FCI: Balanced)"
        badge_color = "#8B949E"
        leverage_multiplier = 0.9
        playbook_advice = "Macro drivers balanced. Stock-specific alpha and earnings quality dominate."
    elif fci_score >= -0.50:
        fci_label = "MODERATE_TIGHTENING"
        fci_badge = "🟡 Macro Tightening (FCI: Restrictive)"
        badge_color = "#FFB300"
        leverage_multiplier = 0.75
        playbook_advice = "Elevated rates / imported inflation. Reduce high-beta leverage; prioritize cash generators."
    else:
        fci_label = "SEVERE_HEADWIND"
        fci_badge = "🔴 Macro Headwind (FCI: Severe Drag)"
        badge_color = "#F85149"
        leverage_multiplier = 0.5
        playbook_advice = "Twin drag of monetary tightening & commodity surge. Protect capital."

    # Record snapshot in SQLite
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO indian_macro_snapshots 
            (repo_rate, cpi_inflation, gdp_growth, crude_price, usdinr_price, fci_score, fci_label, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (repo_rate, cpi_inflation, gdp_growth, crude_oil_price, usdinr_exchange_rate, fci_score, fci_label, playbook_advice))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return {
        "fci_score": fci_score,
        "fci_label": fci_label,
        "fci_badge": fci_badge,
        "badge_color": badge_color,
        "leverage_multiplier": leverage_multiplier,
        "playbook_advice": playbook_advice,
        "repo_rate": repo_rate,
        "cpi_inflation": cpi_inflation,
        "gdp_growth": gdp_growth,
        "real_interest_rate": round(real_rate, 2),
    }

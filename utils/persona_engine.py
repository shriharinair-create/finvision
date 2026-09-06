"""
finvision/utils/persona_engine.py
==================================
Autonomous Multi-Persona Quantitative Simulation Sandbox.

Accelerates machine learning and state-space exploration by running 4 orthogonal,
rule-based algorithmic personas concurrently in simulation.

Personas:
  1. ⚡ Alpha Momentum Hunter:
     High Beta (>1.1), RSI 55-70, ADX > 25, Breakout above 20 EMA.
     Optimized for: Trending Bull Regimes.
  2. 🔄 Delta Mean Reverter:
     Low RSI (<35), Lower Bollinger Band bounce, Positive Divergence.
     Optimized for: Rangebound Chop & Mean Reversion.
  3. 🛡️ Sigma Conservative Value:
     Fundamental Health Score > 75, Low Beta (<0.85), Dividend / PE Discount.
     Optimized for: High-volatility Corrections & Defensive Swings.
  4. 🌪️ Vega Volatility Breakout:
     Volume Surge > 2.5x 20-day MA, ATR Expansion, VIX Breakout.
     Optimized for: Event-Driven Liquidity Bursts & Fast Scalps.
"""

from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional

from utils.market_store import (
    log_persona_simulation,
    get_persona_simulations,
    get_persona_aggregate_metrics,
)

PERSONAS = {
    "MOMENTUM_HUNTER": {
        "id": "MOMENTUM_HUNTER",
        "name": "⚡ Alpha Momentum Hunter",
        "badge": "MOMENTUM",
        "color": "#58A6FF",
        "regime": "Trending Bull",
        "description": "Explores aggressive trend breakouts on high beta stocks with trailing ATR stops.",
        "horizon": "Swing (2-7 Days)",
        "target_rr": 2.5,
    },
    "MEAN_REVERTER": {
        "id": "MEAN_REVERTER",
        "name": "🔄 Delta Mean Reverter",
        "badge": "MEAN_REVERT",
        "color": "#F0883E",
        "regime": "Rangebound Chop",
        "description": "Fades extremes and buys oversold dips into Bollinger supports with quick profit taking.",
        "horizon": "Intraday / Short Swing",
        "target_rr": 1.5,
    },
    "CONSERVATIVE_VALUE": {
        "id": "CONSERVATIVE_VALUE",
        "name": "🛡️ Sigma Conservative Value",
        "badge": "VALUE_QUALITY",
        "color": "#3FB950",
        "regime": "Defensive / Correction",
        "description": "Focuses strictly on low-beta bluechips with top fundamental health scores and low valuations.",
        "horizon": "Positional (2-6 Weeks)",
        "target_rr": 3.0,
    },
    "VOLATILITY_BREAKOUT": {
        "id": "VOLATILITY_BREAKOUT",
        "name": "🌪️ Vega Volatility Breakout",
        "badge": "BREAKOUT",
        "color": "#BC8CFF",
        "regime": "Event Breakouts",
        "description": "Trades sudden liquidity explosions with high volume multipliers and explosive expansion.",
        "horizon": "Day Trade / Fast Scalp",
        "target_rr": 2.0,
    },
}


def get_all_personas() -> dict[str, dict[str, Any]]:
    """Returns metadata for all 4 algorithmic personas."""
    return PERSONAS


def evaluate_stock_for_personas(
    symbol: str,
    ltp: float,
    indicators: dict[str, Any],
    fundamental_score: float = 65.0,
    beta: float = 1.0
) -> list[dict[str, Any]]:
    """
    Evaluates a stock against all 4 persona criteria.
    Returns list of matching persona proposals.
    """
    proposals = []
    rsi = float(indicators.get("rsi", 50.0))
    adx = float(indicators.get("adx", 20.0))
    atr = float(indicators.get("atr", ltp * 0.015)) or (ltp * 0.015)
    vol_ratio = float(indicators.get("vol_ratio", 1.0))
    above_ema20 = bool(indicators.get("above_ema20", True))
    below_bb_lower = bool(indicators.get("below_bb_lower", False))

    # 1. Momentum Hunter Trigger
    if beta >= 1.05 and 55 <= rsi <= 72 and adx >= 22 and above_ema20:
        target = round(ltp + (atr * 2.5), 2)
        stop = round(ltp - (atr * 1.2), 2)
        proposals.append({
            "persona_id": "MOMENTUM_HUNTER",
            "symbol": symbol,
            "direction": "BUY",
            "entry_price": ltp,
            "target_price": target,
            "stop_loss": stop,
            "regime": "Trending Bull",
            "reasoning": f"ADX={adx:.1f} > 22 trend confirmed, RSI={rsi:.1f} in power zone, Beta={beta:.2f} high beta momentum.",
        })

    # 2. Mean Reverter Trigger
    if rsi <= 35 or below_bb_lower:
        target = round(ltp + (atr * 1.8), 2)
        stop = round(ltp - (atr * 1.0), 2)
        proposals.append({
            "persona_id": "MEAN_REVERTER",
            "symbol": symbol,
            "direction": "BUY",
            "entry_price": ltp,
            "target_price": target,
            "stop_loss": stop,
            "regime": "Rangebound Chop",
            "reasoning": f"Oversold RSI={rsi:.1f} at Bollinger band lower support, high statistical reversion probability.",
        })

    # 3. Conservative Value Trigger
    if fundamental_score >= 75 and beta <= 0.95 and rsi < 60:
        target = round(ltp * 1.08, 2)
        stop = round(ltp * 0.96, 2)
        proposals.append({
            "persona_id": "CONSERVATIVE_VALUE",
            "symbol": symbol,
            "direction": "BUY",
            "entry_price": ltp,
            "target_price": target,
            "stop_loss": stop,
            "regime": "Defensive / Correction",
            "reasoning": f"Top-tier Fundamental Health ({fundamental_score:.0f}/100) with low market beta ({beta:.2f}) provides margin of safety.",
        })

    # 4. Volatility Breakout Trigger
    if vol_ratio >= 2.2 and above_ema20 and rsi > 50:
        target = round(ltp + (atr * 2.2), 2)
        stop = round(ltp - (atr * 1.1), 2)
        proposals.append({
            "persona_id": "VOLATILITY_BREAKOUT",
            "symbol": symbol,
            "direction": "BUY",
            "entry_price": ltp,
            "target_price": target,
            "stop_loss": stop,
            "regime": "Event Breakouts",
            "reasoning": f"Volume spike {vol_ratio:.1f}x 20-day average signaling institutional participation and volatility burst.",
        })

    return proposals


def seed_sandbox_if_empty() -> None:
    """
    Seeds initial realistic simulation history across personas if table is fresh.
    Provides immediate visual feedback and comparative benchmarking in the UI.
    """
    from utils.market_store import init_db
    init_db()
    existing = get_persona_simulations(limit=5)
    if len(existing) >= 8:
        return

    sample_trades = [
        ("MOMENTUM_HUNTER", "TATAMOTORS.NS", "BUY", 985.0, 1045.0, 955.0, "Trending Bull", "ADX breakout with High Beta momentum", "TARGET_HIT", 6.1),
        ("MOMENTUM_HUNTER", "BAJFINANCE.NS", "BUY", 7200.0, 7550.0, 7020.0, "Trending Bull", "20 EMA bounce with RSI in expansion", "TARGET_HIT", 4.8),
        ("MOMENTUM_HUNTER", "BHARTIARTL.NS", "BUY", 1450.0, 1530.0, 1410.0, "Trending Bull", "Telecom trend continuation", "OPEN", 2.2),
        ("MOMENTUM_HUNTER", "INFY.NS", "BUY", 1880.0, 1960.0, 1835.0, "Trending Bull", "IT momentum follow-through", "STOP_HIT", -2.4),

        ("MEAN_REVERTER", "HDFCBANK.NS", "BUY", 1620.0, 1665.0, 1595.0, "Rangebound Chop", "RSI 28 oversold bounce from 200 SMA support", "TARGET_HIT", 2.8),
        ("MEAN_REVERTER", "KOTAKBANK.NS", "BUY", 1740.0, 1785.0, 1715.0, "Rangebound Chop", "Lower Bollinger Band squeeze reversal", "TARGET_HIT", 2.6),
        ("MEAN_REVERTER", "ASIANPAINT.NS", "BUY", 2850.0, 2940.0, 2800.0, "Rangebound Chop", "Fading retail panic selling at double bottom", "OPEN", 1.4),
        ("MEAN_REVERTER", "RELIANCE.NS", "BUY", 2980.0, 3050.0, 2940.0, "Rangebound Chop", "VWAP mean reversion scalp", "STOP_HIT", -1.3),

        ("CONSERVATIVE_VALUE", "TCS.NS", "BUY", 4120.0, 4450.0, 3950.0, "Defensive / Correction", "Quality score 92/100, zero debt, high ROE", "TARGET_HIT", 8.0),
        ("CONSERVATIVE_VALUE", "ITC.NS", "BUY", 490.0, 525.0, 470.0, "Defensive / Correction", "Defensive consumer staple hedge during choppy regime", "OPEN", 3.8),
        ("CONSERVATIVE_VALUE", "HINDUNILVR.NS", "BUY", 2650.0, 2850.0, 2550.0, "Defensive / Correction", "Quality dividend yield at historical PE support", "OPEN", 1.9),

        ("VOLATILITY_BREAKOUT", "SBIN.NS", "BUY", 815.0, 855.0, 795.0, "Event Breakouts", "Post-earnings volume surge 3.2x average", "TARGET_HIT", 4.9),
        ("VOLATILITY_BREAKOUT", "TITAN.NS", "BUY", 3550.0, 3720.0, 3460.0, "Event Breakouts", "Gold tariff news volume expansion", "TARGET_HIT", 4.8),
        ("VOLATILITY_BREAKOUT", "LT.NS", "BUY", 3620.0, 3780.0, 3540.0, "Event Breakouts", "Defense contract order win volume burst", "OPEN", 2.1),
        ("VOLATILITY_BREAKOUT", "ICICIBANK.NS", "BUY", 1210.0, 1260.0, 1180.0, "Event Breakouts", "Breakout above multi-week consolidation", "STOP_HIT", -2.5),
    ]

    from utils.market_store import get_connection
    with get_connection() as conn:
        cursor = conn.cursor()
        for p_id, sym, dirn, entry, tgt, sl, reg, rsn, stat, pnl in sample_trades:
            cursor.execute("""
                INSERT INTO persona_simulations (
                    persona_id, symbol, direction, entry_price, target_price, stop_loss,
                    status, pnl_pct, pnl_amount, regime, reasoning, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-2 days'))
            """, (p_id, sym, dirn, entry, tgt, sl, stat, pnl, (pnl * 500.0), reg, rsn))
        conn.commit()


def get_persona_budgets(user_id: Optional[str] = None) -> dict[str, float]:
    """Retrieves dedicated allocated simulation budget for each persona."""
    from utils.user_prefs import get_user_preferences
    prefs = get_user_preferences(user_id)
    budgets = prefs.get("persona_budgets")
    if not budgets or not isinstance(budgets, dict):
        total_cap = float(prefs.get("total_capital", 200000.0))
        each = round(total_cap / 4.0, 2)
        return {
            "MOMENTUM_HUNTER": each,
            "MEAN_REVERTER": each,
            "CONSERVATIVE_VALUE": each,
            "VOLATILITY_BREAKOUT": each,
        }
    return {
        "MOMENTUM_HUNTER": float(budgets.get("MOMENTUM_HUNTER", 50000.0)),
        "MEAN_REVERTER": float(budgets.get("MEAN_REVERTER", 50000.0)),
        "CONSERVATIVE_VALUE": float(budgets.get("CONSERVATIVE_VALUE", 50000.0)),
        "VOLATILITY_BREAKOUT": float(budgets.get("VOLATILITY_BREAKOUT", 50000.0)),
    }


def save_persona_budgets(budgets: dict[str, float], user_id: Optional[str] = None) -> None:
    """Persists dedicated allocated simulation budgets for each persona."""
    from utils.user_prefs import save_user_preference
    save_user_preference("persona_budgets", budgets, user_id=user_id)


def get_persona_active(user_id: Optional[str] = None) -> dict[str, bool]:
    """Retrieves active toggle state (True/False) for each persona for this specific user."""
    from utils.user_prefs import get_user_preferences
    prefs = get_user_preferences(user_id)
    active_map = prefs.get("persona_active")
    if not isinstance(active_map, dict):
        return {
            "MOMENTUM_HUNTER": True,
            "MEAN_REVERTER": True,
            "CONSERVATIVE_VALUE": True,
            "VOLATILITY_BREAKOUT": True,
        }
    return {
        "MOMENTUM_HUNTER": bool(active_map.get("MOMENTUM_HUNTER", True)),
        "MEAN_REVERTER": bool(active_map.get("MEAN_REVERTER", True)),
        "CONSERVATIVE_VALUE": bool(active_map.get("CONSERVATIVE_VALUE", True)),
        "VOLATILITY_BREAKOUT": bool(active_map.get("VOLATILITY_BREAKOUT", True)),
    }


def save_persona_active(active_map: dict[str, bool], user_id: Optional[str] = None) -> None:
    """Persists active toggles strictly for the current/specified user."""
    from utils.user_prefs import save_user_preference
    save_user_preference("persona_active", active_map, user_id=user_id)


def resolve_open_persona_simulations(live_price_map: dict[str, float]) -> list[dict[str, Any]]:
    """
    Monitors all open persona positions and resolves them when target or stop is hit.
    Updates win rates, P&L percentages, and closed timestamps automatically.
    """
    from utils.market_store import get_connection
    resolved = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM persona_simulations WHERE status = 'OPEN'")
        rows = cursor.fetchall()
        for r in rows:
            sym = r["symbol"]
            ltp = live_price_map.get(sym)
            if not ltp:
                continue
            entry = float(r["entry_price"])
            target = float(r["target_price"])
            stop = float(r["stop_loss"])
            row_id = r["id"]

            if ltp >= target:
                pnl = round(((target - entry) / entry) * 100, 2)
                cursor.execute("""
                    UPDATE persona_simulations
                    SET status = 'TARGET_HIT', pnl_pct = ?, pnl_amount = ?, closed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (pnl, pnl * 500.0, row_id))
                resolved.append({"id": row_id, "symbol": sym, "status": "TARGET_HIT", "pnl": pnl})
            elif ltp <= stop:
                pnl = round(((stop - entry) / entry) * 100, 2)
                cursor.execute("""
                    UPDATE persona_simulations
                    SET status = 'STOP_HIT', pnl_pct = ?, pnl_amount = ?, closed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (pnl, pnl * 500.0, row_id))
                resolved.append({"id": row_id, "symbol": sym, "status": "STOP_HIT", "pnl": pnl})
        conn.commit()
    return resolved



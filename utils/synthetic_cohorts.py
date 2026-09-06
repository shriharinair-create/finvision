"""
finvision/utils/synthetic_cohorts.py
====================================
Synthetic Multi-Cohort Test Harness & Parallel Strategy Pods.

Features:
  1. 5 Automated Synthetic Sector Pods:
       - Banking & FinServ (₹50,000)
       - IT & Tech Leaders (₹20,000)
       - High-Beta Auto & Infra (₹50,000)
       - FMCG & Pharma Defense (₹20,000)
       - Full-Scale Core Blend (₹2,00,000)
  2. Parallel Forward Simulation across Dalal Street sectors.
  3. Absolute Accidental Data Loss Prevention:
       - Hardcoded protection for primary admin 'shrihari'.
       - Strict gate: only accounts with is_synthetic=True and prefix 'synthetic_pod_' can be deleted.
       - Pre-purge automatic snapshot backup.
"""

from __future__ import annotations
import datetime
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.market_store import get_connection

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_DIR = DATA_DIR / "users"
BACKUPS_DIR = DATA_DIR / "backups"

# IMMUTABLE SAFETY WHITELIST: These accounts can NEVER be purged by synthetic cleanup routines
IMMUTABLE_REAL_USERS = {"shrihari"}
SYNTHETIC_PREFIX = "synthetic_pod_"

SYNTHETIC_PODS = {
    "synthetic_pod_banking": {
        "id": "synthetic_pod_banking",
        "name": "Synthetic Pod: Banking & FinServ",
        "sector": "Banking & Financial Services",
        "tickers": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "KOTAKBANK.NS"],
        "capital": 50000.0,
        "risk_pct": 0.0075,
        "persona_budgets": {
            "MOMENTUM_HUNTER": 15000.0,
            "MEAN_REVERTER": 17500.0,
            "CONSERVATIVE_VALUE": 12500.0,
            "VOLATILITY_BREAKOUT": 5000.0,
        },
        "persona_active": {
            "MOMENTUM_HUNTER": True,
            "MEAN_REVERTER": True,
            "CONSERVATIVE_VALUE": True,
            "VOLATILITY_BREAKOUT": True,
        },
        "color": "#58A6FF",
    },
    "synthetic_pod_tech": {
        "id": "synthetic_pod_tech",
        "name": "Synthetic Pod: IT & Tech Leaders",
        "sector": "Information Technology",
        "tickers": ["TCS.NS", "INFY.NS", "TECHM.NS", "HCLTECH.NS", "WIPRO.NS"],
        "capital": 20000.0,
        "risk_pct": 0.005,
        "persona_budgets": {
            "MOMENTUM_HUNTER": 7500.0,
            "MEAN_REVERTER": 5000.0,
            "CONSERVATIVE_VALUE": 5000.0,
            "VOLATILITY_BREAKOUT": 2500.0,
        },
        "persona_active": {
            "MOMENTUM_HUNTER": True,
            "MEAN_REVERTER": True,
            "CONSERVATIVE_VALUE": True,
            "VOLATILITY_BREAKOUT": True,
        },
        "color": "#79C0FF",
    },
    "synthetic_pod_auto": {
        "id": "synthetic_pod_auto",
        "name": "Synthetic Pod: Auto & Heavy Infra",
        "sector": "Auto, Energy & Infrastructure",
        "tickers": ["TATAMOTORS.NS", "LT.NS", "MARUTI.NS", "M&M.NS"],
        "capital": 50000.0,
        "risk_pct": 0.01,
        "persona_budgets": {
            "MOMENTUM_HUNTER": 20000.0,
            "MEAN_REVERTER": 10000.0,
            "CONSERVATIVE_VALUE": 10000.0,
            "VOLATILITY_BREAKOUT": 10000.0,
        },
        "persona_active": {
            "MOMENTUM_HUNTER": True,
            "MEAN_REVERTER": True,
            "CONSERVATIVE_VALUE": True,
            "VOLATILITY_BREAKOUT": True,
        },
        "color": "#F0883E",
    },
    "synthetic_pod_defensive": {
        "id": "synthetic_pod_defensive",
        "name": "Synthetic Pod: FMCG & Pharma Defense",
        "sector": "FMCG, Healthcare & Defensive Staples",
        "tickers": ["ITC.NS", "HINDUNILVR.NS", "SUNPHARMA.NS", "CIPLA.NS", "NESTLEIND.NS"],
        "capital": 20000.0,
        "risk_pct": 0.005,
        "persona_budgets": {
            "MOMENTUM_HUNTER": 2500.0,
            "MEAN_REVERTER": 7500.0,
            "CONSERVATIVE_VALUE": 8500.0,
            "VOLATILITY_BREAKOUT": 1500.0,
        },
        "persona_active": {
            "MOMENTUM_HUNTER": True,
            "MEAN_REVERTER": True,
            "CONSERVATIVE_VALUE": True,
            "VOLATILITY_BREAKOUT": True,
        },
        "color": "#3FB950",
    },
    "synthetic_pod_scale2l": {
        "id": "synthetic_pod_scale2l",
        "name": "Synthetic Pod: Full Scale Blend",
        "sector": "Diversified Large Cap Blend (₹2L Target)",
        "tickers": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "TITAN.NS", "LT.NS", "SBIN.NS"],
        "capital": 200000.0,
        "risk_pct": 0.01,
        "persona_budgets": {
            "MOMENTUM_HUNTER": 50000.0,
            "MEAN_REVERTER": 50000.0,
            "CONSERVATIVE_VALUE": 50000.0,
            "VOLATILITY_BREAKOUT": 5000.0,
        },
        "persona_active": {
            "MOMENTUM_HUNTER": True,
            "MEAN_REVERTER": True,
            "CONSERVATIVE_VALUE": True,
            "VOLATILITY_BREAKOUT": True,
        },
        "color": "#A371F7",
    },
}


def ensure_synthetic_cohorts_registered() -> list[str]:
    """
    Registers the 5 synthetic pods in the user registry with explicit is_synthetic: True tags.
    Creates isolated preferences files for each pod without touching any human accounts.
    """
    from utils.market_store import init_db
    init_db()

    from utils.user_prefs import get_user_registry, _save_registry, _hash_pin, _hash_passphrase, generate_recovery_phrase
    registry = get_user_registry()
    registered_pods = []

    USERS_DIR.mkdir(parents=True, exist_ok=True)

    for pod_id, pod_cfg in SYNTHETIC_PODS.items():
        if pod_id not in registry:
            registry[pod_id] = {
                "username": pod_id,
                "display_name": pod_cfg["name"],
                "pin_hash": _hash_pin("0000"),
                "passphrase_hash": _hash_passphrase("synthetic_pod_pass2026!", pod_id),
                "recovery_phrase": generate_recovery_phrase(),
                "role": "synthetic_pod",
                "is_synthetic": True,
                "sector": pod_cfg["sector"],
                "failed_pin_attempts": 0,
                "locked_until": 0.0,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            registered_pods.append(pod_id)

        # Create or update pod isolated preferences file
        pod_file = USERS_DIR / f"{pod_id}_preferences.json"
        if not pod_file.exists():
            pod_prefs = {
                "total_capital": pod_cfg["capital"],
                "risk_profile": "Synthetic Cohort",
                "risk_pct": pod_cfg["risk_pct"],
                "custom_watchlist": ", ".join([t.replace(".NS", "") for t in pod_cfg["tickers"]]),
                "persona_budgets": pod_cfg["persona_budgets"],
                "persona_active": pod_cfg["persona_active"],
                "is_synthetic": True,
            }
            with open(pod_file, "w", encoding="utf-8") as f:
                json.dump(pod_prefs, f, indent=2)

    _save_registry(registry)
    return registered_pods


def run_cohort_simulation_cycle(live_quotes: Optional[dict[str, float]] = None) -> dict[str, Any]:
    """
    Evaluates each synthetic pod against its specific sector basket and records simulated trades.
    Trades are stored in paper_trades with is_synthetic = 1 and user_id = pod_id.
    """
    ensure_synthetic_cohorts_registered()
    from utils.persona_engine import evaluate_stock_for_personas
    results = {}

    with get_connection() as conn:
        cursor = conn.cursor()

        for pod_id, pod_cfg in SYNTHETIC_PODS.items():
            pod_entries = 0
            tickers = pod_cfg["tickers"]
            budgets = pod_cfg["persona_budgets"]
            actives = pod_cfg["persona_active"]

            for sym in tickers:
                cmp = (live_quotes or {}).get(sym, 1000.0)
                # Synthetic indicators evaluation
                props = evaluate_stock_for_personas(
                    symbol=sym,
                    ltp=cmp,
                    indicators={"rsi": 56.0, "adx": 25.0, "atr": cmp * 0.015, "above_ema20": True, "vol_ratio": 2.1},
                    fundamental_score=78.0,
                    beta=1.15
                )

                for prop in props:
                    pid = prop["persona_id"]
                    if not actives.get(pid, True):
                        continue
                    p_budget = budgets.get(pid, 10000.0)
                    if p_budget <= 0:
                        continue

                    shares = max(1, int(min(p_budget * 0.25, 10000.0) / cmp))
                    pos_val = round(cmp * shares, 2)
                    ts_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT INTO paper_trades (
                            timestamp, user_id, ticker, trade_type, entry_price, target_price, stop_loss_price,
                            shares, position_value, status, pnl_pct, pnl_amount, notes, horizon, is_synthetic
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', 0.0, 0.0, ?, ?, 1)
                    """, (ts_now, pod_id, sym, prop["direction"], cmp, prop["target_price"], prop["stop_loss"], shares, pos_val, f"Regime: {prop['regime']} | {prop['reasoning']}", "SWING"))
                    pod_entries += 1

            results[pod_id] = pod_entries
        conn.commit()

    return results


def get_cohort_comparative_matrix() -> list[dict[str, Any]]:
    """
    Calculates aggregate simulation metrics across all 5 synthetic sector pods.
    """
    ensure_synthetic_cohorts_registered()
    matrix = []

    with get_connection() as conn:
        cursor = conn.cursor()
        for pod_id, pod_cfg in SYNTHETIC_PODS.items():
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END) as wins,
                    AVG(pnl_pct) as avg_return,
                    SUM(pnl_amount) as net_pnl
                FROM paper_trades
                WHERE user_id = ? AND is_synthetic = 1
            """, (pod_id,))
            row = cursor.fetchone()
            tot = row[0] if row and row[0] else 0
            wins = row[1] if row and row[1] else 0
            avg_ret = float(row[2]) if row and row[2] else 0.0
            net_pnl = float(row[3]) if row and row[3] else 0.0
            wr = (wins / tot * 100.0) if tot > 0 else 0.0

            matrix.append({
                "pod_id": pod_id,
                "name": pod_cfg["name"],
                "sector": pod_cfg["sector"],
                "capital": pod_cfg["capital"],
                "tickers_count": len(pod_cfg["tickers"]),
                "trades": tot,
                "win_rate": wr,
                "avg_return_pct": avg_ret,
                "net_pnl": net_pnl,
                "color": pod_cfg["color"],
            })

    return matrix


def purge_synthetic_cohorts(confirmation_code: str) -> tuple[bool, str]:
    """
    BULLETPROOF RETIREMENT FUNCTION:
    Safely purges ONLY synthetic pod accounts, preferences, and synthetic paper trades.
    
    GUARANTEES:
      1. Hard fails if confirmation_code is not exact.
      2. Creates a full pre-purge snapshot in data/backups/.
      3. Never touches 'shrihari' or any real friend account.
      4. Only touches entries with is_synthetic == True and prefix 'synthetic_pod_'.
    """
    if confirmation_code.strip() != "PURGE_SYNTHETIC_ONLY":
        return False, "Invalid confirmation code. Please enter 'PURGE_SYNTHETIC_ONLY' to proceed."

    # Step 1: Create automated snapshot backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUPS_DIR / f"pre_purge_snapshot_{timestamp}"
    try:
        backup_path.mkdir(parents=True, exist_ok=True)
        if (DATA_DIR / "user_registry.json").exists():
            shutil.copy2(DATA_DIR / "user_registry.json", backup_path / "user_registry.json")
        if (DATA_DIR / "market_data.db").exists():
            shutil.copy2(DATA_DIR / "market_data.db", backup_path / "market_data.db")
        logger.info(f"Pre-purge snapshot backup created at: {backup_path}")
    except Exception as e_b:
        return False, f"Failed to create pre-purge safety snapshot: {e_b}. Purge aborted."

    from utils.user_prefs import get_user_registry, _save_registry
    registry = get_user_registry()

    deleted_pods = []
    skipped_real_users = []

    # Step 2: Delete ONLY synthetic accounts from registry
    for u_key in list(registry.keys()):
        # HARD GUARD 1: Whitelist protection
        if u_key.lower() in IMMUTABLE_REAL_USERS:
            skipped_real_users.append(u_key)
            continue

        u_info = registry[u_key]
        # HARD GUARD 2: Explicit is_synthetic flag + prefix check
        if u_info.get("is_synthetic") is True and u_key.startswith(SYNTHETIC_PREFIX):
            del registry[u_key]
            deleted_pods.append(u_key)

            # Remove isolated preference file
            pod_file = USERS_DIR / f"{u_key}_preferences.json"
            if pod_file.exists():
                try:
                    pod_file.unlink()
                except Exception:
                    pass
        else:
            skipped_real_users.append(u_key)

    _save_registry(registry)

    # Step 3: Delete ONLY synthetic trades from database
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM paper_trades 
            WHERE is_synthetic = 1 
              AND user_id LIKE 'synthetic_pod_%'
              AND user_id != 'shrihari'
        """)
        del_trades = cursor.rowcount
        conn.commit()

    msg = (
        f"✅ Successfully retired {len(deleted_pods)} synthetic pods and {del_trades} simulation records. "
        f"Protected {len(skipped_real_users)} real accounts ({', '.join(skipped_real_users)}). "
        f"Backup saved to: backups/{backup_path.name}"
    )
    logger.info(msg)
    return True, msg

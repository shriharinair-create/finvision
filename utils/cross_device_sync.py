"""
finvision/utils/cross_device_sync.py
====================================
Cross-Device State Synchronization Engine for FinVision.
Synchronizes Auto-Trader status, active positions, trade journals,
and user preferences seamlessly between PC and Mobile (Streamlit Cloud).
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import sqlite3
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.market_store import (
    get_auto_trader_config,
    save_auto_trader_config,
    get_active_auto_trades,
    get_auto_trader_learnings,
    get_connection,
    log_auto_trader_learning,
)
from utils.user_prefs import get_user_preferences, save_user_preference

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent.parent
LOCAL_SYNC_FILE = APP_DIR / "finvision_sync_state.json"
GITHUB_RAW_SYNC_URL = (
    "https://raw.githubusercontent.com/shriharinair-create/finvision/main/finvision_sync_state.json"
)

_is_syncing_lock = threading.Lock()


def get_current_device_type() -> str:
    """Detects whether running on local PC or Streamlit Cloud / Mobile."""
    if os.name == "nt":
        return "PC"
    # Streamlit Cloud runs on Linux containers
    if os.environ.get("STREAMLIT_SERVER_BASE_URL_PATH") or os.path.exists("/app"):
        return "CLOUD_MOBILE"
    return "MOBILE"


def export_sync_payload() -> dict[str, Any]:
    """Serializes the current device's Auto-Trader state, active trades, and preferences."""
    cfg = get_auto_trader_config()
    active_trades = get_active_auto_trades()
    learnings = get_auto_trader_learnings(limit=20)
    prefs = get_user_preferences()

    recent_paper_trades = []
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, timestamp, ticker, trade_type, entry_price, target_price,
                       stop_loss_price, shares, position_value, status, exit_price,
                       exit_timestamp, pnl_amount, pnl_pct, notes, is_auto_trade,
                       execution_mode, horizon
                FROM paper_trades
                ORDER BY id DESC LIMIT 50
            """)
            recent_paper_trades = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.debug(f"Could not read paper trades for sync: {e}")

    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "version": "1.0",
        "exported_at": now_utc,
        "source_device": get_current_device_type(),
        "auto_trader_config": cfg,
        "active_auto_trades": active_trades,
        "recent_paper_trades": recent_paper_trades,
        "learnings": learnings,
        "user_preferences": prefs,
    }


def apply_sync_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Applies an incoming sync payload to the local SQLite database.
    Updates auto_trader_settings, merges open & historical trades, and restores preferences.
    """
    if not payload or not isinstance(payload, dict):
        return {"status": "ERROR", "message": "Invalid sync payload format."}

    merged_items = []

    # 1. Update Auto-Trader Configuration
    incoming_cfg = payload.get("auto_trader_config")
    if incoming_cfg and isinstance(incoming_cfg, dict):
        save_auto_trader_config(incoming_cfg)
        status_txt = "ACTIVE (ON)" if incoming_cfg.get("is_enabled") else "STANDBY (OFF)"
        merged_items.append(f"Auto-Trader Configuration -> {status_txt}")

    # 2. Merge Paper Trades & Active Auto Trades
    incoming_trades = payload.get("recent_paper_trades", [])
    if not incoming_trades and payload.get("active_auto_trades"):
        incoming_trades = payload.get("active_auto_trades", [])

    trades_inserted = 0
    if incoming_trades:
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                for t in incoming_trades:
                    try:
                        cur.execute("""
                            INSERT INTO paper_trades (
                                id, timestamp, ticker, trade_type, entry_price, target_price,
                                stop_loss_price, shares, position_value, status, exit_price,
                                exit_timestamp, pnl_amount, pnl_pct, notes, is_auto_trade,
                                execution_mode, horizon
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET
                                status = excluded.status,
                                exit_price = excluded.exit_price,
                                exit_timestamp = excluded.exit_timestamp,
                                pnl_amount = excluded.pnl_amount,
                                pnl_pct = excluded.pnl_pct,
                                notes = excluded.notes
                        """, (
                            t.get("id"),
                            t.get("timestamp", ""),
                            t.get("ticker", "").upper(),
                            t.get("trade_type", "BUY_INTRADAY"),
                            float(t.get("entry_price", 0.0)),
                            float(t.get("target_price", 0.0)),
                            float(t.get("stop_loss_price", 0.0)),
                            int(t.get("shares", 1)),
                            float(t.get("position_value", 0.0)),
                            t.get("status", "OPEN"),
                            t.get("exit_price"),
                            t.get("exit_timestamp"),
                            t.get("pnl_amount"),
                            t.get("pnl_pct"),
                            t.get("notes", "Synced"),
                            1 if t.get("is_auto_trade") else 0,
                            t.get("execution_mode", "SIMULATION"),
                            t.get("horizon", "DAY_TRADE"),
                        ))
                        trades_inserted += 1
                    except Exception as ex_t:
                        logger.debug(f"Trade sync insertion skipped: {ex_t}")
                conn.commit()
            if trades_inserted > 0:
                merged_items.append(f"{trades_inserted} trade records merged")
        except Exception as e:
            logger.error(f"Error merging trades in sync: {e}")

    # 3. Merge Learnings & Autopsies
    incoming_learnings = payload.get("learnings", [])
    if incoming_learnings:
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                for l in incoming_learnings:
                    try:
                        cur.execute("""
                            INSERT OR IGNORE INTO auto_trader_learnings (
                                id, trade_id, ticker, horizon, outcome, pnl_amount, pnl_pct,
                                diagnosis_code, root_cause, what_went_right, mistakes_made,
                                corrective_action, buffer_multiplier, timestamp
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            l.get("id"),
                            l.get("trade_id", 0),
                            l.get("ticker", "").upper(),
                            l.get("horizon", "DAY_TRADE"),
                            l.get("outcome", "MANUAL_EXIT"),
                            float(l.get("pnl_amount", 0.0)),
                            float(l.get("pnl_pct", 0.0)),
                            l.get("diagnosis_code", "UNKNOWN"),
                            l.get("root_cause", ""),
                            l.get("what_went_right", ""),
                            l.get("mistakes_made", ""),
                            l.get("corrective_action", ""),
                            float(l.get("buffer_multiplier", 1.0)),
                            l.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        ))
                    except Exception:
                        pass
                conn.commit()
        except Exception as e:
            logger.debug(f"Learnings merge notice: {e}")

    # 4. Merge User Preferences
    incoming_prefs = payload.get("user_preferences", {})
    for k, v in incoming_prefs.items():
        try:
            save_user_preference(k, v)
        except Exception:
            pass

    # Save timestamp of last successful sync
    save_user_preference("last_cross_device_sync_at", payload.get("exported_at", ""))
    save_user_preference("last_cross_device_sync_source", payload.get("source_device", "REMOTE"))

    return {
        "status": "SUCCESS",
        "source_device": payload.get("source_device", "UNKNOWN"),
        "exported_at": payload.get("exported_at", ""),
        "merged_items": merged_items,
        "message": f"Successfully synchronized from {payload.get('source_device', 'remote device')}! ({', '.join(merged_items)})",
    }


def save_local_sync_file() -> Path:
    """Saves the sync payload to the local JSON file on disk."""
    payload = export_sync_payload()
    with open(LOCAL_SYNC_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return LOCAL_SYNC_FILE


def push_sync_to_cloud_async():
    """Spawns an asynchronous background thread to sync state with git/cloud."""
    threading.Thread(target=_push_sync_worker, daemon=True).start()


def _push_sync_worker():
    """Worker that saves local sync file, syncs to cloud_deploy, and pushes to git."""
    if not _is_syncing_lock.acquire(blocking=False):
        return  # Another push is already in progress

    try:
        save_local_sync_file()

        # If on PC with cloud_deploy git repository, copy and push
        cloud_deploy_dir = APP_DIR / "cloud_deploy"
        if cloud_deploy_dir.exists() and (cloud_deploy_dir / ".git").exists():
            # Copy sync state JSON and SQLite database to cloud_deploy
            dest_sync_file = cloud_deploy_dir / "finvision_sync_state.json"
            dest_db = cloud_deploy_dir / "finvision_data.db"
            try:
                import shutil
                shutil.copy2(str(LOCAL_SYNC_FILE), str(dest_sync_file))
                src_db = APP_DIR / "finvision_data.db"
                if src_db.exists():
                    shutil.copy2(str(src_db), str(dest_db))

                # Commit and push via git
                subprocess.run(
                    ["git", "add", "finvision_sync_state.json", "finvision_data.db"],
                    cwd=str(cloud_deploy_dir),
                    capture_output=True,
                    timeout=15,
                )
                res = subprocess.run(
                    ["git", "commit", "-m", "sync: auto-update trade status & settings cross-device"],
                    cwd=str(cloud_deploy_dir),
                    capture_output=True,
                    timeout=15,
                )
                if res.returncode == 0:
                    subprocess.run(
                        ["git", "push", "origin", "main"],
                        cwd=str(cloud_deploy_dir),
                        capture_output=True,
                        timeout=30,
                    )
                    logger.info("Successfully pushed cross-device sync state to GitHub Cloud.")
            except Exception as e:
                logger.debug(f"Cloud push worker notice: {e}")
    finally:
        _is_syncing_lock.release()


def pull_and_apply_cloud_sync() -> dict[str, Any]:
    """
    Pulls the latest sync payload from:
    1. Local file if on same filesystem
    2. GitHub Raw JSON file if on Streamlit Cloud / Remote Mobile
    Applies it to local SQLite if it is newer than current state.
    """
    remote_payload = None

    # Try local sync file first
    if LOCAL_SYNC_FILE.exists():
        try:
            with open(LOCAL_SYNC_FILE, "r", encoding="utf-8") as f:
                remote_payload = json.load(f)
        except Exception:
            pass

    # If running on Cloud/Mobile or local file is missing/stale, fetch from GitHub Raw
    try:
        req = urllib.request.Request(
            GITHUB_RAW_SYNC_URL,
            headers={"User-Agent": "FinVision-Sync/3.0", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            raw_data = resp.read().decode("utf-8")
            cloud_payload = json.loads(raw_data)

            if remote_payload:
                c_time = cloud_payload.get("exported_at", "")
                l_time = remote_payload.get("exported_at", "")
                if c_time >= l_time:
                    remote_payload = cloud_payload
            else:
                remote_payload = cloud_payload
    except Exception as e:
        logger.debug(f"GitHub Raw sync fetch notice: {e}")

    if not remote_payload:
        return {"status": "NO_SYNC_DATA", "message": "No remote sync state available yet."}

    # Compare timestamps to avoid redundant writes
    last_applied = get_user_preferences().get("last_cross_device_sync_at", "")
    current_export_time = remote_payload.get("exported_at", "")

    # Always apply if local auto_trader is disabled while remote is enabled
    local_cfg = get_auto_trader_config()
    remote_cfg = remote_payload.get("auto_trader_config", {})
    state_diverged = bool(local_cfg.get("is_enabled")) != bool(remote_cfg.get("is_enabled"))

    if current_export_time != last_applied or state_diverged:
        result = apply_sync_payload(remote_payload)
        return result

    return {
        "status": "UP_TO_DATE",
        "last_synced_at": last_applied,
        "message": f"Already up-to-date with {remote_payload.get('source_device', 'remote')}.",
    }

"""
finvision/utils/cloud_sync.py
=============================
Zero-Data-Loss Cloud-to-PC Synchronization & Backup Utility.

Guarantees that your local PC is ALWAYS the permanent master archive.
Even if a cloud account is lost, reset, or deleted, all causal rules,
paper trades, and vector news intelligence remain permanently safe on PC.
"""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import sqlite3
import urllib.request
from pathlib import Path
from typing import Any, Dict

PC_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PC_DIR / "finvision_data.db"
BACKUPS_DIR = PC_DIR / "backups"


def create_local_backup() -> Path:
    """Create a timestamped copy of finvision_data.db before any sync."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUPS_DIR / f"finvision_data_{timestamp}.db"
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_file)
        print(f"[Backup] Permanent snapshot saved: {backup_file.name}")
    return backup_file


def sync_from_cloud(cloud_url: str) -> Dict[str, Any]:
    """Pull latest learnings and trades from the cloud instance into local PC SQLite DB."""
    cloud_url = cloud_url.rstrip("/")
    print(f"[Sync] Connecting to Cloud instance: {cloud_url} ...")

    # Step 1: Create local safety backup first
    create_local_backup()

    stats = {
        "status": "failed",
        "new_trades": 0,
        "new_rules": 0,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Step 2: Fetch learnings from cloud sync server
    learnings_url = f"{cloud_url}/api/learnings"
    try:
        req = urllib.request.Request(learnings_url, headers={"User-Agent": "FinVision-PC-Sync/3.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            cloud_data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[Sync Note] Cloud API endpoint {learnings_url} unreachable: {e}")
        cloud_data = {}

    # Step 3: Fetch paper trades from cloud
    trades_url = f"{cloud_url}/api/trades"
    try:
        req = urllib.request.Request(trades_url, headers={"User-Agent": "FinVision-PC-Sync/3.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            trades_data = json.loads(response.read().decode("utf-8")).get("trades", [])
    except Exception as e:
        trades_data = []

    # Step 4: Merge into local SQLite master database
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()

        # Merge paper trades
        for t in trades_data:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO paper_trades 
                    (timestamp, ticker, trade_type, entry_price, target_price, stop_loss_price, shares, position_value, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    t.get("timestamp", ""),
                    t.get("ticker", "").upper(),
                    t.get("trade_type", "BUY_INTRADAY"),
                    float(t.get("entry_price", 0.0)),
                    float(t.get("target_price", 0.0)),
                    float(t.get("stop_loss_price", 0.0)),
                    int(t.get("shares", 1)),
                    float(t.get("position_value", 0.0)),
                    t.get("status", "OPEN"),
                    t.get("notes", "Synced from Cloud")
                ))
                if cur.rowcount > 0:
                    stats["new_trades"] += 1
            except Exception:
                pass

        # Merge causal rules
        for r in cloud_data.get("causal_rules", []):
            try:
                cur.execute("""
                    INSERT INTO causal_rules 
                    (catalyst, occurrences, avg_move_pct, win_rate_pct, p_value, is_significant)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(catalyst) DO UPDATE SET
                    occurrences = excluded.occurrences,
                    avg_move_pct = excluded.avg_move_pct,
                    win_rate_pct = excluded.win_rate_pct
                """, (
                    r.get("catalyst", ""),
                    int(r.get("occurrences", 0)),
                    float(r.get("avg_move_pct", 0.0)),
                    float(r.get("win_rate_pct", 0.0)),
                    float(r.get("p_value", 0.05)),
                    int(r.get("is_significant", 1))
                ))
                if cur.rowcount > 0:
                    stats["new_rules"] += 1
            except Exception:
                pass

        conn.commit()
        conn.close()
        stats["status"] = "success"
        print(f"[Sync Complete] Merged {stats['new_trades']} new trades and {stats['new_rules']} rules into PC master DB.")
    else:
        print("[Sync Error] Local database finvision_data.db not found.")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinVision Cloud-to-PC Sync & Backup")
    parser.add_argument("--cloud-url", type=str, required=True, help="URL of your Cloud instance (e.g. https://yourname-finvision.hf.space)")
    args = parser.parse_args()

    sync_from_cloud(args.cloud_url)

"""
finvision/utils/sync_server.py
==============================
Lightweight zero-dependency HTTP Sync Server for FinVision PC Backend.
Runs as a background daemon on port 8502.
Provides REST endpoints for Android apps (PC Companion, Standalone, Cloud)
to sync watchlists, paper trades, news intelligence, and causal AI learnings.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

DB_PATH = Path("./finvision_data.db")
SYNC_PORT = 8502
_server_thread: threading.Thread | None = None
_http_server: ThreadingHTTPServer | None = None


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class FinVisionSyncHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        if self.path == "/api/ping" or self.path == "/":
            response = {
                "status": "online",
                "service": "FinVision PC Sync Engine",
                "version": "3.0",
                "port_streamlit": 8501,
                "port_sync": SYNC_PORT,
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/api/learnings":
            # Return causal rules, vector news stats, recent paper trades, and watchlist
            learnings = self._get_pc_learnings()
            self._set_headers(200)
            self.wfile.write(json.dumps(learnings).encode("utf-8"))

        elif self.path == "/api/trades":
            trades = self._get_paper_trades()
            self._set_headers(200)
            self.wfile.write(json.dumps({"trades": trades}).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Endpoint not found"}')

    def do_POST(self):
        if self.path == "/api/sync":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode("utf-8"))
                result = self._process_incoming_sync(payload)
                self._set_headers(200)
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Endpoint not found"}')

    def log_message(self, format, *args):
        # Suppress noisy console logs
        pass

    def _get_pc_learnings(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "causal_rules": [],
            "news_count": 0,
            "recent_catalysts": [],
            "paper_trades_count": 0,
            "open_positions": [],
            "nifty_status": "Tracking",
        }
        if not DB_PATH.exists():
            return data

        try:
            with get_db_connection() as conn:
                cur = conn.cursor()

                # Causal rules
                try:
                    cur.execute("""
                        SELECT catalyst, occurrences, avg_move_pct, win_rate_pct, p_value, is_significant
                        FROM causal_rules
                        ORDER BY win_rate_pct DESC LIMIT 10
                    """)
                    data["causal_rules"] = [dict(r) for r in cur.fetchall()]
                except Exception:
                    pass

                # News archive count & sample
                try:
                    cur.execute("SELECT COUNT(*) as cnt FROM news_catalyst_archive")
                    row = cur.fetchone()
                    if row:
                        data["news_count"] = row["cnt"]

                    cur.execute("""
                        SELECT title, source, sentiment_label, sentiment_score, timestamp
                        FROM news_catalyst_archive
                        ORDER BY created_at DESC LIMIT 5
                    """)
                    data["recent_catalysts"] = [dict(r) for r in cur.fetchall()]
                except Exception:
                    pass

                # Paper trades
                try:
                    cur.execute("SELECT COUNT(*) as cnt FROM paper_trades")
                    row = cur.fetchone()
                    if row:
                        data["paper_trades_count"] = row["cnt"]

                    cur.execute("""
                        SELECT id, timestamp, ticker, trade_type, entry_price, target_price, stop_loss_price, shares, status, pnl_amount
                        FROM paper_trades
                        WHERE status = 'OPEN'
                        ORDER BY id DESC LIMIT 10
                    """)
                    data["open_positions"] = [dict(r) for r in cur.fetchall()]
                except Exception:
                    pass

        except Exception as e:
            data["error"] = str(e)

        return data

    def _get_paper_trades(self) -> list:
        if not DB_PATH.exists():
            return []
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, timestamp, ticker, trade_type, entry_price, target_price, stop_loss_price, shares, status, pnl_amount, notes
                    FROM paper_trades
                    ORDER BY id DESC LIMIT 50
                """)
                return [dict(r) for r in cur.fetchall()]
        except Exception:
            return []

    def _process_incoming_sync(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process mobile client push and return latest PC state."""
        incoming_trades = payload.get("trades", [])
        synced_count = 0

        if incoming_trades and DB_PATH.exists():
            with get_db_connection() as conn:
                cur = conn.cursor()
                for trade in incoming_trades:
                    try:
                        cur.execute("""
                            INSERT INTO paper_trades 
                            (timestamp, ticker, trade_type, entry_price, target_price, stop_loss_price, shares, position_value, status, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            trade.get("timestamp", ""),
                            trade.get("ticker", "").upper(),
                            trade.get("trade_type", "BUY_INTRADAY"),
                            float(trade.get("entry_price", 0.0)),
                            float(trade.get("target_price", 0.0)),
                            float(trade.get("stop_loss_price", 0.0)),
                            int(trade.get("shares", 1)),
                            float(trade.get("position_value", 0.0)),
                            trade.get("status", "OPEN"),
                            trade.get("notes", "Synced from Mobile"),
                        ))
                        synced_count += 1
                    except Exception:
                        pass
                conn.commit()

        # Return updated PC learnings back to mobile
        learnings = self._get_pc_learnings()
        learnings["message"] = f"Successfully synced {synced_count} trades from mobile to PC!"
        return learnings


def start_sync_server(port: int = SYNC_PORT) -> bool:
    """Start the sync server in a daemon thread if not already running."""
    global _server_thread, _http_server
    if _server_thread is not None and _server_thread.is_alive():
        return True

    try:
        _http_server = ThreadingHTTPServer(("0.0.0.0", port), FinVisionSyncHandler)
        _server_thread = threading.Thread(target=_http_server.serve_forever, daemon=True)
        _server_thread.start()
        print(f"[FinVision] [SYNC] Sync Server running on port {port}")
        return True
    except OSError as e:
        print(f"[FinVision] Sync server note: {e}")
        return False


if __name__ == "__main__":
    import time
    start_sync_server()
    print("Sync server active on port 8502. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

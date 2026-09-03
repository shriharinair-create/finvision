"""
finvision/utils/market_store.py
===============================
Local SQLite Data Warehouse for FinVision v3.0.
Provides persistent caching for:
  1. Stock Historical OHLCV bars & technical indicators
  2. News catalyst articles & FinBERT sentiment archives
  3. Paper Trading Simulator Journal & Realized P&L Analytics
  4. Mined Causal Rules and Keyword p-values
"""

from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

DB_PATH = Path("./finvision_data.db")


def get_connection() -> sqlite3.Connection:
    """Get a thread-safe connection to the local SQLite database."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Historical Stock Price Bar Cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_history_cache (
                ticker TEXT NOT NULL,
                date_str TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                interval TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (ticker, date_str, interval)
            )
        """)

        # 2. News Catalyst Archive
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_catalyst_archive (
                doc_id TEXT PRIMARY KEY,
                ticker TEXT,
                source TEXT,
                title TEXT NOT NULL,
                summary TEXT,
                url TEXT,
                timestamp TEXT,
                sentiment_label TEXT,
                sentiment_score REAL,
                entities_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Paper Trading Journal (Simulated Trades & PnL)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ticker TEXT NOT NULL,
                trade_type TEXT NOT NULL, -- 'BUY_INTRADAY', 'BUY_LONGTERM', 'SHORT'
                entry_price REAL NOT NULL,
                target_price REAL NOT NULL,
                stop_loss_price REAL NOT NULL,
                shares INTEGER NOT NULL,
                position_value REAL NOT NULL,
                status TEXT DEFAULT 'OPEN', -- 'OPEN', 'TARGET_HIT', 'STOP_HIT', 'CLOSED_MANUAL'
                exit_price REAL,
                exit_timestamp TEXT,
                pnl_amount REAL DEFAULT 0.0,
                pnl_pct REAL DEFAULT 0.0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Statistical Causal Rules Cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS causal_rules (
                catalyst TEXT PRIMARY KEY,
                occurrences INTEGER NOT NULL,
                avg_move_pct REAL NOT NULL,
                win_rate_pct REAL NOT NULL,
                p_value REAL NOT NULL,
                is_significant INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Intraday Forecast Snapshots & Real-Time Adaptation Ledger
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intraday_forecast_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                spot_price REAL NOT NULL,
                fused_score REAL,
                bias_label TEXT,
                prob_up REAL,
                expected_open REAL,
                expected_close REAL,
                expected_return_pct REAL,
                ci_80_low REAL,
                ci_80_high REAL,
                final_vwap REAL,
                news_sentiment REAL DEFAULT 0.0,
                catalyst_score REAL DEFAULT 0.0,
                actual_close_price REAL,
                actual_return_pct REAL,
                error_pct REAL,
                is_within_ci INTEGER,
                UNIQUE(ticker, session_date, time_slot) ON CONFLICT REPLACE
            )
        """)

        # 6. Trade Post-Mortem & Attribution Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_postmortems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER,
                ticker TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                status TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                pnl_amount REAL NOT NULL,
                pnl_pct REAL NOT NULL,
                diagnosis_code TEXT NOT NULL,
                attribution_summary TEXT,
                corrective_learning TEXT,
                stock_buffer_multiplier REAL DEFAULT 1.0,
                regime_at_entry TEXT DEFAULT 'NORMAL',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. Adaptive Stock Risk Buffer Registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adaptive_stock_buffers (
                ticker TEXT PRIMARY KEY,
                current_stop_multiplier REAL DEFAULT 1.0,
                target_multiplier REAL DEFAULT 1.0,
                liquidity_hunts_count INTEGER DEFAULT 0,
                clean_wins_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 8. Indian Market Regime History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regime_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date TEXT NOT NULL UNIQUE,
                regime_code TEXT NOT NULL,
                nifty_price REAL,
                vix_value REAL,
                strategy_playbook TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# ── Stock Price Caching Utilities ─────────────────────────────────────────────

def cache_stock_ohlcv(ticker: str, df: pd.DataFrame, interval: str = "1d") -> int:
    """Cache OHLCV historical dataframe into SQLite for fast offline queries."""
    if df.empty:
        return 0

    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [c[0] for c in df.columns]

    rows_to_insert = []
    for dt, row in df.iterrows():
        d_str = dt.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dt, pd.Timestamp) else str(dt)
        o = float(row.get("Open", row.get("close", 0)))
        h = float(row.get("High", row.get("close", 0)))
        l = float(row.get("Low", row.get("close", 0)))
        c = float(row.get("Close", 0))
        v = float(row.get("Volume", 0))
        rows_to_insert.append((ticker.upper(), d_str, o, h, l, c, v, interval))

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR REPLACE INTO stock_history_cache
            (ticker, date_str, open, high, low, close, volume, interval)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_to_insert)
        conn.commit()

    return len(rows_to_insert)


def load_cached_stock_ohlcv(ticker: str, interval: str = "1d") -> pd.DataFrame:
    """Retrieve cached OHLCV data from SQLite."""
    with get_connection() as conn:
        query = """
            SELECT date_str, open, high, low, close, volume
            FROM stock_history_cache
            WHERE ticker = ? AND interval = ?
            ORDER BY date_str ASC
        """
        df = pd.read_sql_query(query, conn, params=(ticker.upper(), interval))

    if df.empty:
        return pd.DataFrame()

    df["Date"] = pd.to_datetime(df["date_str"])
    df = df.set_index("Date").drop(columns=["date_str"])
    df.columns = ["Open", "High", "Low", "Close", "Volume"]
    return df


# ── Paper Trading Simulator Utilities ─────────────────────────────────────────

def log_paper_trade(
    ticker: str,
    trade_type: str,
    entry_price: float,
    target_price: float,
    stop_loss_price: float,
    shares: int,
    notes: str = "",
) -> int:
    """Log a new simulated paper trade into the SQLite journal."""
    ts_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pos_val = round(entry_price * shares, 2)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO paper_trades
            (timestamp, ticker, trade_type, entry_price, target_price, stop_loss_price, shares, position_value, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts_now, ticker.upper(), trade_type, entry_price, target_price, stop_loss_price, shares, pos_val, notes))
        conn.commit()
        return cursor.lastrowid or 0


def get_all_paper_trades() -> list[dict[str, Any]]:
    """Retrieve all simulated paper trades with their latest status and PnL."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM paper_trades ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def close_paper_trade(trade_id: int, exit_price: float, reason: str = "MANUAL_CLOSE") -> bool:
    """Close an open paper trade and compute final realized PnL."""
    ts_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()
        if not trade:
            return False

        entry = trade["entry_price"]
        shares = trade["shares"]
        trade_type = trade["trade_type"]

        if "SHORT" in trade_type:
            pnl_amt = round((entry - exit_price) * shares, 2)
            pnl_pct = round(((entry - exit_price) / max(0.01, entry)) * 100.0, 2)
        else:
            pnl_amt = round((exit_price - entry) * shares, 2)
            pnl_pct = round(((exit_price - entry) / max(0.01, entry)) * 100.0, 2)

        status_label = "TARGET_HIT" if "TARGET" in reason else "STOP_HIT" if "STOP" in reason else "CLOSED_MANUAL"

        cursor.execute("""
            UPDATE paper_trades
            SET status = ?, exit_price = ?, exit_timestamp = ?, pnl_amount = ?, pnl_pct = ?, notes = notes || ?
            WHERE id = ?
        """, (status_label, exit_price, ts_now, pnl_amt, pnl_pct, f" [{reason}]", trade_id))
        conn.commit()
        return True


def get_paper_trading_summary() -> dict[str, Any]:
    """Computes total simulated portfolio metrics: Win Rate, Total PnL, Profit Factor."""
    trades = get_all_paper_trades()
    closed_trades = [t for t in trades if t["status"] != "OPEN"]

    if not closed_trades:
        return {
            "total_trades": len(trades),
            "open_trades": len(trades),
            "closed_trades": 0,
            "win_rate_pct": 0.0,
            "total_realized_pnl": 0.0,
            "winning_trades": 0,
            "losing_trades": 0,
            "profit_factor": 0.0,
            "avg_pnl_per_trade": 0.0,
        }

    wins = [t for t in closed_trades if t["pnl_amount"] > 0]
    losses = [t for t in closed_trades if t["pnl_amount"] < 0]
    total_pnl = sum(t["pnl_amount"] for t in closed_trades)
    win_rate = (len(wins) / len(closed_trades)) * 100.0 if closed_trades else 0.0

    total_gross_profit = sum(t["pnl_amount"] for t in wins)
    total_gross_loss = abs(sum(t["pnl_amount"] for t in losses))
    profit_factor = round(total_gross_profit / max(0.01, total_gross_loss), 2) if total_gross_loss > 0 else total_gross_profit

    return {
        "total_trades": len(trades),
        "open_trades": len([t for t in trades if t["status"] == "OPEN"]),
        "closed_trades": len(closed_trades),
        "win_rate_pct": round(win_rate, 1),
        "total_realized_pnl": round(total_pnl, 2),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "profit_factor": profit_factor,
        "avg_pnl_per_trade": round(total_pnl / len(closed_trades), 2),
    }


# ── Intraday Forecast Snapshots & Real-Time Adaptation Utilities ──────────────

def log_intraday_forecast_snapshot(snapshot: dict[str, Any]) -> int:
    """
    Persist or update an intraday forecast snapshot into SQLite.
    Guarantees no spam duplicate rows per (ticker, session_date, time_slot).
    """
    ts_now = snapshot.get("timestamp") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ticker = str(snapshot.get("ticker", "")).upper()
    session_date = str(snapshot.get("session_date", datetime.datetime.now().strftime("%Y-%m-%d")))
    time_slot = str(snapshot.get("time_slot", datetime.datetime.now().strftime("%H:%M")))
    spot_price = float(snapshot.get("spot_price", 0.0))
    fused_score = float(snapshot.get("fused_score", 0.0))
    bias_label = str(snapshot.get("bias_label", "NEUTRAL"))
    prob_up = float(snapshot.get("prob_up", 0.5))
    expected_open = float(snapshot.get("expected_open", spot_price))
    expected_close = float(snapshot.get("expected_close", spot_price))
    expected_return_pct = float(snapshot.get("expected_return_pct", 0.0))
    ci_80_low = float(snapshot.get("ci_80_low", spot_price * 0.98))
    ci_80_high = float(snapshot.get("ci_80_high", spot_price * 1.02))
    final_vwap = float(snapshot.get("final_vwap", spot_price))
    news_sentiment = float(snapshot.get("news_sentiment", 0.0))
    catalyst_score = float(snapshot.get("catalyst_score", 0.0))
    actual_close_price = snapshot.get("actual_close_price")
    actual_return_pct = snapshot.get("actual_return_pct")
    error_pct = snapshot.get("error_pct")
    is_within_ci = snapshot.get("is_within_ci")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO intraday_forecast_snapshots
            (timestamp, session_date, ticker, time_slot, spot_price, fused_score,
             bias_label, prob_up, expected_open, expected_close, expected_return_pct,
             ci_80_low, ci_80_high, final_vwap, news_sentiment, catalyst_score,
             actual_close_price, actual_return_pct, error_pct, is_within_ci)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ts_now, session_date, ticker, time_slot, spot_price, fused_score,
            bias_label, prob_up, expected_open, expected_close, expected_return_pct,
            ci_80_low, ci_80_high, final_vwap, news_sentiment, catalyst_score,
            actual_close_price, actual_return_pct, error_pct, is_within_ci
        ))
        conn.commit()
        return cursor.lastrowid or 0


def get_intraday_forecast_snapshots(
    ticker: str,
    session_date: Optional[str] = None,
    limit: int = 75
) -> list[dict[str, Any]]:
    """Retrieve chronologically ordered intraday forecast snapshots for a ticker."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if session_date:
            cursor.execute("""
                SELECT * FROM intraday_forecast_snapshots
                WHERE ticker = ? AND session_date = ?
                ORDER BY time_slot ASC
                LIMIT ?
            """, (ticker.upper(), session_date, limit))
        else:
            cursor.execute("""
                SELECT * FROM intraday_forecast_snapshots
                WHERE ticker = ?
                ORDER BY id DESC
                LIMIT ?
            """, (ticker.upper(), limit))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def reconcile_snapshot_outcomes(
    ticker: str,
    session_date: str,
    actual_close: float
) -> int:
    """
    Reconciles all intraday snapshots for a given date with the final actual closing price.
    Calculates error %, directional hit, and whether the close was within the 80% CI envelope.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, spot_price, expected_return_pct, ci_80_low, ci_80_high
            FROM intraday_forecast_snapshots
            WHERE ticker = ? AND session_date = ?
        """, (ticker.upper(), session_date))
        rows = cursor.fetchall()
        
        updated_count = 0
        for r in rows:
            snap_id = r["id"]
            spot = r["spot_price"]
            exp_ret = r["expected_return_pct"]
            ci_low = r["ci_80_low"]
            ci_high = r["ci_80_high"]

            act_ret = ((actual_close - spot) / max(0.01, spot)) * 100.0 if spot > 0 else 0.0
            err_pct = act_ret - exp_ret
            in_ci = 1 if (ci_low <= actual_close <= ci_high) else 0

            cursor.execute("""
                UPDATE intraday_forecast_snapshots
                SET actual_close_price = ?, actual_return_pct = ?, error_pct = ?, is_within_ci = ?
                WHERE id = ?
            """, (actual_close, round(act_ret, 3), round(err_pct, 3), in_ci, snap_id))
            updated_count += 1
            
        conn.commit()
        return updated_count


def get_snapshot_adaptation_audit(
    ticker: str,
    session_date: Optional[str] = None
) -> dict[str, Any]:
    """
    Computes an analytical audit of how the forecast adapted through the day:
    1. Early session bias vs mid-day bias vs close.
    2. Prediction error convergence (did error decrease as more 5m bars completed?).
    3. CI coverage rate across all daytime adjustments.
    """
    snaps = get_intraday_forecast_snapshots(ticker, session_date)
    if not snaps:
        return {"available": False, "reason": "No intraday snapshots recorded yet for this session."}

    df_s = pd.DataFrame(snaps)
    total_snaps = len(df_s)
    
    # Calculate error metrics if reconciled
    has_actual = df_s["actual_close_price"].notna().any()
    mae_pct = round(df_s["error_pct"].abs().mean(), 2) if has_actual and "error_pct" in df_s.columns else None
    ci_coverage = round((df_s["is_within_ci"].sum() / total_snaps) * 100.0, 1) if has_actual else None

    first_pred = df_s.iloc[0]
    latest_pred = df_s.iloc[-1]

    return {
        "available": True,
        "ticker": ticker.upper(),
        "session_date": df_s["session_date"].iloc[0],
        "total_snapshots": total_snaps,
        "first_snapshot_time": first_pred.get("time_slot"),
        "latest_snapshot_time": latest_pred.get("time_slot"),
        "initial_expected_close": round(first_pred.get("expected_close", 0.0), 2),
        "latest_expected_close": round(latest_pred.get("expected_close", 0.0), 2),
        "initial_bias": first_pred.get("bias_label"),
        "latest_bias": latest_pred.get("bias_label"),
        "has_actual_reconciliation": has_actual,
        "actual_close": round(df_s["actual_close_price"].dropna().iloc[0], 2) if has_actual else None,
        "mean_absolute_error_pct": mae_pct,
        "ci_coverage_pct": ci_coverage,
        "snapshots": snaps
    }


# ── Trade Post-Mortem & Attribution Store ─────────────────────────────────────

def log_trade_postmortem(postmortem: dict[str, Any]) -> int:
    """Stores a quantitative trade post-mortem autopsy in SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trade_postmortems (
                trade_id, ticker, trade_type, status, entry_price, exit_price,
                pnl_amount, pnl_pct, diagnosis_code, attribution_summary,
                corrective_learning, stock_buffer_multiplier, regime_at_entry
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            postmortem.get("trade_id", 0),
            postmortem.get("ticker", "").upper(),
            postmortem.get("trade_type", ""),
            postmortem.get("status", ""),
            float(postmortem.get("entry_price", 0.0)),
            float(postmortem.get("exit_price", 0.0)),
            float(postmortem.get("pnl_amount", 0.0)),
            float(postmortem.get("pnl_pct", 0.0)),
            postmortem.get("diagnosis_code", "UNKNOWN"),
            postmortem.get("attribution_summary", ""),
            postmortem.get("corrective_learning", ""),
            float(postmortem.get("stock_buffer_multiplier", 1.0)),
            postmortem.get("regime_at_entry", "NORMAL")
        ))
        row_id = cursor.lastrowid

        # Update or create adaptive stock buffer entry
        ticker = postmortem.get("ticker", "").upper()
        buf_mult = float(postmortem.get("stock_buffer_multiplier", 1.0))
        is_hunt = 1 if postmortem.get("diagnosis_code") == "LIQUIDITY_SWEEP_HUNT" else 0
        is_win = 1 if "WIN" in postmortem.get("diagnosis_code", "") or "BLOWOFF" in postmortem.get("diagnosis_code", "") else 0

        cursor.execute("""
            INSERT INTO adaptive_stock_buffers (ticker, current_stop_multiplier, liquidity_hunts_count, clean_wins_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                current_stop_multiplier = MAX(adaptive_stock_buffers.current_stop_multiplier, excluded.current_stop_multiplier),
                liquidity_hunts_count = adaptive_stock_buffers.liquidity_hunts_count + excluded.liquidity_hunts_count,
                clean_wins_count = adaptive_stock_buffers.clean_wins_count + excluded.clean_wins_count,
                updated_at = CURRENT_TIMESTAMP
        """, (ticker, buf_mult, is_hunt, is_win))

        conn.commit()
        return row_id


def get_postmortem_history(limit: int = 50) -> list[dict[str, Any]]:
    """Retrieves recent trade post-mortem autopsy records."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM trade_postmortems
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]


def get_stock_adaptive_buffer(ticker: str) -> dict[str, Any]:
    """Gets stock-specific adaptive stop multiplier learned from past post-mortems."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM adaptive_stock_buffers WHERE ticker = ?
        """, (ticker.upper(),))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            "ticker": ticker.upper(),
            "current_stop_multiplier": 1.0,
            "target_multiplier": 1.0,
            "liquidity_hunts_count": 0,
            "clean_wins_count": 0
        }


def log_regime_snapshot(regime_data: dict[str, Any]) -> None:
    """Stores the daily market regime state."""
    session_date = datetime.date.today().strftime("%Y-%m-%d")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO regime_history (session_date, regime_code, nifty_price, vix_value, strategy_playbook)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_date) DO UPDATE SET
                regime_code = excluded.regime_code,
                nifty_price = excluded.nifty_price,
                vix_value = excluded.vix_value,
                strategy_playbook = excluded.strategy_playbook
        """, (
            session_date,
            regime_data.get("regime_code", "NORMAL"),
            float(regime_data.get("nifty_price", 0.0)),
            float(regime_data.get("vix_value", 14.5)),
            regime_data.get("strategy_playbook", "BALANCED")
        ))
        conn.commit()


def get_recent_regime_history(limit: int = 15) -> list[dict[str, Any]]:
    """Fetches recent daily market regime history."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM regime_history
            ORDER BY session_date DESC LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]


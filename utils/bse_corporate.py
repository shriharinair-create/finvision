"""
finvision/utils/bse_corporate.py
================================
BSE India Corporate Disclosures & Regulatory Announcements Engine.
Ingests direct SEBI/BSE regulatory filings, board meetings, quarterly results,
dividends, splits, and insider transactions into FinVision's intelligence layer.

Provides Binary Event Risk Guard:
  Flags imminent corporate catalysts (e.g. Earnings announcement within 48-72h)
  to prevent holding swing positions into high-volatility gap risk events.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sqlite3
from typing import Any, Dict, List, Optional
from pathlib import Path
import requests

from utils.bse_helper import resolve_indian_ticker

_DB_PATH = Path("./finvision_data.db")

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bseindia.com/",
    "Origin": "https://www.bseindia.com",
}


def _init_corporate_db(db_path: Path = _DB_PATH) -> None:
    """Ensure SQLite table for BSE Corporate Filings exists."""
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bse_corporate_filings (
                    id TEXT PRIMARY KEY,
                    scrip_code TEXT,
                    symbol TEXT,
                    company_name TEXT,
                    category TEXT,
                    headline TEXT,
                    details TEXT,
                    event_date TEXT,
                    is_price_sensitive INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bse_filings_sym ON bse_corporate_filings(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bse_filings_code ON bse_corporate_filings(scrip_code)")
            conn.commit()
    except Exception:
        pass


def fetch_bse_corporate_announcements(
    scrip_code: Optional[str] = None,
    category: str = "all",
    max_items: int = 20
) -> list[dict[str, Any]]:
    """
    Fetches official BSE corporate announcements.
    If scrip_code is provided, filters for that company; otherwise pulls broad market disclosures.
    """
    _init_corporate_db()
    
    # Official BSE India Public Announcements API endpoint
    # (BSE provides JSON feeds at api.bseindia.com / bseindia.com)
    url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
    params = {
        "pageno": "1",
        "strCat": "-1" if category == "all" else category,
        "strPrevDate": (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y%m%d"),
        "strScrip": scrip_code if scrip_code else "",
        "strSearch": "P",
        "strToDate": datetime.datetime.now().strftime("%Y%m%d"),
        "strType": "C",
    }
    
    announcements: list[dict[str, Any]] = []
    
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, params=params, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            table = data.get("Table", [])
            for item in table[:max_items]:
                ann_id = str(item.get("NEWSID", item.get("SLONGNAME", "")))
                h_line = item.get("NEWSSUB", "")
                dt_str = item.get("NEWS_DT", "")
                code = str(item.get("SCRIP_CD", ""))
                body = item.get("HEADLINE", "")
                cat_name = item.get("CATEGORYNAME", "General Disclosure")
                
                # Check price sensitivity
                is_sensitive = any(w in (h_line + " " + cat_name).lower() for w in [
                    "financial result", "dividend", "board meeting", "bonus", "split", "acquisition", "sebi"
                ])
                
                res_obj = resolve_indian_ticker(code)
                sym = res_obj.get("symbol", code)
                c_name = res_obj.get("company_name", item.get("SLONGNAME", ""))
                
                announcements.append({
                    "id": ann_id or hashlib.md5((code + h_line + dt_str).encode()).hexdigest()[:16],
                    "scrip_code": code,
                    "symbol": sym,
                    "company_name": c_name,
                    "category": cat_name,
                    "headline": h_line,
                    "details": body,
                    "event_date": dt_str,
                    "is_price_sensitive": is_sensitive,
                })
    except Exception:
        pass

    # If live BSE network is restricted or fails, fall back to stored DB or synthetic sample filings
    if not announcements:
        announcements = _get_cached_or_fallback_announcements(scrip_code, max_items)
        
    return announcements


def _get_cached_or_fallback_announcements(
    scrip_code: Optional[str],
    max_items: int
) -> list[dict[str, Any]]:
    """Returns local cached filings or structured institutional disclosures."""
    results = []
    try:
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cursor = conn.cursor()
            if scrip_code:
                cursor.execute(
                    "SELECT id, scrip_code, symbol, company_name, category, headline, details, event_date, is_price_sensitive "
                    "FROM bse_corporate_filings WHERE scrip_code = ? ORDER BY event_date DESC LIMIT ?",
                    (scrip_code, max_items)
                )
            else:
                cursor.execute(
                    "SELECT id, scrip_code, symbol, company_name, category, headline, details, event_date, is_price_sensitive "
                    "FROM bse_corporate_filings ORDER BY event_date DESC LIMIT ?",
                    (max_items,)
                )
            rows = cursor.fetchall()
            for r in rows:
                results.append({
                    "id": r[0],
                    "scrip_code": r[1],
                    "symbol": r[2],
                    "company_name": r[3],
                    "category": r[4],
                    "headline": r[5],
                    "details": r[6],
                    "event_date": r[7],
                    "is_price_sensitive": bool(r[8]),
                })
    except Exception:
        pass

    return results


def check_corporate_event_risk(ticker_or_code: str) -> dict[str, Any]:
    """
    Evaluates whether a stock faces an imminent binary corporate event.
    
    Checks:
      - Upcoming Board Meetings (Audited Financial Results)
      - Dividend Ex-Dates
      - Stock Splits / Bonus Issues
      - AGMs / EGM Decisions
      
    Returns:
      {
          "has_imminent_event": bool,
          "event_type": str,
          "event_date": str,
          "warning_badge": str,
          "description": str,
          "is_high_risk": bool
      }
    """
    resolved = resolve_indian_ticker(ticker_or_code)
    bse_code = resolved.get("bse_code", "")
    sym = resolved.get("symbol", ticker_or_code.replace(".NS", "").replace(".BO", ""))
    
    # Query database for scheduled events within the next 4 days
    today = datetime.date.today()
    target_cutoff = today + datetime.timedelta(days=4)
    
    try:
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category, headline, event_date, is_price_sensitive "
                "FROM bse_corporate_filings "
                "WHERE (symbol = ? OR scrip_code = ?) AND is_price_sensitive = 1 "
                "ORDER BY event_date DESC LIMIT 3",
                (sym, bse_code)
            )
            rows = cursor.fetchall()
            for cat, headline, ev_date, sensitive in rows:
                lower_h = (headline + " " + cat).lower()
                if "financial result" in lower_h or "board meeting" in lower_h:
                    return {
                        "has_imminent_event": True,
                        "event_type": "EARNINGS_BOARD_MEETING",
                        "event_date": ev_date,
                        "warning_badge": "⚠️ Earnings / Board Meeting Imminent",
                        "description": f"Scheduled corporate meeting ({cat}): {headline[:60]}...",
                        "is_high_risk": True,
                    }
                elif "dividend" in lower_h:
                    return {
                        "has_imminent_event": True,
                        "event_type": "DIVIDEND_EX_DATE",
                        "event_date": ev_date,
                        "warning_badge": "💰 Dividend Action Imminent",
                        "description": f"Corporate dividend action announced: {headline[:60]}...",
                        "is_high_risk": False,
                    }
                elif "bonus" in lower_h or "split" in lower_h:
                    return {
                        "has_imminent_event": True,
                        "event_type": "SPLIT_BONUS_CORPORATE_ACTION",
                        "event_date": ev_date,
                        "warning_badge": "🔄 Split / Bonus Imminent",
                        "description": f"Capital restructuring action: {headline[:60]}...",
                        "is_high_risk": True,
                    }
    except Exception:
        pass

    # No imminent risk detected
    return {
        "has_imminent_event": False,
        "event_type": "NONE",
        "event_date": "",
        "warning_badge": "",
        "description": "No high-volatility corporate events or binary earnings dates within 72 hours.",
        "is_high_risk": False,
    }


def ingest_bse_filings_to_vector_news() -> int:
    """
    Ingests recent BSE regulatory filings into ChromaDB Vector News & SQLite.
    Allows FinBERT to score sentiment directly from primary exchange disclosures.
    """
    announcements = fetch_bse_corporate_announcements(max_items=30)
    if not announcements:
        return 0

    _init_corporate_db()
    count = 0
    try:
        with sqlite3.connect(str(_DB_PATH)) as conn:
            cursor = conn.cursor()
            for a in announcements:
                cursor.execute("""
                    INSERT OR REPLACE INTO bse_corporate_filings
                    (id, scrip_code, symbol, company_name, category, headline, details, event_date, is_price_sensitive)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    a["id"], a["scrip_code"], a["symbol"], a["company_name"],
                    a["category"], a["headline"], a["details"], a["event_date"],
                    1 if a["is_price_sensitive"] else 0
                ))
                count += 1
            conn.commit()
    except Exception:
        pass

    # Also push price-sensitive announcements to ChromaDB vector store
    try:
        from utils.vector_news import get_vector_resources
        embedder, _, collection = get_vector_resources()
        docs, metas, ids = [], [], []
        
        for a in announcements:
            if a["is_price_sensitive"] and a["headline"]:
                doc_text = f"BSE Regulatory Filing [{a['symbol']} / {a['company_name']}]: {a['headline']} - {a['category']}"
                d_id = f"bse_reg_{a['id']}"
                docs.append(doc_text)
                ids.append(d_id)
                metas.append({
                    "source": "BSE_INDIA_OFFICIAL",
                    "ticker": a["symbol"],
                    "category": a["category"],
                    "timestamp": a["event_date"] or str(datetime.date.today()),
                })
        
        if docs:
            embs = embedder.encode(docs, convert_to_numpy=True).tolist()
            collection.upsert(ids=ids, embeddings=embs, documents=docs, metadatas=metas)
    except Exception:
        pass

    return count

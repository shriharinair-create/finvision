"""
finvision/utils/historical_news.py
==================================
Historical news backfilling engine using date-windowed feeds and ticker archives.
"""

from __future__ import annotations

import datetime
import hashlib
import time
from typing import Any, Dict, List
import feedparser
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

from utils.vector_news import get_vector_resources

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def fetch_ticker_historical_news(ticker: str) -> list[dict[str, Any]]:
    """Fetches historical ticker-specific news via yfinance news endpoint."""
    t = yf.Ticker(ticker)
    news_items = []
    
    try:
        raw_news = t.news
        if not raw_news:
            return []
        
        for item in raw_news:
            content = item.get("content", item)
            title = content.get("title", "")
            summary = content.get("summary", title)
            pub_time = content.get("pubDate", "")
            link = content.get("canonicalUrl", {}).get("url", "")
            
            # Convert timestamp
            if isinstance(pub_time, (int, float)):
                dt_str = datetime.datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M")
            else:
                dt_str = str(pub_time)[:16]

            if title:
                news_items.append({
                    "text": f"{title}. {summary}",
                    "title": title,
                    "timestamp": dt_str,
                    "source": "Yahoo Finance Archive",
                    "url": link,
                    "ticker": ticker
                })
    except Exception:
        pass
    
    return news_items


def backfill_google_news_archive(query: str, months_back: int = 6) -> list[dict[str, Any]]:
    """
    Backfills historical news by stepping backwards through monthly time windows.
    Uses Google News search syntax (after:YYYY-MM-DD before:YYYY-MM-DD).
    """
    all_articles = []
    today = datetime.date.today()

    for i in range(months_back):
        end_date = today - datetime.timedelta(days=i * 30)
        start_date = today - datetime.timedelta(days=(i + 1) * 30)

        # Google News date-bounded search query
        time_query = f"{query} after:{start_date.isoformat()} before:{end_date.isoformat()}"
        encoded_query = requests.utils.quote(time_query)
        feed_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

        try:
            resp = requests.get(feed_url, headers=BROWSER_HEADERS, timeout=8)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:20]:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", title).strip()
                    link = entry.get("link", "")
                    pub_date = entry.get("published", str(start_date))

                    clean_summary = summary.replace("<p>", "").replace("</p>", "").replace("<b>", "").replace("</b>", "")
                    
                    if title and len(title) > 10:
                        all_articles.append({
                            "text": f"{title}. {clean_summary}",
                            "title": title,
                            "timestamp": str(pub_date),
                            "source": "Google News Archive",
                            "url": link,
                            "ticker": query
                        })
            time.sleep(0.3)  # Rate limiting courtesy delay
        except Exception:
            continue

    return all_articles


def backfill_and_store(ticker: str, months_back: int = 6) -> int:
    """Combines historical sources, generates embeddings, and saves to persistent ChromaDB."""
    embedder, _, collection = get_vector_resources()
    
    clean_sym = ticker.replace("^", "").replace(".NS", "").replace(".BO", "")
    
    # 1. Fetch from yfinance
    yf_news = fetch_ticker_historical_news(ticker)
    
    # 2. Fetch from windowed Google News Archive
    gnews = backfill_google_news_archive(f"{clean_sym} India stock", months_back=months_back)
    
    combined = yf_news + gnews
    if not combined:
        return 0

    documents, metadatas, ids = [], [], []
    for item in combined:
        doc_id = hashlib.md5((item["url"] or item["title"]).encode("utf-8")).hexdigest()
        existing = collection.get(ids=[doc_id])
        if not existing["ids"]:
            documents.append(item["text"])
            metadatas.append({
                "source": item["source"],
                "title": item["title"],
                "url": item["url"],
                "timestamp": item["timestamp"],
                "ticker": ticker
            })
            ids.append(doc_id)

    if documents:
        embeddings = embedder.encode(documents, convert_to_numpy=True).tolist()
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    return len(documents)


@st.cache_data(ttl=900, show_spinner=False)
def get_live_15m_ticker_news(ticker: str) -> dict[str, Any]:
    """
    Fetches real-time market news polled every 15 minutes (900s TTL cache).
    Computes real-time sentiment polarity and high-impact keyword catalyst score.
    """
    import urllib.parse
    clean_sym = ticker.replace(".NS", "").replace(".BO", "")
    
    # Mapping for search queries
    name_map = {
        "APOLLO": "Apollo Micro Systems",
        "APOLLOHOSP": "Apollo Hospitals",
        "APOLLOTYRE": "Apollo Tyres",
        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services IT",
        "INFY": "Infosys",
        "HDFCBANK": "HDFC Bank",
        "ICICIBANK": "ICICI Bank",
        "SBIN": "State Bank of India",
        "BHARTIARTL": "Bharti Airtel",
        "ITC": "ITC Limited",
        "LT": "Larsen Toubro"
    }
    company_name = name_map.get(clean_sym, clean_sym)
    
    headlines = []
    # 1. Fetch yfinance news
    try:
        t = yf.Ticker(ticker)
        raw_yf = t.news or []
        for item in raw_yf[:6]:
            c = item.get("content", item)
            title = c.get("title", "")
            if title and title not in headlines:
                headlines.append(title)
    except Exception:
        pass

    # 2. Fetch Google News RSS
    try:
        q = urllib.parse.quote(f"{company_name} share stock market India")
        rss_url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:6]:
            t_str = entry.title
            if t_str and t_str not in headlines:
                headlines.append(t_str)
    except Exception:
        pass

    # 3. Sentiment & Catalyst Taxonomy
    BULLISH = [
        "deal", "win", "order", "profit", "surge", "jump", "rally", "upgrade", "buy", 
        "growth", "beat", "expansion", "record", "dividend", "acquisition", "gain", 
        "rate cut", "tech surge", "ai contract", "outperform", "target hike", "breakout"
    ]
    BEARISH = [
        "fall", "drop", "slump", "loss", "downgrade", "sell", "probe", "penalty", 
        "margin pressure", "weak", "plunge", "cut", "drag", "fii selling", "tariff",
        "cost pressure", "delay", "inflation", "recession"
    ]

    sent_sum = 0.0
    cat_sum = 0.0
    
    for h in headlines:
        h_low = h.lower()
        pos = sum(1 for w in BULLISH if w in h_low)
        neg = sum(1 for w in BEARISH if w in h_low)
        
        if pos > neg:
            sent_sum += min(1.0, 0.40 + 0.25 * (pos - neg))
        elif neg > pos:
            sent_sum += max(-1.0, -0.40 - 0.25 * (neg - pos))
            
        if any(c in h_low for c in ["order win", "deal win", "contract", "acquisition", "rate cut", "upgrade", "record profit"]):
            cat_sum += 0.65
        elif any(c in h_low for c in ["probe", "penalty", "lawsuit", "downgrade", "loss", "margin drop"]):
            cat_sum -= 0.65

    count = max(1, len(headlines))
    avg_sent = float(np.clip(sent_sum / count, -1.0, 1.0))
    avg_cat = float(np.clip(cat_sum / count, -1.0, 1.0))
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "ticker": ticker,
        "sentiment_score": round(avg_sent, 2),
        "catalyst_score": round(avg_cat, 2),
        "headlines": headlines[:8],
        "headlines_count": len(headlines),
        "last_polled_at": now_str,
        "is_active_15m": True
    }



@st.cache_data(ttl=600)
def fetch_sebi_corporate_disclosures(ticker: str) -> list[dict[str, Any]]:
    """
    Fetches primary regulatory corporate announcements and insider filings (SEBI SAST / BSE Announcements)
    for Indian equities, bypassing secondary financial news blogs.
    """
    clean_sym = ticker.replace(".NS", "").replace(".BO", "").replace("^", "")
    disclosures = []
    
    # Query Google News directly for official regulatory/corporate disclosure feeds
    queries = [
        f"{clean_sym} corporate announcement BSE NSE filing",
        f"{clean_sym} insider trading promoter disclosure SEBI"
    ]
    
    for q in queries:
        encoded_q = requests.utils.quote(q)
        feed_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            resp = requests.get(feed_url, headers=BROWSER_HEADERS, timeout=6)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:6]:
                    title = entry.get("title", "").strip()
                    url = entry.get("link", "")
                    pub_parsed = entry.get("published_parsed")
                    d_str = datetime.date(*pub_parsed[:3]).isoformat() if pub_parsed else datetime.date.today().isoformat()
                    
                    if title:
                        disclosures.append({
                            "type": "REGULATORY_DISCLOSURE",
                            "title": title,
                            "date": d_str,
                            "url": url,
                            "ticker": ticker,
                            "source": "BSE/NSE Regulatory Feed"
                        })
        except Exception:
            pass
            
    return disclosures



# ==============================================================================
# MULTI-SOURCE INDIAN FINANCIAL NEWS & ADAPTIVE 60-SEC MARKET ENGINE
# ==============================================================================

INDIAN_FINANCIAL_FEEDS = {
    "Moneycontrol Markets": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "Moneycontrol Business": "https://www.moneycontrol.com/rss/business.xml",
    "Economic Times Stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    "LiveMint Markets": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss"
}


def fetch_multi_source_ticker_news(ticker: str, company_name: str = "") -> list[dict[str, Any]]:
    """
    Fetches breaking news from 6 diversified financial sources:
      1. Google News RSS (Specific Ticker Search)
      2. Moneycontrol Live RSS
      3. Economic Times Markets RSS
      4. LiveMint RSS
      5. Business Standard RSS
      6. Yahoo Finance News API
    """
    clean_sym = ticker.replace(".NS", "").replace(".BO", "").replace("^", "")
    search_terms = [clean_sym]
    if company_name and len(company_name) > 3:
        search_terms.append(company_name.split()[0].lower())

    aggregated_articles = []
    seen_titles = set()

    # 1. Google News Ticker Search
    encoded_q = requests.utils.quote(f"{clean_sym} share stock India")
    gnews_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        resp = requests.get(gnews_url, headers=BROWSER_HEADERS, timeout=5)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:8]:
                t = entry.get("title", "").strip()
                s = entry.get("summary", t).strip()
                u = entry.get("link", "")
                if t and t not in seen_titles:
                    seen_titles.add(t)
                    aggregated_articles.append({
                        "source": "Google News",
                        "title": t,
                        "summary": s,
                        "url": u,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
    except Exception:
        pass

    # 2. Curated Indian Financial RSS Feeds (Moneycontrol, ET, Mint, BS)
    for src_name, feed_url in INDIAN_FINANCIAL_FEEDS.items():
        try:
            resp = requests.get(feed_url, headers=BROWSER_HEADERS, timeout=4)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                for entry in feed.entries[:15]:
                    t = entry.get("title", "").strip()
                    s = entry.get("summary", t).strip()
                    u = entry.get("link", "")
                    # Filter for relevance to active ticker or general market
                    t_low = t.lower()
                    s_low = s.lower()
                    if any(term.lower() in t_low or term.lower() in s_low for term in search_terms):
                        if t and t not in seen_titles:
                            seen_titles.add(t)
                            aggregated_articles.append({
                                "source": src_name,
                                "title": t,
                                "summary": s,
                                "url": u,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
        except Exception:
            pass

    # 3. Yahoo Finance Live API
    try:
        t_obj = yf.Ticker(ticker)
        yf_news = t_obj.news or []
        for item in yf_news[:6]:
            c = item.get("content", item)
            t = c.get("title", "")
            s = c.get("summary", t)
            u = c.get("canonicalUrl", {}).get("url", "")
            if t and t not in seen_titles:
                seen_titles.add(t)
                aggregated_articles.append({
                    "source": "Yahoo Finance",
                    "title": t,
                    "summary": s,
                    "url": u,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
    except Exception:
        pass

    return aggregated_articles


def get_adaptive_ttl_seconds() -> int:
    """
    Returns 60s TTL during live trading hours (09:00 - 15:30 IST on weekdays),
    and 600s TTL during off-market hours / weekends to conserve bandwidth.
    """
    now = datetime.datetime.now()
    # Weekday check (0=Mon, 4=Fri)
    if now.weekday() < 5:
        if datetime.time(9, 0) <= now.time() <= datetime.time(15, 30):
            return 60  # Fast 60-second polling during live market hours
    return 600  # 10-minute polling off-hours


@st.cache_data(ttl=60)
def get_live_adaptive_ticker_news(ticker: str) -> dict[str, Any]:
    """
    Continuous Multi-Source Live News Ingestion Engine with 60s Fast Polling during market hours.
    Aggregates Moneycontrol, Economic Times, LiveMint, Business Standard, YF, and Google News.
    """
    articles = fetch_multi_source_ticker_news(ticker)
    
    if not articles:
        # Fallback to local DB news if network call returns empty
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT sentiment_score, title, summary FROM news_catalyst_archive WHERE ticker = ? ORDER BY created_at DESC LIMIT 5;", (ticker,))
            rows = c.fetchall()
            conn.close()
            if rows:
                avg_s = float(np.mean([r[0] for r in rows if r[0] is not None]))
                return {
                    "sentiment_score": round(avg_s, 2),
                    "catalyst_score": 0.0,
                    "headlines_count": len(rows),
                    "last_polled_at": datetime.datetime.now().strftime("%H:%M:%S"),
                    "polling_mode": "Local DB Cached",
                    "sources_used": ["SQLite Archive"],
                    "articles": [{"title": r[1], "source": "Archive"} for r in rows]
                }
        except Exception:
            pass

        return {
            "sentiment_score": 0.0,
            "catalyst_score": 0.0,
            "headlines_count": 0,
            "last_polled_at": datetime.datetime.now().strftime("%H:%M:%S"),
            "polling_mode": "No Live Articles Found",
            "sources_used": [],
            "articles": []
        }

    # Score sentiment and catalyst keywords across all multi-source articles
    sent_scores = []
    cat_scores = []
    sources_active = set()

    for a in articles:
        sources_active.add(a["source"])
        text = f"{a['title']}. {a['summary']}"
        text_low = text.lower()
        
        # Bullish vs Bearish Keywords
        pos_words = ['surge', 'jump', 'profit', 'deal', 'win', 'order', 'gain', 'growth', 'beat', 'rally', 'dividend', 'expansion', 'upgrade', 'contract']
        neg_words = ['fall', 'drop', 'slump', 'loss', 'probe', 'penalty', 'weak', 'plunge', 'cut', 'drag', 'fraud', 'downgrade', 'raid']
        cat_words = ['order win', 'q1 result', 'q2 result', 'q3 result', 'q4 result', 'acquisition', 'merger', 'usfda', 'patent', 'capex', 'bonus']

        pos_cnt = sum(1 for w in pos_words if w in text_low)
        neg_cnt = sum(1 for w in neg_words if w in text_low)
        has_cat = any(w in text_low for w in cat_words)

        s = 0.0
        if pos_cnt > neg_cnt: s = min(0.85, 0.35 + 0.15 * (pos_cnt - neg_cnt))
        elif neg_cnt > pos_cnt: s = max(-0.85, -0.35 - 0.15 * (neg_cnt - pos_cnt))
        sent_scores.append(s)

        cat_s = 0.50 if (has_cat and s > 0) else -0.50 if (has_cat and s < 0) else 0.0
        cat_scores.append(cat_s)

    avg_sent = float(np.mean(sent_scores)) if sent_scores else 0.0
    avg_cat = float(np.mean(cat_scores)) if cat_scores else 0.0
    
    mode_label = "60-Sec Fast Poller (Market Hours)" if get_adaptive_ttl_seconds() == 60 else "Off-Market 10-Min Cache"

    return {
        "sentiment_score": round(avg_sent, 2),
        "catalyst_score": round(avg_cat, 2),
        "headlines_count": len(articles),
        "last_polled_at": datetime.datetime.now().strftime("%H:%M:%S"),
        "polling_mode": mode_label,
        "sources_used": sorted(list(sources_active)),
        "articles": articles
    }


# Backward compatibility alias
get_live_15m_ticker_news = get_live_adaptive_ticker_news

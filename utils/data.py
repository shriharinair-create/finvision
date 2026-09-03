"""
Core data pipeline: yfinance fetching, caching, candlestick math, sentiment, scoring.
All heavy operations are wrapped in st.cache_data for performance.
"""

from __future__ import annotations

import re
import time
import warnings
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import requests
import streamlit as st

from utils import indicators as ti

warnings.filterwarnings("ignore")

# ── Constants ────────────────────────────────────────────────────────────────

MANDATORY_TICKERS = [
    # High-momentum / frequently-traded names that should always be present
    # even if the live NSE fetch fails or a stock gets rebalanced out of an
    # index mid-cycle.
    "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ZOMATO.NS", "SUZLON.NS", "JIOFIN.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    "INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
    "RELIANCE.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TATAPOWER.NS",
    "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS",
    "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS",
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
    "LT.NS", "ULTRACEMCO.NS", "GRASIM.NS", "SHREECEM.NS",
    "ASIANPAINT.NS", "TITAN.NS", "DMART.NS", "TRENT.NS",
    "ONGC.NS", "COALINDIA.NS", "NTPC.NS", "POWERGRID.NS",
    "BHARTIARTL.NS", "VEDL.NS", "JSWSTEEL.NS", "HINDALCO.NS",
    "PNB.NS", "BANKBARODA.NS", "CANBK.NS", "IDFCFIRSTB.NS",
    "PAYTM.NS", "NYKAA.NS", "POLICYBZR.NS", "DELHIVERY.NS",
    "IRFC.NS", "RVNL.NS", "IRCTC.NS", "INDIGO.NS",
]

NIFTY_CSV_URL = (
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
)

# Weighted lexicon: words carry different signal strength (1.0 = strong, 0.5 = mild)
SENTIMENT_POSITIVE_WORDS = {
    "surge": 1.0, "rally": 1.0, "soar": 1.0, "jump": 0.8, "beat": 1.0,
    "gain": 0.6, "record": 0.8, "high": 0.4, "rise": 0.6, "grow": 0.5,
    "strong": 0.6, "bullish": 1.0, "upgrade": 1.0, "buy": 0.7,
    "positive": 0.5, "boost": 0.7, "expansion": 0.6, "acquisition": 0.5,
    "dividend": 0.4, "outperform": 0.9, "breakout": 0.8, "recovery": 0.7,
    "milestone": 0.5, "win": 0.6, "success": 0.5, "launch": 0.4,
    "revenue": 0.3, "profit": 0.8, "rebound": 0.7, "upbeat": 0.6,
    "optimistic": 0.6, "exceeds": 0.7, "robust": 0.6, "blockbuster": 0.9,
}

SENTIMENT_NEGATIVE_WORDS = {
    "crash": 1.0, "plunge": 1.0, "fall": 0.6, "loss": 0.7, "miss": 0.8,
    "drop": 0.6, "decline": 0.6, "weak": 0.6, "bearish": 1.0,
    "downgrade": 1.0, "sell": 0.5, "negative": 0.5, "probe": 0.8,
    "fraud": 1.0, "scam": 1.0, "debt": 0.5, "layoff": 0.8,
    "recession": 0.9, "warning": 0.7, "caution": 0.5, "risk": 0.3,
    "penalty": 0.7, "fine": 0.6, "regulatory": 0.4, "investigation": 0.8,
    "default": 0.9, "bankruptcy": 1.0, "slump": 0.8, "tumble": 0.8,
    "slash": 0.7, "cut": 0.5, "concern": 0.4, "lawsuit": 0.7,
    "scrutiny": 0.5, "underperform": 0.8, "shortfall": 0.7, "halt": 0.6,
}

NEGATION_WORDS = {"not", "no", "never", "without", "isn't", "wasn't", "aren't", "didn't"}


# ── Watchlist loading ────────────────────────────────────────────────────────

@st.cache_data(ttl=86_400, show_spinner="Loading Nifty 500 index...")
def load_nifty500_watchlist() -> tuple[list[str], dict]:
    """
    Fetch Nifty 500 CSV from NSE, merge mandatory tickers, return unique list.

    Returns (tickers, status) where status reports exactly what happened —
    NSE's archive server is known to intermittently block non-browser
    requests (403s, redirects to an access-denied page), and that failure
    was previously swallowed silently by a bare `except: pass`, which meant
    the app would quietly fall back to a ~12-ticker list with zero
    indication anything had gone wrong. Now the caller (the sidebar/scanner
    UI) can show the real fetch status so a missing ticker is explainable
    rather than mysterious.
    """
    tickers: list[str] = list(MANDATORY_TICKERS)
    status = {
        "live_fetch_succeeded": False,
        "live_tickers_added": 0,
        "http_status": None,
        "error": None,
    }

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/csv,application/csv,text/plain,*/*",
            "Referer": "https://www.nseindia.com/",
        }
        # NSE often requires an initial visit to set session cookies before
        # the archive endpoint will respond to a script instead of a 403.
        session = requests.Session()
        session.headers.update(headers)
        try:
            session.get("https://www.nseindia.com", timeout=8)
        except Exception:
            pass  # best-effort cookie warm-up; proceed regardless

        resp = session.get(NIFTY_CSV_URL, timeout=12)
        status["http_status"] = resp.status_code

        if resp.status_code == 200 and resp.content:
            df = pd.read_csv(pd.io.common.BytesIO(resp.content))
            sym_col = next(
                (c for c in df.columns if "symbol" in c.lower()), None
            )
            if sym_col and len(df) > 50:  # sanity check: a real Nifty 500
                                            # list has ~500 rows; a tiny or
                                            # malformed response (e.g. an
                                            # HTML error page misread as CSV)
                                            # would fail this check instead
                                            # of silently "succeeding" with junk.
                nse_tickers = [f"{s.strip()}.NS" for s in df[sym_col].dropna()]
                tickers.extend(nse_tickers)
                status["live_fetch_succeeded"] = True
                status["live_tickers_added"] = len(nse_tickers)
            else:
                status["error"] = (
                    f"Response didn't look like a valid Nifty 500 CSV "
                    f"(only {len(df)} rows parsed, or no Symbol column found)."
                )
        else:
            status["error"] = f"NSE returned HTTP {resp.status_code} instead of the CSV."

    except Exception as exc:
        status["error"] = f"Request failed: {exc}"

    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    status["total_tickers"] = len(unique)
    return unique, status


# ── yfinance wrapper ─────────────────────────────────────────────────────────

def _safe_yf_download(ticker: str, **kwargs) -> pd.DataFrame:
    """Download OHLCV data; return empty DataFrame on any error."""
    try:
        import yfinance as yf
        df = yf.download(ticker, progress=False, auto_adjust=True, **kwargs)
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()


def _safe_ticker_info(ticker: str) -> dict:
    """Fetch ticker .info dict; return empty dict on any error."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        return t.info or {}
    except Exception:
        return {}


def _safe_ticker_news(ticker: str) -> list[dict]:
    """Fetch ticker news list; return empty list on any error."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        return t.news or []
    except Exception:
        return []


# ── Historical data (cached per ticker per day) ───────────────────────────────

@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_daily_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    return _safe_yf_download(ticker, period=period, interval="1d")


@st.cache_data(ttl=900, show_spinner=False)
def fetch_intraday_15m(ticker: str) -> pd.DataFrame:
    return _safe_yf_download(ticker, period="5d", interval="15m")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_intraday_5m(ticker: str) -> pd.DataFrame:
    return _safe_yf_download(ticker, period="2d", interval="5m")


@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_ticker_info(ticker: str) -> dict:
    return _safe_ticker_info(ticker)


def build_sector_map(
    tickers: list[str],
    progress_callback=None,
) -> dict[str, dict[str, list[str]]]:
    """
    Builds a two-level index: {sector_name: {industry_name: [ticker, ...]}}.

    yfinance's `.info` dict gives both a broad `sector` (e.g. "Industrials")
    and a narrower `industry` (e.g. "Conglomerates", "Aerospace & Defense")
    — this builds both levels in one pass so sector filtering can be
    drilled down further (sector -> industry) without a second round of
    network calls. Each underlying `fetch_ticker_info` call is itself
    cached for an hour, so re-running this after the first pass for the
    same watchlist is fast — only genuinely new tickers trigger a network
    call. Tickers with no sector/industry data from the source are grouped
    under "Unknown / Not Available" rather than silently dropped, so a user
    can still see why a stock might be missing from filtered results.

    `progress_callback(done, total)` is called after each ticker if
    provided, so the caller (Streamlit UI) can show a progress bar without
    this module needing to know anything about Streamlit widgets directly.
    """
    sector_map: dict[str, dict[str, list[str]]] = {}
    total = len(tickers)

    for i, ticker in enumerate(tickers):
        info = fetch_ticker_info(ticker)
        sector = info.get("sector") or "Unknown / Not Available"
        industry = info.get("industry") or "Unknown / Not Available"
        sector_map.setdefault(sector, {}).setdefault(industry, []).append(ticker)
        if progress_callback:
            progress_callback(i + 1, total)

    return sector_map


def flatten_sector_map(sector_map: dict[str, dict[str, list[str]]]) -> dict[str, list[str]]:
    """
    Collapses the two-level {sector: {industry: [tickers]}} structure down
    to {sector: [tickers]} — used wherever only sector-level filtering is
    needed (e.g. the "is my ticker in scope" lookup, or any older code path
    that predates industry-level drill-down).
    """
    return {
        sector: [t for industry_tickers in industries.values() for t in industry_tickers]
        for sector, industries in sector_map.items()
    }


def get_sector_for_ticker(sector_map: dict[str, dict[str, list[str]]], ticker: str) -> tuple[str | None, str | None]:
    """Returns (sector, industry) for a ticker if present in the index, else (None, None)."""
    for sector, industries in sector_map.items():
        for industry, tickers in industries.items():
            if ticker in tickers:
                return sector, industry
    return None, None


@st.cache_data(ttl=1_800, show_spinner=False)
def fetch_news(ticker: str) -> list[dict]:
    return _safe_ticker_news(ticker)


# ── Candlestick pattern detection ─────────────────────────────────────────────

def detect_candle_patterns(df: pd.DataFrame) -> pd.Series:
    """
    Returns a Series of pattern labels for each row in df.
    Patterns:
        'shooting_star'     — upper wick > 2× body; bearish reversal / fakeout
        'hammer'            — lower wick > 2× body; bullish support / reversal
        'strong_bullish'    — body covers > 60% of total range; momentum
        'strong_bearish'    — bearish body covers > 60% of total range
        ''                  — no notable pattern
    """
    if df.empty or not {"Open", "High", "Low", "Close"}.issubset(df.columns):
        return pd.Series([], dtype=str)

    o = df["Open"].astype(float)
    h = df["High"].astype(float)
    lo = df["Low"].astype(float)
    c = df["Close"].astype(float)

    body      = (c - o).abs()
    total_rng = h - lo
    upper_wick = h - np.maximum(o, c)
    lower_wick = np.minimum(o, c) - lo

    # Avoid divide-by-zero
    body_safe = body.replace(0, 1e-9)
    range_safe = total_rng.replace(0, 1e-9)

    is_shooting = upper_wick > 2 * body_safe
    is_hammer   = lower_wick > 2 * body_safe

    patterns = pd.Series("", index=df.index)

    # When both wicks exceed the threshold on a tiny-bodied candle, classify
    # by whichever wick is larger — that side dominates the candle's story.
    both = is_shooting & is_hammer
    shooting_only = is_shooting & ~is_hammer
    hammer_only    = is_hammer & ~is_shooting
    both_shooting_wins = both & (upper_wick >= lower_wick)
    both_hammer_wins    = both & (lower_wick > upper_wick)

    patterns = patterns.where(~(shooting_only | both_shooting_wins), "shooting_star")
    patterns = patterns.where(~(hammer_only | both_hammer_wins), "hammer")

    bullish_mask = (c > o) & (body / range_safe > 0.60) & (patterns == "")
    patterns = patterns.where(~bullish_mask, "strong_bullish")
    bearish_mask = (c < o) & (body / range_safe > 0.60) & (patterns == "")
    patterns = patterns.where(~bearish_mask, "strong_bearish")

    return patterns


# ── ATR calculation ───────────────────────────────────────────────────────────

def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """Average True Range over `period` bars. Returns 0.0 on error. (Delegates to utils.indicators)"""
    return ti.calculate_atr_value(df, period)


# ── SMA helpers ───────────────────────────────────────────────────────────────

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


# ── News sentiment scoring ────────────────────────────────────────────────────

def score_headline_sentiment(headline: str) -> str:
    """Weighted, negation-aware sentiment: 'positive' | 'negative' | 'neutral'."""
    score, _ = score_headline_sentiment_value(headline)
    if score > 0.15:
        return "positive"
    if score < -0.15:
        return "negative"
    return "neutral"


def score_headline_sentiment_value(headline: str) -> tuple[float, dict]:
    """
    Returns (score, debug_info). Score roughly in [-3, 3] (unnormalized magnitude),
    accounting for word weight and simple negation flipping
    (e.g. "not profitable" flips a positive word to negative).
    """
    tokens = re.sub(r"[^\w\s]", " ", headline.lower()).split()
    score = 0.0
    hits = {"positive": [], "negative": []}

    for i, word in enumerate(tokens):
        negate = any(t in NEGATION_WORDS for t in tokens[max(0, i - 3):i])
        if word in SENTIMENT_POSITIVE_WORDS:
            w = SENTIMENT_POSITIVE_WORDS[word]
            score += -w if negate else w
            hits["positive"].append(word if not negate else f"NOT {word}")
        elif word in SENTIMENT_NEGATIVE_WORDS:
            w = SENTIMENT_NEGATIVE_WORDS[word]
            score += w if negate else -w
            hits["negative"].append(word if not negate else f"NOT {word}")

    return score, hits


def aggregate_news_sentiment(news: list[dict]) -> dict:
    """
    Recency-weighted sentiment aggregate across a news list.
    More recent headlines count more heavily, since stale news has already
    been priced in. Returns {
        'score': float  # -1.0 to +1.0
        'label': str    # 'Bullish' | 'Bearish' | 'Mixed' | 'Neutral'
        'breakdown': {'positive': int, 'negative': int, 'neutral': int}
    }
    """
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    if not news:
        return {"score": 0.0, "label": "Neutral", "breakdown": counts}

    now = time.time()
    weighted_sum = 0.0
    weight_total = 0.0

    for item in news:
        title = item.get("title", "") or ""
        raw_score, _ = score_headline_sentiment_value(title)
        label = "positive" if raw_score > 0.15 else ("negative" if raw_score < -0.15 else "neutral")
        counts[label] += 1

        # Recency weight: full weight for <24h old, decaying over 7 days
        pub_time = item.get("providerPublishTime", now)
        age_hours = max(0, (now - pub_time) / 3600)
        recency_weight = max(0.15, 1.0 - (age_hours / (24 * 7)))

        # Clip raw_score to [-1, 1] per headline before weighting
        clipped = max(-1.0, min(1.0, raw_score))
        weighted_sum += clipped * recency_weight
        weight_total += recency_weight

    score = weighted_sum / weight_total if weight_total > 0 else 0.0
    score = round(max(-1.0, min(1.0, score)), 2)

    if score > 0.25:
        label = "Bullish"
    elif score < -0.25:
        label = "Bearish"
    elif abs(score) < 0.08:
        label = "Neutral"
    else:
        label = "Mixed"

    return {"score": score, "label": label, "breakdown": counts}


# ── Trading plan calculations ─────────────────────────────────────────────────

def compute_plan_a(current_price: float, atr_15m: float, adx_value: float = 20.0) -> dict:
    """
    Day-trade (Plan A): tight ATR-based order levels on 15-min data.
    Entry ~0.5 ATR below current; stop 1× ATR below entry.
    Target multiple scales with trend strength (ADX): strong trends (ADX>25)
    get a fuller 2.5× ATR target; choppy/range-bound markets (ADX<20) get a
    conservative 1.5× ATR target, since breakouts are statistically less
    likely to run far in low-ADX conditions.
    """
    if atr_15m <= 0:
        return {}
    target_multiple = 1.5 if adx_value < 20 else (2.0 if adx_value < 25 else 2.5)
    entry  = round(current_price - 0.5 * atr_15m, 2)
    stop   = round(entry - 1.0 * atr_15m, 2)
    target = round(entry + target_multiple * atr_15m, 2)
    rr     = round((target - entry) / max(entry - stop, 1e-9), 2)
    return {
        "current":  round(current_price, 2),
        "entry":    entry,
        "stop":     stop,
        "target":   target,
        "rr_ratio": rr,
        "atr_15m":  round(atr_15m, 2),
        "target_multiple": target_multiple,
    }


def compute_plan_b(
    current_price: float,
    daily_df: pd.DataFrame,
    info: dict,
) -> dict:
    """
    Swing / long-term (Plan B): macro levels from up to 1-year daily data.
    Entry at 1% below the longest available SMA (50 or 200); stop 2% below it;
    raw target scales with trend strength (ADX): 20% above entry in a strong
    uptrend, 10% in a weak/choppy one. Clamps target below 52-week high to
    prevent delusion. Degrades gracefully if < 200 days of history exist
    (uses SMA50 for both reference lines, clearly labelled as lower-confidence).
    """
    if daily_df.empty or len(daily_df) < 60:
        return {}

    close = daily_df["Close"].astype(float)
    has_200 = len(daily_df) >= 200

    sma50  = float(ti.sma(close, 50).iloc[-1])
    sma200 = float(ti.sma(close, 200).iloc[-1]) if has_200 else sma50

    lookback = min(len(close), 252)
    week52_high = float(close.tail(lookback).max())
    week52_low  = float(close.tail(lookback).min())

    adx_series = ti.adx(daily_df)
    adx_v = float(adx_series.iloc[-1]) if not pd.isna(adx_series.iloc[-1]) else 20.0
    target_pct = 0.20 if adx_v > 25 else (0.15 if adx_v > 20 else 0.10)

    entry  = round(sma50 * 0.99, 2)
    stop   = round(sma200 * 0.98, 2)
    raw_target = round(entry * (1 + target_pct), 2)

    # ── Delusion protection ───────────────────────────────────────────────
    delusional = raw_target > week52_high
    clamped_target = round(week52_high * 0.97, 2) if delusional else raw_target

    rr = round((clamped_target - entry) / max(entry - stop, 1e-9), 2)

    return {
        "current":         round(current_price, 2),
        "entry":           entry,
        "stop":            stop,
        "raw_target":      raw_target,
        "target":          clamped_target,
        "delusional":      delusional,
        "week52_high":     round(week52_high, 2),
        "week52_low":      round(week52_low, 2),
        "sma50":           round(sma50, 2),
        "sma200":          round(sma200, 2),
        "rr_ratio":        rr,
        "target_pct":      target_pct,
        "adx":             round(adx_v, 1),
        "low_confidence":  not has_200,
    }


# ── Composite conviction score ────────────────────────────────────────────────

def compute_conviction_score(
    price: float,
    daily_df: pd.DataFrame,
    news_sentiment: dict,
    plan_b: dict,
) -> dict:
    """
    Composite 0–100 conviction score blending trend, momentum, volatility
    positioning, volume confirmation, news sentiment, and risk/reward —
    with explicit penalties for overbought conditions and price/volume
    divergence (the two most common precursors to a failed breakout).

    Components (max points):
        Trend Structure   (20) — SMA20/50/200 alignment + ADX strength
        Momentum (MACD)   (15) — MACD line vs signal, direction & magnitude
        RSI Positioning   (15) — penalises overbought, rewards healthy/oversold zones
        Volume Confirm.   (15) — OBV trend matches price trend (penalises divergence)
        Volatility Pos.   (10) — Bollinger %B: extended bands reduce score
        News Sentiment    (15) — recency-weighted headline sentiment
        Risk/Reward       (10) — Plan B reward-to-risk ratio
    """
    if daily_df.empty or len(daily_df) < 60:
        return {"total": 0, "grade": "N/A", "breakdown": {}, "warnings": ["Insufficient price history (need 60+ daily bars)."]}

    close = daily_df["Close"].astype(float)
    breakdown: dict[str, float] = {}
    warnings_list: list[str] = []

    # ── Trend structure (20 pts): SMA stack + ADX strength ──────────────────
    trend = ti.classify_trend(daily_df)
    trend_pts = 0.0
    if trend["label"] in ("Strong Uptrend", "Uptrend"):
        trend_pts = 12 + min(8, trend["adx"] / 50 * 8)
    elif trend["label"] == "Range-bound":
        trend_pts = 6
    else:  # Downtrend / Strong Downtrend
        trend_pts = max(0, 4 - trend["adx"] / 25 * 4)
        warnings_list.append(f"Trend classified as {trend['label']} — counter-trend long positions carry elevated risk.")
    breakdown["Trend Structure"] = round(trend_pts, 1)

    # ── Momentum / MACD (15 pts) ─────────────────────────────────────────────
    macd_d = ti.macd(close)
    macd_pts = 0.0
    if not macd_d["hist"].empty and not pd.isna(macd_d["hist"].iloc[-1]):
        hist_val = float(macd_d["hist"].iloc[-1])
        hist_norm = hist_val / max(close.iloc[-1] * 0.02, 1e-9)  # normalize by ~2% of price
        macd_pts = max(0, min(15, 7.5 + hist_norm * 7.5))
        if trend["macd_bullish"] and hist_val < 0:
            warnings_list.append("MACD just crossed bullish but histogram still negative — early signal, confirm before sizing up.")
    breakdown["Momentum (MACD)"] = round(macd_pts, 1)

    # ── RSI positioning (15 pts) ─────────────────────────────────────────────
    rsi_v = trend["rsi"]
    if rsi_v >= 80:
        rsi_pts = 2
        warnings_list.append(f"RSI {rsi_v:.0f} is deeply overbought — high risk of mean-reversion pullback.")
    elif rsi_v >= 70:
        rsi_pts = 6
        warnings_list.append(f"RSI {rsi_v:.0f} is overbought — momentum may be stretched short-term.")
    elif 45 <= rsi_v < 70:
        rsi_pts = 15  # healthy bullish zone without being stretched
    elif 30 <= rsi_v < 45:
        rsi_pts = 9
    else:
        rsi_pts = 5  # oversold — could bounce, but trend is weak
    breakdown["RSI Positioning"] = round(rsi_pts, 1)

    # ── Volume confirmation via OBV (15 pts) ─────────────────────────────────
    vol_conf = ti.volume_trend_confirmation(daily_df)
    if vol_conf["divergence"]:
        vol_pts = 2
        warnings_list.append(
            "Price/volume divergence detected — price is moving without OBV confirmation, "
            "a classic fakeout precursor."
        )
    elif vol_conf["confirmed"]:
        vol_pts = 15
    else:
        vol_pts = 8
    breakdown["Volume Confirmation"] = round(vol_pts, 1)

    # ── Volatility positioning via Bollinger %B (10 pts) ─────────────────────
    bb = ti.bollinger_bands(close)
    bb_pts = 5.0
    if not bb["pct_b"].empty and not pd.isna(bb["pct_b"].iloc[-1]):
        pct_b = float(bb["pct_b"].iloc[-1])
        if pct_b > 1.0:
            bb_pts = 3
            warnings_list.append("Price is trading above the upper Bollinger Band — extended, mean-reversion risk.")
        elif pct_b > 0.8:
            bb_pts = 7
        elif 0.2 <= pct_b <= 0.8:
            bb_pts = 10
        elif pct_b < 0:
            bb_pts = 4
            warnings_list.append("Price is trading below the lower Bollinger Band — sharp downside volatility.")
        else:
            bb_pts = 6
    breakdown["Volatility Positioning"] = round(bb_pts, 1)

    # ── News sentiment (15 pts) ───────────────────────────────────────────────
    s = news_sentiment.get("score", 0)
    sent_pts = max(0, min(15, (s + 1) / 2 * 15))
    if news_sentiment.get("label") == "Bearish":
        warnings_list.append("Recent news sentiment is bearish — check headlines before entering.")
    breakdown["News Sentiment"] = round(sent_pts, 1)

    # ── Risk/Reward from Plan B (10 pts) ──────────────────────────────────────
    rr = plan_b.get("rr_ratio", 0) if plan_b else 0
    rr_pts = max(0, min(10, rr / 3 * 10))
    breakdown["Risk/Reward"] = round(rr_pts, 1)
    if plan_b and plan_b.get("delusional"):
        warnings_list.append("Swing target was clamped — raw mathematical target exceeded the 52-week high.")

    total = round(sum(breakdown.values()))
    total = min(100, max(0, total))

    if total >= 75:
        grade = "A"
    elif total >= 58:
        grade = "B"
    elif total >= 40:
        grade = "C"
    else:
        grade = "D"

    return {
        "total": total,
        "grade": grade,
        "breakdown": breakdown,
        "trend": trend,
        "warnings": warnings_list,
    }


# ── Full ticker analysis bundle ───────────────────────────────────────────────

def analyse_ticker(ticker: str) -> dict | None:
    """
    Full analysis bundle for a single ticker.
    Returns None if data is unavailable or insufficient to analyse.
    """
    info     = fetch_ticker_info(ticker)
    daily_df = fetch_daily_history(ticker, period="1y")
    df_15m   = fetch_intraday_15m(ticker)
    news     = fetch_news(ticker)

    if daily_df.empty or len(daily_df) < 30:
        return None

    close_series = daily_df["Close"].astype(float)

    # Some tickers (illiquid micro-caps, recent listings, data gaps from the
    # source) return a NaN for the most recent close even though earlier
    # rows are fine. Using that NaN directly would silently poison every
    # downstream number — Plan A, Plan B, conviction score, day-change % —
    # all the way through to "₹nan" rendered on screen with no error raised
    # anywhere. Instead: drop trailing NaN rows and use the most recent
    # genuinely valid close. If there's no valid close at all in the whole
    # series, the ticker's data is unusable and we bail out cleanly.
    valid_close_series = close_series.dropna()
    if valid_close_series.empty:
        return None

    current_price = float(valid_close_series.iloc[-1])
    is_stale_price = valid_close_series.index[-1] != close_series.index[-1]

    # Use the same NaN-dropped series for everything downstream so a single
    # bad trailing row doesn't propagate into trend/indicator calculations
    # either.
    daily_df = daily_df.loc[:valid_close_series.index[-1]]
    close_series = valid_close_series

    # Volume stats
    avg_vol_10d = 0.0
    if "Volume" in daily_df.columns:
        avg_vol_10d = float(daily_df["Volume"].astype(float).tail(10).mean())

    atr_15m = calculate_atr(df_15m) if not df_15m.empty else 0.0
    atr_daily = calculate_atr(daily_df)

    # ADX feeds into Plan A's target sizing (trend strength gates target distance)
    adx_series = ti.adx(daily_df)
    adx_v = float(adx_series.iloc[-1]) if not adx_series.empty and not pd.isna(adx_series.iloc[-1]) else 20.0

    plan_a = compute_plan_a(
        current_price,
        atr_15m if atr_15m > 0 else atr_daily * 0.3,
        adx_value=adx_v,
    )
    plan_b = compute_plan_b(current_price, daily_df, info)

    patterns = detect_candle_patterns(daily_df)
    recent_patterns = patterns.tail(5).tolist()
    last_pattern = patterns.dropna().iloc[-1] if not patterns.dropna().empty else ""

    news_sentiment = aggregate_news_sentiment(news)
    conviction = compute_conviction_score(current_price, daily_df, news_sentiment, plan_b)
    trend = conviction.get("trend") or ti.classify_trend(daily_df)
    vol_confirmation = ti.volume_trend_confirmation(daily_df)

    day_change_pct = 0.0
    if len(close_series) >= 2:
        day_change_pct = float(
            (close_series.iloc[-1] - close_series.iloc[-2]) / close_series.iloc[-2] * 100
        )

    return {
        "ticker":         ticker,
        "name":           info.get("longName") or info.get("shortName") or ticker,
        "sector":         info.get("sector", "—"),
        "industry":       info.get("industry", "—"),
        "current_price":  current_price,
        "is_stale_price": is_stale_price,
        "day_change_pct": round(day_change_pct, 2),
        "avg_vol_10d":    avg_vol_10d,
        "market_cap":     info.get("marketCap"),
        "pe_ratio":       info.get("trailingPE"),
        "beta":           info.get("beta"),
        "plan_a":         plan_a,
        "plan_b":         plan_b,
        "news":           news[:8],
        "news_sentiment": news_sentiment,
        "conviction":     conviction,
        "trend":          trend,
        "volume_confirmation": vol_confirmation,
        "last_pattern":   last_pattern,
        "recent_patterns": recent_patterns,
        "daily_df":       daily_df,
        "df_15m":         df_15m,
    }

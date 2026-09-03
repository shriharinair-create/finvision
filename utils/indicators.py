"""
Technical indicator library for FinVision.

All functions are pure pandas/numpy — no external TA dependency, so they
work even in restricted-network environments. Each function is defensive:
returns NaN-safe series/values on insufficient data rather than raising.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ── Trend indicators ──────────────────────────────────────────────────────────

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=max(1, period // 2)).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    Returns {'macd': Series, 'signal': Series, 'hist': Series}.
    MACD line crossing above signal = bullish; below = bearish.
    """
    if len(series) < slow + signal:
        empty = pd.Series([np.nan] * len(series), index=series.index)
        return {"macd": empty, "signal": empty, "hist": empty}

    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "hist": hist}


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average Directional Index — trend strength (0-100), using Wilder's
    original smoothing method.
    >25 = trending market (directional moves are reliable)
    <20 = ranging/choppy market (breakouts more likely to fail)
    """
    if len(df) < period * 2:
        return pd.Series([np.nan] * len(df), index=df.index)

    high, low, close = df["High"].astype(float), df["Low"].astype(float), df["Close"].astype(float)
    prev_close = close.shift(1)
    prev_high = high.shift(1)
    prev_low = low.shift(1)

    up_move = high - prev_high
    down_move = prev_low - low

    plus_dm  = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    # Wilder smoothing: first value is a simple sum over `period`, then
    # recursively smoothed — using ewm(alpha=1/period) approximates this
    # well once warmed up, but the early values are unreliable, so we only
    # trust values after the first `period * 2` bars (guarded by caller).
    atr_s = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    plus_dm_smooth  = pd.Series(plus_dm, index=df.index).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    minus_dm_smooth = pd.Series(minus_dm, index=df.index).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    plus_di  = 100 * plus_dm_smooth / atr_s.replace(0, np.nan)
    minus_di = 100 * minus_dm_smooth / atr_s.replace(0, np.nan)

    di_sum = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx_s = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return adx_s


# ── Momentum indicators ───────────────────────────────────────────────────────

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (0-100).
    >70 = overbought (risk of pullback); <30 = oversold (risk of bounce).
    """
    if len(series) < period + 1:
        return pd.Series([np.nan] * len(series), index=series.index)

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_s = 100 - (100 / (1 + rs))
    rsi_s = rsi_s.fillna(50)  # neutral when avg_loss is 0 (pure uptrend)
    return rsi_s


def stochastic_oscillator(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> dict:
    """Returns {'k': Series, 'd': Series}. %K crossing above %D = bullish signal."""
    if len(df) < k_period:
        empty = pd.Series([np.nan] * len(df), index=df.index)
        return {"k": empty, "d": empty}

    low_min = df["Low"].astype(float).rolling(k_period).min()
    high_max = df["High"].astype(float).rolling(k_period).max()
    close = df["Close"].astype(float)

    k = 100 * (close - low_min) / (high_max - low_min).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return {"k": k, "d": d}


# ── Volatility indicators ─────────────────────────────────────────────────────

def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> dict:
    """Returns {'upper': Series, 'mid': Series, 'lower': Series, 'pct_b': Series}."""
    if len(series) < period:
        empty = pd.Series([np.nan] * len(series), index=series.index)
        return {"upper": empty, "mid": empty, "lower": empty, "pct_b": empty}

    mid = sma(series, period)
    std = series.rolling(period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    pct_b = (series - lower) / (upper - lower).replace(0, np.nan)
    return {"upper": upper, "mid": mid, "lower": lower, "pct_b": pct_b}


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range — absolute volatility measure."""
    if len(df) < period + 1:
        return pd.Series([np.nan] * len(df), index=df.index)

    h, l, c = df["High"].astype(float), df["Low"].astype(float), df["Close"].astype(float)
    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def calculate_atr_value(df: pd.DataFrame, period: int = 14) -> float:
    """Scalar ATR (last value), 0.0 on insufficient data."""
    series = atr(df, period)
    if series.empty or pd.isna(series.iloc[-1]):
        return 0.0
    return float(series.iloc[-1])


# ── Volume indicators ─────────────────────────────────────────────────────────

def obv(df: pd.DataFrame) -> pd.Series:
    """
    On-Balance Volume — cumulative volume flow.
    Rising OBV alongside rising price confirms a genuine trend;
    divergence (price up, OBV flat/down) warns of a weak rally.
    """
    if "Volume" not in df.columns or len(df) < 2:
        return pd.Series([np.nan] * len(df), index=df.index)

    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def volume_trend_confirmation(df: pd.DataFrame, lookback: int = 20) -> dict:
    """
    Checks whether recent price momentum is backed by volume (genuine)
    or unconfirmed by volume (suspect — common precursor to a fakeout/fade).

    Returns {'confirmed': bool, 'obv_slope': float, 'price_slope': float, 'divergence': bool}
    """
    if len(df) < lookback + 1 or "Volume" not in df.columns:
        return {"confirmed": False, "obv_slope": 0.0, "price_slope": 0.0, "divergence": False}

    close = df["Close"].astype(float).tail(lookback)
    obv_s = obv(df).tail(lookback)

    # Normalized slopes via simple linear regression
    x = np.arange(len(close))
    price_slope = float(np.polyfit(x, close.values, 1)[0]) / max(close.mean(), 1e-9)
    obv_slope = float(np.polyfit(x, obv_s.values, 1)[0]) if obv_s.notna().all() else 0.0
    obv_slope_norm = obv_slope / max(abs(obv_s).mean(), 1.0)

    # Divergence: price rising but OBV falling (or vice versa)
    divergence = (price_slope > 0 and obv_slope_norm < 0) or (price_slope < 0 and obv_slope_norm > 0)
    confirmed = (price_slope > 0 and obv_slope_norm > 0) or (price_slope < 0 and obv_slope_norm < 0)

    return {
        "confirmed": confirmed,
        "obv_slope": round(obv_slope_norm, 4),
        "price_slope": round(price_slope, 4),
        "divergence": divergence,
    }


# ── Composite trend classification ────────────────────────────────────────────

def classify_trend(df: pd.DataFrame) -> dict:
    """
    Synthesizes SMA alignment, ADX strength, MACD direction, and RSI zone
    into a single human-readable trend classification with confidence.

    Returns {
        'label': str,            # 'Strong Uptrend' | 'Uptrend' | 'Range-bound' |
                                  # 'Downtrend' | 'Strong Downtrend'
        'confidence': float,     # 0-100
        'adx': float,
        'rsi': float,
        'macd_bullish': bool,
        'details': list[str],
    }
    """
    if len(df) < 60:
        return {
            "label": "Insufficient Data", "confidence": 0, "adx": 0, "rsi": 50,
            "macd_bullish": False, "details": ["Need 60+ daily bars for trend classification."],
        }

    close = df["Close"].astype(float)
    price = float(close.iloc[-1])

    sma20_v  = float(sma(close, 20).iloc[-1])
    sma50_v  = float(sma(close, 50).iloc[-1]) if len(close) >= 50 else sma20_v
    sma200_v = float(sma(close, 200).iloc[-1]) if len(close) >= 200 else sma50_v

    adx_s = adx(df)
    adx_v = float(adx_s.iloc[-1]) if not pd.isna(adx_s.iloc[-1]) else 0.0

    rsi_s = rsi(close)
    rsi_v = float(rsi_s.iloc[-1]) if not pd.isna(rsi_s.iloc[-1]) else 50.0

    macd_d = macd(close)
    macd_bullish = False
    if not pd.isna(macd_d["macd"].iloc[-1]) and not pd.isna(macd_d["signal"].iloc[-1]):
        macd_bullish = macd_d["macd"].iloc[-1] > macd_d["signal"].iloc[-1]

    details = []
    bull_points = 0
    bear_points = 0

    # SMA alignment (golden/death cross structure)
    if price > sma20_v > sma50_v > sma200_v:
        bull_points += 2
        details.append("Price > SMA20 > SMA50 > SMA200 — fully bullish stack")
    elif price > sma50_v and price > sma200_v:
        bull_points += 1
        details.append("Price above both SMA50 and SMA200")
    elif price < sma20_v < sma50_v < sma200_v:
        bear_points += 2
        details.append("Price < SMA20 < SMA50 < SMA200 — fully bearish stack")
    elif price < sma50_v and price < sma200_v:
        bear_points += 1
        details.append("Price below both SMA50 and SMA200")
    else:
        details.append("Mixed SMA alignment — no clear structural trend")

    # ADX trend strength gate
    trending = adx_v > 25
    if trending:
        details.append(f"ADX {adx_v:.1f} confirms a trending (non-choppy) market")
    else:
        details.append(f"ADX {adx_v:.1f} suggests range-bound/choppy conditions — signals less reliable")

    # MACD confirmation
    if macd_bullish:
        bull_points += 1
        details.append("MACD line above signal line — bullish momentum")
    else:
        bear_points += 1
        details.append("MACD line below signal line — bearish momentum")

    # RSI zone
    if rsi_v > 70:
        details.append(f"RSI {rsi_v:.0f} is overbought — pullback risk elevated")
        bear_points += 0.5
    elif rsi_v < 30:
        details.append(f"RSI {rsi_v:.0f} is oversold — bounce potential")
        bull_points += 0.5
    else:
        details.append(f"RSI {rsi_v:.0f} is in neutral territory")

    net = bull_points - bear_points
    if net >= 2.5 and trending:
        label, confidence = "Strong Uptrend", min(95, 60 + adx_v)
    elif net >= 1:
        label, confidence = "Uptrend", min(80, 45 + adx_v * 0.8)
    elif net <= -2.5 and trending:
        label, confidence = "Strong Downtrend", min(95, 60 + adx_v)
    elif net <= -1:
        label, confidence = "Downtrend", min(80, 45 + adx_v * 0.8)
    else:
        label, confidence = "Range-bound", max(20, 50 - adx_v)

    return {
        "label": label,
        "confidence": round(confidence, 1),
        "adx": round(adx_v, 1),
        "rsi": round(rsi_v, 1),
        "macd_bullish": macd_bullish,
        "details": details,
    }


# ── Intraday-specific: VWAP and Opening Range ─────────────────────────────────

def vwap(df: pd.DataFrame) -> pd.Series:
    """
    Volume-Weighted Average Price, reset at the start of the data (assumes
    `df` already covers a single session — call per-day if passing
    multi-day intraday data). VWAP is generally a more meaningful intraday
    reference line than a simple time-based EMA, since it weights by where
    volume actually traded rather than just elapsed time.
    """
    if df.empty or "Volume" not in df.columns:
        return pd.Series([float("nan")] * len(df), index=df.index)

    typical_price = (df["High"].astype(float) + df["Low"].astype(float) + df["Close"].astype(float)) / 3
    volume = df["Volume"].astype(float)
    cum_vol = volume.cumsum()
    cum_vol_price = (typical_price * volume).cumsum()
    return cum_vol_price / cum_vol.replace(0, float("nan"))


def opening_range(df: pd.DataFrame, minutes: int = 15) -> dict:
    """
    Computes the opening range high/low from the first `minutes` of a
    single session's intraday data — the classic ORB (Opening Range
    Breakout) reference levels. The first 15 minutes of a session are
    often dominated by overnight-gap noise and algorithmic order-flow
    rather than genuine price discovery, so many intraday traders avoid
    taking fresh breakout signals until this window has closed.

    Returns {'available': bool, 'high': float, 'low': float,
             'range_closed': bool, 'minutes_elapsed': int}
    """
    if df.empty or len(df) < 2:
        return {"available": False, "high": None, "low": None, "range_closed": False, "minutes_elapsed": 0}

    session_start = df.index[0]
    elapsed = (df.index - session_start).total_seconds() / 60
    in_range_mask = elapsed <= minutes

    if not in_range_mask.any():
        return {"available": False, "high": None, "low": None, "range_closed": False, "minutes_elapsed": 0}

    range_df = df[in_range_mask]
    minutes_elapsed = float(elapsed[in_range_mask].max())

    return {
        "available": True,
        "high": float(range_df["High"].astype(float).max()),
        "low": float(range_df["Low"].astype(float).min()),
        "range_closed": minutes_elapsed >= minutes,
        "minutes_elapsed": round(minutes_elapsed, 1),
    }



def detect_wyckoff_accumulation_structure(df: pd.DataFrame) -> dict[str, Any]:
    """
    Detects Wyckoff Institutional Stealth Accumulation & Float Absorption.
    Identifies tight sideways price consolidation paired with anomalous volume spikes.
    """
    if df.empty or len(df) < 30:
        return {"is_absorbing": False, "absorption_score": 0.0, "phase": "INSUFFICIENT_DATA"}

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    vol = df["Volume"].astype(float)

    # 1. Price Range Compression (last 15 bars)
    high15 = high.tail(15).max()
    low15 = low.tail(15).min()
    current_p = close.iloc[-1]
    range_pct = ((high15 - low15) / (low15 + 1e-9)) * 100.0

    # 2. Volume Expansion Ratio (15-day volume vs 50-day average)
    vol_sma15 = vol.tail(15).mean()
    vol_sma50 = vol.tail(50).mean() if len(vol) >= 50 else vol.mean()
    vol_expansion = vol_sma15 / (vol_sma50 + 1e-9)

    # 3. Absorption Score
    # Ideal: tight range (< 6%) with heavy volume (> 1.25x)
    is_tight = range_pct <= 7.0
    is_high_vol = vol_expansion >= 1.20
    
    score = 0.0
    if is_tight:
        score += max(0.0, 50.0 * (1.0 - range_pct / 7.0))
    if is_high_vol:
        score += min(50.0, 25.0 * (vol_expansion - 1.0))

    score = float(np.clip(score, 0.0, 100.0))

    if score >= 65.0:
        phase = "WYCKOFF PHASE B: STEALTH FLOAT ABSORPTION"
        desc = f"Smart money accumulating float. Price range compressed to {range_pct:.1f}% while volume expanded {vol_expansion:.2f}x."
    elif score >= 40.0:
        phase = "WYCKOFF PHASE A: PRELIMINARY ACCUMULATION"
        desc = f"Early absorption signals. 15-day range is {range_pct:.1f}% with volume ratio {vol_expansion:.2f}x."
    else:
        phase = "MARKUP / MARKDOWN / UNCORRELATED"
        desc = f"Standard market drift. 15-day range is {range_pct:.1f}%."

    return {
        "is_absorbing": score >= 50.0,
        "absorption_score": round(score, 1),
        "phase": phase,
        "range_15d_pct": round(range_pct, 2),
        "volume_expansion_ratio": round(vol_expansion, 2),
        "breakout_trigger": round(high15 * 1.005, 2),
        "absorption_floor": round(low15 * 0.995, 2),
        "details": desc
    }


def detect_liquidity_sweep_spring(df: pd.DataFrame) -> dict[str, Any]:
    """
    Detects Liquidity Sweeps / Wyckoff Springs (Operator Stop-Hunt Traps).
    Occurs when price dips below 20-day support to trigger retail stop losses,
    then aggressively reclaims the level within the same or next session.
    """
    if df.empty or len(df) < 25:
        return {"is_spring": False, "trap_type": "NONE"}

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)

    # 20-day prior support (excluding current bar)
    prior_low20 = low.iloc[-21:-1].min()
    current_low = low.iloc[-1]
    current_close = close.iloc[-1]
    current_open = df["Open"].astype(float).iloc[-1]

    # Spring Condition: Low pierced below prior 20-day low, but Close finished ABOVE prior low
    pierced_support = current_low < prior_low20
    reclaimed_support = current_close > prior_low20
    strong_close = current_close >= (current_low + 0.60 * (high.iloc[-1] - current_low))

    is_spring = bool(pierced_support and reclaimed_support and strong_close)
    
    # Bear Trap strength calculation
    lower_wick_ratio = (min(current_open, current_close) - current_low) / (high.iloc[-1] - current_low + 1e-9)

    if is_spring:
        trap_type = "BULLISH SPRING (OPERATOR STOP HUNT RECLAIM)"
        desc = f"Price pierced 20-day low ({prior_low20:.2f}) down to {current_low:.2f} to hunt stops, then sharply closed above support at {current_close:.2f}."
    elif current_low < prior_low20 and not reclaimed_support:
        trap_type = "BREAKDOWN IN PROGRESS"
        desc = f"Price broke 20-day support ({prior_low20:.2f}) and closed below at {current_close:.2f}."
    else:
        trap_type = "NONE"
        desc = "No liquidity sweep detected."

    return {
        "is_spring": is_spring,
        "trap_type": trap_type,
        "support_level": round(prior_low20, 2),
        "sweep_low": round(current_low, 2),
        "lower_wick_ratio": round(lower_wick_ratio, 2),
        "invalidation_level": round(current_low * 0.995, 2),
        "description": desc
    }


def compute_max_pain_and_oi_walls(ticker: str, current_price: float) -> dict[str, Any]:
    """
    Computes Options Max Pain Strike and Call/Put Open Interest Walls for Indian F&O Stocks.
    On expiry sessions, price is gravitationally pulled toward the Max Pain strike.
    """
    import yfinance as yf
    try:
        t = yf.Ticker(ticker)
        expirations = t.options
        if not expirations:
            # Fallback estimation based on standard round strikes
            strike_step = 50.0 if current_price > 1000 else 10.0 if current_price > 200 else 5.0
            approx_pain = round(current_price / strike_step) * strike_step
            return {
                "max_pain": approx_pain,
                "call_oi_wall": approx_pain + 2 * strike_step,
                "put_oi_wall": approx_pain - 2 * strike_step,
                "expiry_gravity_pull_pct": round(((approx_pain - current_price) / current_price) * 100.0, 2),
                "is_options_active": False
            }

        nearest_exp = expirations[0]
        opt_chain = t.option_chain(nearest_exp)
        calls = opt_chain.calls
        puts = opt_chain.puts

        if calls.empty or puts.empty:
            return {}

        # Max Call OI (Call Wall / Resistance)
        call_wall = float(calls.loc[calls["openInterest"].idxmax()]["strike"]) if "openInterest" in calls else current_price * 1.03
        # Max Put OI (Put Wall / Support)
        put_wall = float(puts.loc[puts["openInterest"].idxmax()]["strike"]) if "openInterest" in puts else current_price * 0.97

        # Calculate Max Pain
        all_strikes = sorted(list(set(calls["strike"].tolist() + puts["strike"].tolist())))
        pain_values = []
        for s in all_strikes:
            # Total call loss: sum(max(0, s - call_strike) * call_oi)
            call_loss = calls.apply(lambda r: max(0, s - r["strike"]) * r.get("openInterest", 0), axis=1).sum()
            # Total put loss: sum(max(0, put_strike - s) * put_oi)
            put_loss = puts.apply(lambda r: max(0, r["strike"] - s) * r.get("openInterest", 0), axis=1).sum()
            pain_values.append(call_loss + put_loss)

        min_pain_idx = int(np.argmin(pain_values))
        max_pain_strike = float(all_strikes[min_pain_idx])
        gravity_pull = round(((max_pain_strike - current_price) / current_price) * 100.0, 2)

        total_call_oi = float(calls["openInterest"].sum()) if "openInterest" in calls else 1.0
        total_put_oi = float(puts["openInterest"].sum()) if "openInterest" in puts else 1.0
        pcr = round(total_put_oi / max(1.0, total_call_oi), 2)
        if pcr >= 1.25:
            pcr_sentiment = "BULLISH_SUPPORT"
        elif pcr <= 0.75:
            pcr_sentiment = "BEARISH_RESISTANCE"
        else:
            pcr_sentiment = "BALANCED_NEUTRAL"

        return {
            "max_pain": max_pain_strike,
            "call_oi_wall": call_wall,
            "put_oi_wall": put_wall,
            "pcr": pcr,
            "pcr_sentiment": pcr_sentiment,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "expiry_date": nearest_exp,
            "expiry_gravity_pull_pct": gravity_pull,
            "is_options_active": True
        }
    except Exception:
        strike_step = 50.0 if current_price > 1000 else 10.0 if current_price > 200 else 5.0
        approx_pain = round(current_price / strike_step) * strike_step
        return {
            "max_pain": approx_pain,
            "call_oi_wall": approx_pain + 2 * strike_step,
            "put_oi_wall": approx_pain - 2 * strike_step,
            "pcr": 1.0,
            "pcr_sentiment": "BALANCED_NEUTRAL",
            "expiry_gravity_pull_pct": round(((approx_pain - current_price) / current_price) * 100.0, 2),
            "is_options_active": False
        }


def check_exit_liquidity_trap(
    df: pd.DataFrame, 
    news_sentiment_score: float = 0.0, 
    catalyst_score: float = 0.0, 
    rsi: float = 50.0
) -> dict[str, Any]:
    """
    Detects potential 'Sell-the-News' Exit Liquidity Distribution Traps.
    Flags when smart money/operators use retail euphoria around breaking news/earnings
    to distribute inventory after a steep pre-catalyst run-up.
    """
    if df.empty or len(df) < 10:
        return {"is_trap": False, "risk_level": "LOW", "warning_message": ""}

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    vol = df["Volume"].astype(float) if "Volume" in df.columns else pd.Series(1.0, index=close.index)

    last_p = float(close.iloc[-1])
    ret_5d = float((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] * 100.0) if len(close) >= 6 else 0.0
    ret_10d = float((close.iloc[-1] - close.iloc[-11]) / close.iloc[-11] * 100.0) if len(close) >= 11 else ret_5d

    # Upper wick rejection detection on latest session
    bar_range = float(high.iloc[-1] - low.iloc[-1] + 1e-9)
    upper_wick_ratio = float((high.iloc[-1] - max(close.iloc[-1], df["Open"].iloc[-1])) / bar_range)
    
    # Volume spike vs 20D SMA
    vol_sma20 = float(vol.tail(20).mean()) if len(vol) >= 5 else 1.0
    vol_ratio = float(vol.iloc[-1] / max(1.0, vol_sma20))

    euphoria_catalyst = (news_sentiment_score >= 0.25 or catalyst_score >= 0.25)
    steep_runup = (ret_5d >= 10.0 or ret_10d >= 18.0)
    overbought_rsi = (rsi >= 70.0)
    distribution_wick = (upper_wick_ratio >= 0.35 and vol_ratio >= 1.25)

    # Multi-session upper-wick rejection analysis across last 10 sessions
    recent_bars = df.tail(min(10, len(df)))
    recent_upper_wicks = []
    for _, r in recent_bars.iterrows():
        b_range = float(r["High"] - r["Low"] + 1e-9)
        u_wick = float(r["High"] - max(r["Close"], r["Open"])) / b_range
        recent_upper_wicks.append(u_wick)
    avg_upper_wick_ratio = float(np.mean(recent_upper_wicks)) if recent_upper_wicks else 0.0
    high_wick_days = sum(1 for w in recent_upper_wicks if w >= 0.38)

    range_15d_high = float(high.tail(min(15, len(high))).max())
    dist_from_range_high_pct = float(((range_15d_high - last_p) / range_15d_high) * 100.0)

    # 1. Momentum Blow-Off Exit Trap
    is_momentum_trap = steep_runup and euphoria_catalyst and (overbought_rsi or distribution_wick)

    # 2. Resistance Distribution Trap (e.g. repeated upper wick rejections near ceiling + headline excitement)
    is_resistance_trap = (
        euphoria_catalyst and
        dist_from_range_high_pct <= 4.5 and
        (high_wick_days >= 4 or avg_upper_wick_ratio >= 0.38)
    )

    is_trap = False
    risk_level = "LOW"
    warning = ""

    if is_momentum_trap:
        is_trap = True
        risk_level = "HIGH"
        warning = (
            f"⚠️ High-risk 'Sell-the-News' Distribution Zone. Stock gained {ret_5d:+.1f}% over 5 sessions "
            f"into headline euphoria (RSI: {rsi:.1f}). High probability of institutional profit taking into retail buying."
        )
    elif is_resistance_trap:
        is_trap = True
        risk_level = "HIGH"
        warning = (
            f"⚠️ High-risk 'Sell-the-News' Resistance Trap. Stock has faced severe upper-wick rejections on {high_wick_days} of the last {len(recent_upper_wicks)} sessions "
            f"near range ceiling (₹{range_15d_high:,.2f}). Smart money is utilizing news excitement to distribute overhead inventory."
        )
    elif steep_runup and overbought_rsi:
        is_trap = False
        risk_level = "MODERATE"
        warning = f"Momentum extended (+{ret_5d:.1f}% in 5D, RSI: {rsi:.1f}). Watch for mean reversion pullbacks."

    return {
        "is_trap": is_trap,
        "risk_level": risk_level,
        "trap_type": "MOMENTUM_BLOWOFF" if is_momentum_trap else "RESISTANCE_DISTRIBUTION" if is_resistance_trap else "NONE",
        "recent_runup_5d_pct": round(ret_5d, 2),
        "recent_runup_10d_pct": round(ret_10d, 2),
        "upper_wick_ratio": round(upper_wick_ratio, 2),
        "avg_upper_wick_10d": round(avg_upper_wick_ratio, 2),
        "high_wick_days_count": high_wick_days,
        "volume_spike_ratio": round(vol_ratio, 2),
        "warning_message": warning
    }


def detect_delivery_accumulation_anomaly(df: pd.DataFrame) -> dict[str, Any]:
    """
    Detects Stealth Institutional Accumulation & Volatility Compression.
    Occurs when trading volume expands significantly while price volatility compresses into a tight channel,
    indicating quiet institutional float absorption before a markup expansion.
    """
    if df.empty or len(df) < 20:
        return {"is_accumulation": False, "score": 50, "status": "NORMAL"}

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    vol = df["Volume"].astype(float) if "Volume" in df.columns else pd.Series(1.0, index=close.index)

    # Volatility compression ratio (5D true range vs 20D average true range)
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr20 = float(tr.tail(20).mean())
    atr5 = float(tr.tail(5).mean())
    compression_ratio = round(atr5 / max(1e-9, atr20), 2)

    # Volume expansion ratio
    vol20 = float(vol.tail(20).mean())
    vol5 = float(vol.tail(5).mean())
    vol_ratio = round(vol5 / max(1.0, vol20), 2)

    # Accumulation occurs if volume expands (>1.15) while volatility contracts (<0.85)
    is_accumulation = bool(vol_ratio >= 1.15 and compression_ratio <= 0.85)
    
    score = 50.0
    if is_accumulation:
        score = min(95.0, 65.0 + (vol_ratio - 1.0) * 20.0 + (1.0 - compression_ratio) * 15.0)
        status = "STEALTH INSTITUTIONAL ACCUMULATION (FLOAT ABSORPTION)"
    elif vol_ratio >= 1.5 and compression_ratio >= 1.3:
        score = 30.0
        status = "HIGH VOLATILITY EXPANSION / CHURN"
    else:
        score = 50.0
        status = "BALANCED ORDER FLOW"

    return {
        "is_accumulation": is_accumulation,
        "score": round(score, 1),
        "vol_expansion_ratio": vol_ratio,
        "volatility_compression_ratio": compression_ratio,
        "status": status
    }


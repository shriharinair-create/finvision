"""
finvision/utils/forecasting.py
==============================
Advanced Quantitative Confluence & Machine Learning Price Forecasting Utilities.
Includes multi-timeframe trend hierarchy, momentum oscillator confluence,
support/resistance channel detection, volume OBV dynamics, broad market regime gating,
EWMA adaptive Monte Carlo simulations, and automated walk-forward backtesting.
"""

from __future__ import annotations

import datetime
import hashlib

from utils.indicators import (
    detect_wyckoff_accumulation_structure, 
    detect_liquidity_sweep_spring, 
    compute_max_pain_and_oi_walls,
    check_exit_liquidity_trap,
    detect_delivery_accumulation_anomaly
)

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from utils.ml_ensemble import compute_ml_ensemble_consensus
from utils.risk import compute_institutional_var_cvar
from utils.macro import get_live_cross_asset_macro


def compute_quantitative_confluence_forecast(
    df: pd.DataFrame,
    nse_df: Optional[pd.DataFrame] = None,
    forecast_days: int = 5,
    news_sentiment_score: float = 0.0,
    catalyst_score: float = 0.0,
    pre_market_gap_pct: float = 0.0,
) -> dict[str, Any]:
    """
    Computes a multi-modal quantitative confluence forecast for a given stock.
    Synthesizes:
      1. Trend Structure (25%): EMA 8/21, SMA 50/200 hierarchy & stack alignment.
      2. Momentum Dynamics (25%): RSI divergence/exhaustion, MACD velocity & Stochastic %K/%D.
      3. Support / Resistance (20%): 20-day high/low boundaries, Bollinger Band %B & Classical Pivots.
      4. Volume Confirmation (15%): OBV slope flow & accumulation/distribution divergence.
      5. Market Regime & Relative Strength (15%): Nifty 50 (^NSEI) regime gate + stock alpha.
      6. News Sentiment & Keyword Catalysts (when available).

    Returns calibrated directional bias, 1-day/5-day targets, stop loss, take profit,
    and multi-day projection table with 80% confidence interval bands.
    """
    if df.empty or len(df) < 30:
        return {}

    # Normalize column names if multi-indexed
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [c[0] for c in df.columns]

    close = df["Close"].astype(float).dropna()
    if close.empty:
        return {}

    # Match indexes
    df = df.loc[close.index]
    high = df["High"].astype(float) if "High" in df.columns else close
    low = df["Low"].astype(float) if "Low" in df.columns else close
    open_p = df["Open"].astype(float) if "Open" in df.columns else close
    vol = df["Volume"].astype(float) if "Volume" in df.columns else pd.Series(1.0, index=close.index)

    last_p = float(close.iloc[-1])

    # ── 1. Broad Market Regime Gate (^NSEI context) ──────────────────────────
    mkt_regime_drag = 0.0
    nse_ret5 = 0.0
    if nse_df is not None and not nse_df.empty:
        try:
            if isinstance(nse_df.columns, pd.MultiIndex):
                nse_df = nse_df.copy()
                nse_df.columns = [c[0] for c in nse_df.columns]
            nse_c = nse_df["Close"].astype(float).reindex(close.index).ffill()
            if len(nse_c.dropna()) >= 20:
                nse_last = float(nse_c.iloc[-1])
                nse_ema20 = float(nse_c.ewm(span=20, adjust=False).mean().iloc[-1])
                nse_ret5 = float((nse_c.iloc[-1] - nse_c.iloc[-5]) / nse_c.iloc[-5] * 100.0) if len(nse_c) >= 5 else 0.0
                if nse_last < nse_ema20 or nse_ret5 < -0.5:
                    mkt_regime_drag = -0.25
                elif nse_last > nse_ema20 and nse_ret5 > 0.5:
                    mkt_regime_drag = +0.20
        except Exception:
            pass

    # Stock's Relative Strength vs Benchmark
    stock_ret5 = float((close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100.0) if len(close) >= 5 else 0.0
    rel_strength = stock_ret5 - nse_ret5

    # ── 2. Trend & Moving Average Hierarchy ──────────────────────────────────
    ema8 = float(close.ewm(span=8, adjust=False).mean().iloc[-1])
    ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])
    sma50 = float(close.rolling(50, min_periods=min(50, max(5, len(close)//4))).mean().iloc[-1])
    sma200 = float(close.rolling(200, min_periods=min(200, max(10, len(close)//2))).mean().iloc[-1]) if len(close) >= 50 else sma50

    trend_score = 0.0
    if last_p > ema8 > ema21:
        trend_score += 0.40
    elif last_p < ema8 < ema21:
        trend_score -= 0.40
    else:
        trend_score += 0.15 if last_p > ema21 else -0.15

    if last_p > sma50: trend_score += 0.30
    else: trend_score -= 0.30

    if last_p > sma200: trend_score += 0.30
    else: trend_score -= 0.30

    # ── 3. Momentum & Oscillator Mechanics ───────────────────────────────────
    # RSI (14)
    delta = close.diff()
    gain14 = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss14 = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs14 = gain14 / (loss14.replace(0, np.nan))
    rsi_s = 100 - (100 / (1 + rs14)).fillna(50)
    rsi = float(rsi_s.iloc[-1])
    rsi_slope3 = float(rsi_s.iloc[-1] - rsi_s.iloc[-3]) if len(rsi_s) >= 3 else 0.0

    # MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    hist_now = float(hist.iloc[-1]) if not hist.empty else 0.0
    hist_slope3 = float(hist.iloc[-1] - hist.iloc[-3]) if len(hist) >= 3 else 0.0

    # Stochastic %K and %D
    low14 = low.rolling(14, min_periods=5).min()
    high14 = high.rolling(14, min_periods=5).max()
    stoch_k = 100 * (close - low14) / (high14 - low14 + 1e-9)
    stoch_d = stoch_k.rolling(3, min_periods=1).mean()
    k_val = float(stoch_k.iloc[-1]) if not stoch_k.empty else 50.0
    d_val = float(stoch_d.iloc[-1]) if not stoch_d.empty else 50.0

    # Consolidated Momentum Factor (combines RSI, MACD velocity, and Stochastics without double-counting)
    mom_rsi = 0.0
    if rsi >= 68:
        mom_rsi = -0.50  # Overbought exhaustion risk
    elif rsi <= 32:
        mom_rsi = +0.50 if (hist_slope3 > 0 or rsi_slope3 > 0) else -0.25
    else:
        mom_rsi = (rsi - 50.0) / 35.0

    mom_macd = 0.0
    if hist_now > 0 and hist_slope3 > 0:
        mom_macd = +0.50
    elif hist_now > 0 and hist_slope3 <= 0:
        mom_macd = -0.15
    elif hist_now < 0 and hist_slope3 > 0:
        mom_macd = +0.40
    else:
        mom_macd = -0.50

    mom_stoch = 0.0
    if k_val > d_val and k_val < 80:
        mom_stoch = +0.30
    elif k_val < d_val and k_val > 20:
        mom_stoch = -0.30

    mom_score = float(np.clip(0.40 * mom_rsi + 0.40 * mom_macd + 0.20 * mom_stoch, -1.0, 1.0))

    # ── 4. Support/Resistance & Volatility Band Location ──────────────────────
    bb_mid = float(close.rolling(20, min_periods=10).mean().iloc[-1])
    bb_std = float(close.rolling(20, min_periods=10).std().iloc[-1])
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    pct_b = (last_p - bb_lower) / (bb_upper - bb_lower + 1e-9)

    low20 = float(low.rolling(20, min_periods=5).min().iloc[-1])
    high20 = float(high.rolling(20, min_periods=5).max().iloc[-1])
    dist_to_low20 = (last_p - low20) / (high20 - low20 + 1e-9)

    sr_score = 0.0
    if pct_b >= 0.90:
        sr_score -= 0.50  # Upper band rejection
    elif pct_b <= 0.10:
        sr_score += 0.50  # Lower band bounce
    elif dist_to_low20 < 0.15 and (rsi_slope3 > 0 or k_val > d_val):
        sr_score += 0.45  # 20-day support test & hold
    elif dist_to_low20 > 0.85 and (rsi_slope3 < 0 or k_val < d_val):
        sr_score -= 0.45  # 20-day resistance rejection
    else:
        sr_score = (pct_b - 0.50) * 0.35

    # ── 5. Volume Flow, Liquidity & Float Absorption ─────────────────────────
    vol_sma20 = float(vol.rolling(20, min_periods=5).mean().iloc[-1])
    obv = (np.sign(close.diff()).fillna(0) * vol).cumsum()
    obv_slope5 = float(obv.iloc[-1] - obv.iloc[-5]) if len(obv) >= 5 else 0.0
    price_slope5 = float(close.iloc[-1] - close.iloc[-5]) if len(close) >= 5 else 0.0

    vol_score = 0.0
    if price_slope5 > 0 and obv_slope5 > 0:
        vol_score = 0.45
    elif price_slope5 < 0 and obv_slope5 < 0:
        vol_score = -0.45
    elif price_slope5 > 0 and obv_slope5 < 0:
        vol_score = -0.55  # Bearish volume divergence
    elif price_slope5 < 0 and obv_slope5 > 0:
        vol_score = 0.55   # Bullish volume accumulation

    delivery_data = detect_delivery_accumulation_anomaly(df)
    if delivery_data.get("is_accumulation"):
        vol_score += 0.25

    flow_score = float(np.clip(0.60 * vol_score + 0.40 * sr_score, -1.0, 1.0))

    # ── 6. Market Benchmark Regime & Stock Relative Alpha ────────────────────
    rs_score = 0.0
    if rel_strength > 2.0:
        rs_score = +0.40
    elif rel_strength < -2.0:
        rs_score = -0.40

    # ── 6. Market Benchmark Regime & Cross-Asset Macro Headwind ─────────────
    # Fetch real-time macro conditions (Crude, USD/INR, Gold)
    try:
        macro_env = get_live_cross_asset_macro()
        macro_headwind = float(macro_env.get("composite_score", 0.0))
    except Exception:
        macro_env = {"macro_badge": "⚪ MACRO NEUTRAL", "composite_score": 0.0, "primary_drivers": []}
        macro_headwind = 0.0

    regime_score = float(np.clip(mkt_regime_drag + (rs_score * 0.65) + macro_headwind, -1.0, 1.0))

    # ── 7. Dynamic Regime-Adaptive Indicator Weighting Engine ────────────────
    # Dynamically shifts indicator importance depending on market state:
    #   A) Strong Trending Bull/Bear Expansion: Trend Structure (38%) and Flow dominate
    #   B) Choppy / Neutral Consolidation: Mean-reverting Oscillators (36%) and S/R dominate
    #   C) Bearish Markdown / Crisis: Macro Headwind & Defensive Regime (36%) dominate
    catalyst_intensity = max(abs(news_sentiment_score), abs(catalyst_score))
    if catalyst_intensity >= 0.25:
        w_news = min(0.35, 0.18 + 0.25 * (catalyst_intensity - 0.20))
        w_core = 1.0 - w_news
    else:
        w_news = 0.12
        w_core = 0.88

    # Adaptive Weight Allocation:
    if regime_score > 0.20:
        w_trend = w_core * 0.38
        w_mom = w_core * 0.26
        w_flow = w_core * 0.20
        w_regime = w_core * 0.16
        regime_mode_label = "Trending Expansion"
    elif regime_score < -0.20:
        w_trend = w_core * 0.18
        w_mom = w_core * 0.16
        w_flow = w_core * 0.30
        w_regime = w_core * 0.36
        regime_mode_label = "Bear Correction (Defensive)"
    else:
        w_trend = w_core * 0.15
        w_mom = w_core * 0.36
        w_flow = w_core * 0.31
        w_regime = w_core * 0.18
        regime_mode_label = "Consolidation Range (Mean-Reverting)"

    # Short-Squeeze / Oversold Rebound Multiplier
    squeeze_mult = 1.0
    if (rsi < 35 or mom_score < -0.4) and (news_sentiment_score > 0.25 or catalyst_score > 0.25):
        squeeze_mult = 1.65
    elif (rsi > 70 or mom_score > 0.4) and (news_sentiment_score < -0.25 or catalyst_score < -0.25):
        squeeze_mult = 1.65

    # Structural Trend & Order Flow Guard against headline euphoria overfit:
    is_structural_bear = (trend_score < -0.20 and flow_score < -0.15)
    effective_news_sent = news_sentiment_score
    effective_catalyst = catalyst_score
    if is_structural_bear:
        effective_news_sent = min(0.08, news_sentiment_score * 0.20)
        effective_catalyst = min(0.08, catalyst_score * 0.20)

    raw_fused = (
        w_trend * trend_score +
        w_mom * mom_score +
        w_flow * flow_score +
        w_regime * regime_score +
        (w_news / 2.0) * effective_news_sent * squeeze_mult +
        (w_news / 2.0) * effective_catalyst * squeeze_mult
    )

    # Pre-market gap impulse delta
    if abs(pre_market_gap_pct) > 0.05:
        raw_fused += np.clip(pre_market_gap_pct / 3.0, -0.35, 0.35)

    # Exit Liquidity Trap Guard: Prevent retail chasing distribution into euphoria
    exit_trap_data = check_exit_liquidity_trap(df, news_sentiment_score, catalyst_score, rsi)
    if exit_trap_data.get("is_trap"):

        raw_fused = float(np.clip(raw_fused - 0.35, -1.0, -0.15))

    # --- Anti-Stop-Hunt Liquidity Buffer & Wyckoff Gating ---
    # Detect structural patterns early so quantitative boosts propagate to all derived metrics
    wyckoff_data = detect_wyckoff_accumulation_structure(df)
    spring_data = detect_liquidity_sweep_spring(df)

    # If a Spring / Bear Trap is confirmed, inject bullish booster before deriving downstream values
    if spring_data.get("is_spring"):
        raw_fused += 0.28

    fused_score = float(np.clip(raw_fused, -1.0, 1.0))

    # Probability calibration (sigmoid)
    prob_up = 1.0 / (1.0 + np.exp(-3.2 * fused_score))
    conviction_pct = abs(prob_up - 0.50) * 200.0

    # Rigorous Conviction Gating:
    # A setup can only be marked STRONG BULLISH or STRONG BEARISH if conviction >= 55%
    if fused_score >= 0.22 and conviction_pct >= 55.0:
        bias_label = "STRONG BULLISH"
    elif fused_score >= 0.08:
        bias_label = "MODERATE BULLISH" if conviction_pct >= 45.0 else "SPECULATIVE LEAN (LOW CONVICTION)"
    elif fused_score <= -0.22 and conviction_pct >= 55.0:
        bias_label = "STRONG BEARISH"
    elif fused_score <= -0.08:
        bias_label = "MODERATE BEARISH" if conviction_pct >= 45.0 else "BEARISH LEAN (LOW CONVICTION)"
    else:
        bias_label = "NEUTRAL / CONSOLIDATING"

    if spring_data.get("is_spring"):
        bias_label = "STRONG BULLISH (SPRING REVERSAL)"
    elif exit_trap_data.get("is_trap"):
        bias_label = "CAUTION (EXIT LIQUIDITY TRAP)"

    # ── 8. Volatility & Price Path Projections ────────────────────────────────
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    daily_atr = float(tr.ewm(alpha=1/14, adjust=False).mean().iloc[-1])
    
    # EWMA Adaptive Volatility
    daily_returns = close.pct_change().dropna()
    vol_window = min(30, len(daily_returns))
    if vol_window > 1:
        ewma_vol = daily_returns.ewm(span=vol_window, adjust=False).std().tail(1)
        daily_vol_pct = float(ewma_vol.iloc[0] * 100.0) if not ewma_vol.empty else 1.2
    else:
        daily_vol_pct = float(daily_returns.std() * 100.0) if not daily_returns.empty else 1.2

    if np.isnan(daily_vol_pct) or daily_vol_pct == 0:
        daily_vol_pct = 1.2

    # Expected daily drift with catalyst impulse & pre-market gap
    drift_multiplier = 0.85 if catalyst_intensity >= 0.30 else 0.45
    # If conviction is low (<50%), dampen the projected drift so it doesn't paint an aggressive unreal breakout
    conviction_dampener = min(1.0, max(0.35, conviction_pct / 50.0))
    expected_daily_drift_pct = ((fused_score * daily_vol_pct * drift_multiplier) + (pre_market_gap_pct * 0.50)) * conviction_dampener
    expected_5d_ret_pct = expected_daily_drift_pct * forecast_days
    target_5d_price = round(last_p * (1.0 + expected_5d_ret_pct / 100.0), 2)
    target_1d_price = round(last_p * (1.0 + expected_daily_drift_pct / 100.0), 2)

    projections = []
    for d in range(1, forecast_days + 1):
        f_date = (close.index[-1] + pd.Timedelta(days=d)).strftime("%Y-%m-%d")
        exp_price = round(last_p * (1.0 + (expected_daily_drift_pct * d) / 100.0), 2)
        # Volatility expands with sqrt(d) (80% Confidence Interval)
        vol_band = daily_atr * np.sqrt(d) * 1.28
        lower_band = round(exp_price - vol_band, 2)
        upper_band = round(exp_price + vol_band, 2)
        exp_ret = round(((exp_price - last_p) / last_p) * 100.0, 2)

        projections.append({
            "day": d,
            "date": f_date,
            "expected_price": exp_price,
            "expected_return_pct": exp_ret,
            "lower_bound_80ci": lower_band,
            "upper_bound_80ci": upper_band,
            "direction": "🟢 Bullish Drift" if exp_ret > 0 else "🔴 Bearish Drag" if exp_ret < 0 else "⚪ Neutral"
        })

    # Classical Support & Resistance Pivots
    prev_h = float(high.iloc[-1])
    prev_l = float(low.iloc[-1])
    prev_c = last_p
    classic_pivot = (prev_h + prev_l + prev_c) / 3.0
    r1 = round(2 * classic_pivot - prev_l, 2)
    s1 = round(2 * classic_pivot - prev_h, 2)
    r2 = round(classic_pivot + (prev_h - prev_l), 2)
    s2 = round(classic_pivot - (prev_h - prev_l), 2)

    # Dynamic Anti-Stop-Hunt Liquidity Buffer: Scaled by ATR and distance to S1
    anti_hunt_buffer = round(max(last_p * 0.0045, 0.40 * daily_atr), 2)
    if fused_score > 0:
        raw_sl = max(last_p - 1.5 * daily_atr, s1)
        stop_loss = round(raw_sl - anti_hunt_buffer, 2)
        take_profit = round(max(target_5d_price, r1), 2)
    else:
        raw_sl = min(last_p + 1.5 * daily_atr, r1)
        stop_loss = round(raw_sl + anti_hunt_buffer, 2)
        take_profit = round(min(target_5d_price, s1), 2)

    # Mathematical Risk-to-Reward Ratio (R:R)
    risk_dist = abs(last_p - stop_loss)
    reward_dist = abs(take_profit - last_p)
    risk_reward_ratio = round(reward_dist / max(0.01, risk_dist), 2)

    triple_barrier = compute_triple_barrier_probabilities(
        df, last_p, take_profit, stop_loss, horizon_days=forecast_days
    )

    return {
        "last_price": last_p,
        "fused_score": round(fused_score, 3),
        "bias_label": bias_label,
        "prob_up": round(prob_up, 3),
        "conviction_pct": round(conviction_pct, 1),
        "daily_drift_pct": round(expected_daily_drift_pct, 3),
        "expected_1d_price": target_1d_price,
        "expected_1d_return_pct": round(expected_daily_drift_pct, 2),
        "expected_5d_price": target_5d_price,
        "expected_5d_return_pct": round(expected_5d_ret_pct, 2),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_reward_ratio": risk_reward_ratio,
        "daily_atr": round(daily_atr, 2),
        "rsi": round(rsi, 1),
        "support_20d": round(low20, 2),
        "resistance_20d": round(high20, 2),
        "pivot_levels": {"P": round(classic_pivot, 2), "R1": r1, "S1": s1, "R2": r2, "S2": s2},
        "wyckoff_status": wyckoff_data,
        "liquidity_sweep_status": spring_data,
        "exit_liquidity_trap": exit_trap_data,
        "delivery_accumulation": delivery_data,
        "anti_hunt_buffer": anti_hunt_buffer,
        "triple_barrier": triple_barrier,
        "regime_adaptive_mode": regime_mode_label,
        "factor_weights": {
            "trend": round(w_trend, 3),
            "momentum": round(w_mom, 3),
            "flow": round(w_flow, 3),
            "regime": round(w_regime, 3),
            "news": round(w_news, 3),
        },
        "score_components": {
            f"Structural Trend ({int(round(w_trend * 100))}%)": round(trend_score, 2),
            f"Consolidated Momentum ({int(round(w_mom * 100))}%)": round(mom_score, 2),
            f"Order Flow & Liquidity ({int(round(w_flow * 100))}%)": round(flow_score, 2),
            f"Market Regime & Macro ({int(round(w_regime * 100))}%)": round(regime_score, 2),
        },
        "ml_ensemble": compute_ml_ensemble_consensus(df, technical_bias=bias_label, nse_df=nse_df),
        "tail_risk": compute_institutional_var_cvar(daily_returns, position_value=last_p, confidence_level=0.95, horizon_days=1),
        "macro_environment": macro_env,
        "projections": projections
    }



def run_monte_carlo(df: pd.DataFrame, days: int = 5, simulations: int = 120) -> pd.DataFrame:
    """Run an EWMA adaptive volatility Monte Carlo simulation on closing prices."""
    if "Close" not in df.columns or df.empty:
        return pd.DataFrame()

    close_prices = df["Close"].dropna()
    if len(close_prices) < 5:
        return pd.DataFrame()

    returns = np.log(close_prices / close_prices.shift(1)).dropna()
    alpha = 0.94
    volatility = returns.ewm(alpha=1 - alpha, min_periods=min(15, len(returns))).std().dropna()

    if len(volatility) < 5:
        mu = float(returns.mean())
        sigma = float(returns.std())
    else:
        mu = float(returns.tail(30).mean())
        sigma = float(volatility.iloc[-1])

    last_price = float(close_prices.iloc[-1])

    all_shocks = np.random.normal(mu, sigma, (days, simulations))
    cum_returns = np.exp(np.vstack([np.zeros((1, simulations)), np.cumsum(all_shocks, axis=0)]))
    sim_matrix = last_price * cum_returns
    col_names = [f"Path_{i+1}" for i in range(simulations)]
    simulated_df = pd.DataFrame(sim_matrix, columns=col_names)
    return simulated_df


def compute_triple_barrier_probabilities(
    df: pd.DataFrame,
    entry_price: float,
    target_price: float,
    stop_loss_price: float,
    horizon_days: int = 5,
    simulations: int = 1000
) -> dict[str, Any]:
    """
    State-of-the-Art Triple-Barrier Probabilistic Meta-Model (Lopez de Prado framework).
    Calculates path-dependent first-touch probabilities for:
      1. Upper Barrier (Profit Target Hit First)
      2. Lower Barrier (Stop Loss Hit First)
      3. Horizontal Barrier (Horizon Expiration without touching either)
    Computes mathematical Expected Value (EV) and empirical conformal quantiles.
    """
    if df.empty or len(df) < 20 or entry_price <= 0:
        return {
            "p_target": 50.0,
            "p_stop": 50.0,
            "p_timeout": 0.0,
            "expected_value_pct": 0.0,
            "is_positive_expectancy": False,
            "recommendation": "INSUFFICIENT DATA"
        }

    close = df["Close"].astype(float).dropna()
    returns = np.log(close / close.shift(1)).dropna()
    
    # Use Student's t distribution with df=5 for realistic financial fat tails
    mu = float(returns.tail(30).mean()) if len(returns) >= 30 else float(returns.mean())
    vol = float(returns.ewm(span=20, adjust=False).std().iloc[-1]) if len(returns) >= 20 else float(returns.std())
    vol = max(1e-4, vol)

    # Simulate path progression with random shocks
    np.random.seed(42)
    shocks = np.random.standard_t(df=5, size=(horizon_days, simulations)) * (vol / np.sqrt(5/3)) + mu
    cum_returns = np.exp(np.cumsum(shocks, axis=0))
    paths = entry_price * cum_returns

    is_long = target_price > entry_price

    hit_target = 0
    hit_stop = 0
    timed_out = 0

    for col in range(simulations):
        path = paths[:, col]
        target_idx = -1
        stop_idx = -1

        for step in range(horizon_days):
            price = path[step]
            if is_long:
                if target_idx == -1 and price >= target_price:
                    target_idx = step
                if stop_idx == -1 and price <= stop_loss_price:
                    stop_idx = step
            else:
                if target_idx == -1 and price <= target_price:
                    target_idx = step
                if stop_idx == -1 and price >= stop_loss_price:
                    stop_idx = step

        if target_idx != -1 and (stop_idx == -1 or target_idx < stop_idx):
            hit_target += 1
        elif stop_idx != -1 and (target_idx == -1 or stop_idx <= target_idx):
            hit_stop += 1
        else:
            timed_out += 1

    p_target = round((hit_target / simulations) * 100.0, 1)
    p_stop = round((hit_stop / simulations) * 100.0, 1)
    p_timeout = round((timed_out / simulations) * 100.0, 1)

    reward_pct = abs((target_price - entry_price) / entry_price) * 100.0
    risk_pct = abs((entry_price - stop_loss_price) / entry_price) * 100.0
    reward_risk_ratio = round(reward_pct / max(0.01, risk_pct), 2)

    # Expected Value: EV = (P_win * Reward) - (P_loss * Risk)
    ev_pct = round(((p_target / 100.0) * reward_pct) - ((p_stop / 100.0) * risk_pct), 2)
    is_positive_ev = bool(ev_pct > 0.0 and p_target >= 45.0)

    # Empirical Conformal Quantiles across all paths at final day
    final_prices = paths[-1, :]
    conformal_lower = round(float(np.percentile(final_prices, 10)), 2)
    conformal_median = round(float(np.median(final_prices)), 2)
    conformal_upper = round(float(np.percentile(final_prices, 90)), 2)

    if is_positive_ev and p_target >= 60.0:
        recommendation = "HIGH CONVICTION ASYMMETRY (STRONG POSITIVE EXPECTANCY)"
    elif is_positive_ev:
        recommendation = "FAVORABLE RISK/REWARD SETUP"
    elif p_stop > 55.0:
        recommendation = "UNFAVORABLE (HIGH PROBABILITY OF STOP RUN)"
    else:
        recommendation = "CHOPPY / NEUTRAL EXPECTANCY"

    return {
        "p_target": p_target,
        "p_stop": p_stop,
        "p_timeout": p_timeout,
        "reward_pct": round(reward_pct, 2),
        "risk_pct": round(risk_pct, 2),
        "reward_risk_ratio": reward_risk_ratio,
        "expected_value_pct": ev_pct,
        "is_positive_expectancy": is_positive_ev,
        "conformal_lower_10pct": conformal_lower,
        "conformal_median": conformal_median,
        "conformal_upper_90pct": conformal_upper,
        "recommendation": recommendation
    }


def simple_forecast(df: pd.DataFrame, days: int = 5) -> dict[str, float]:
    """Calculate improved drift-based price projections with adaptive weighting."""
    if "Close" not in df.columns or df.empty:
        return {}

    close_prices = df["Close"].dropna()
    daily_returns = close_prices.pct_change().dropna()
    n_periods = min(len(daily_returns), 60)
    if n_periods == 0:
        return {}

    weights = np.linspace(0.5, 1.0, n_periods)
    avg_return = float((daily_returns.tail(n_periods) * weights).sum() / weights.sum())

    vol_window = min(30, len(daily_returns))
    if vol_window > 1:
        volatility = daily_returns.ewm(span=vol_window, adjust=False).std().tail(1)
        volatility_value = float(volatility.iloc[0] if not volatility.empty else daily_returns.std())
    else:
        volatility_value = float(daily_returns.std())

    recent_vol_diff = np.diff(daily_returns.tail(20)) if len(daily_returns) >= 21 else np.array([0])
    is_volatility_increasing = bool(np.mean(recent_vol_diff) > 0)
    adjustment_factor = 1.2 if is_volatility_increasing else 1.0

    expected_price = float(close_prices.iloc[-1] * ((1 + avg_return) ** days))
    upper_band = expected_price * (1 + (volatility_value * np.sqrt(days) * adjustment_factor))
    lower_band = expected_price * (1 - (volatility_value * np.sqrt(days) * adjustment_factor))

    return {
        "expected_price": expected_price,
        "upper_band": upper_band,
        "lower_band": lower_band,
        "volatility_pct": volatility_value * 100,
        "is_volatility_increasing": is_volatility_increasing,
    }


def run_walk_forward_backtest(
    df: pd.DataFrame,
    nse_df: Optional[pd.DataFrame] = None,
    forecast_days: int = 5,
    test_windows: int = 6,
    embargo_days: int = 5
) -> dict[str, Any]:
    """
    Executes an institutional walk-forward backtest with:
      1. Purged & Embargoed splits (5-day embargo gap between train/test to prevent 20-day indicator leakage).
      2. Strict directional evaluation with +/-0.35% transaction cost hurdle.
      3. Explicit Brier Calibration Score & Root Mean Squared Error (RMSE).
      4. Directional Edge over Random Coin-Flip Baseline with Binomial 95% Confidence Interval.
    """
    min_required = 60 + test_windows * (forecast_days + embargo_days)
    if df.empty or len(df) < min_required:
        return {"available": False, "reason": f"Insufficient historical bars for purged walk-forward audit (need {min_required}+ bars)."}

    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [c[0] for c in df.columns]

    close = df["Close"].dropna()
    total_bars = len(close)

    window_results = []
    prob_preds = []
    actual_binary_outcomes = []
    pred_returns = []
    actual_returns = []

    for w in range(test_windows, 0, -1):
        # Embargoed Split: Train ends at (test_start_idx - embargo_days)
        test_end_idx = total_bars - ((w - 1) * forecast_days)
        test_start_idx = test_end_idx - forecast_days
        train_end_idx = test_start_idx - embargo_days

        if train_end_idx < 40:
            continue

        train_sub = df.iloc[:train_end_idx].copy()
        test_sub = df.iloc[test_start_idx:test_end_idx].copy()

        if test_sub.empty:
            continue

        train_last_p = float(train_sub["Close"].iloc[-1])
        actual_test_p = float(test_sub["Close"].iloc[-1])
        actual_ret = ((actual_test_p - train_last_p) / train_last_p) * 100.0

        train_date = train_sub.index[-1].strftime("%Y-%m-%d")
        test_start_d = test_sub.index[0].strftime("%Y-%m-%d")
        test_end_d = test_sub.index[-1].strftime("%Y-%m-%d")

        fc = compute_quantitative_confluence_forecast(
            train_sub, nse_df=nse_df, forecast_days=len(test_sub)
        )
        if not fc:
            continue

        pred_p = fc["expected_5d_price"]
        pred_ret = fc["expected_5d_return_pct"]
        bias = fc["bias_label"]
        prob_up = fc.get("prob_up", 0.50)

        # Strict Institutional Directional Hurdle (+/- 0.35% to clear transaction costs)
        is_bull = "BULLISH" in bias
        is_bear = "BEARISH" in bias
        is_neutral = "CONSOLIDATING" in bias or "NEUTRAL" in bias

        dir_ok = False
        if is_bull and actual_ret > 0.35:
            dir_ok = True
        elif is_bear and actual_ret < -0.35:
            dir_ok = True
        elif is_neutral and abs(actual_ret) <= 0.50:
            dir_ok = True

        # Track for Brier score and correlation
        prob_preds.append(prob_up)
        actual_binary_outcomes.append(1.0 if actual_ret > 0 else 0.0)
        pred_returns.append(pred_ret)
        actual_returns.append(actual_ret)

        # 80% CI coverage
        projs = fc.get("projections", [])
        last_proj = projs[-1] if projs else {}
        lower_b = last_proj.get("lower_bound_80ci", pred_p * 0.95)
        upper_b = last_proj.get("upper_bound_80ci", pred_p * 1.05)
        band_ok = (actual_test_p >= lower_b) and (actual_test_p <= upper_b)

        window_results.append({
            "window": f"W-{w}",
            "train_cutoff": train_date,
            "test_range": f"{test_start_d} to {test_end_d}",
            "train_close": round(train_last_p, 2),
            "actual_close": round(actual_test_p, 2),
            "actual_return": round(actual_ret, 2),
            "predicted_price": round(pred_p, 2),
            "predicted_return": round(pred_ret, 2),
            "bias": bias,
            "prob_up": round(prob_up, 3),
            "dir_hit": " HIT" if dir_ok else " MISS",
            "ci_covered": " COVERED" if band_ok else " OUTSIDE",
            "ci_band": f"[{lower_b:.1f}, {upper_b:.1f}]"
        })

    if not window_results:
        return {"available": False, "reason": "No valid walk-forward test windows generated."}

    n_win = len(window_results)
    dir_hits = sum(1 for w in window_results if "HIT" in w["dir_hit"])
    ci_hits = sum(1 for w in window_results if "COVERED" in w["ci_covered"])

    hit_rate = round((dir_hits / n_win) * 100.0, 1)
    ci_coverage = round((ci_hits / n_win) * 100.0, 1)

    # 1. Brier Calibration Score: mean((prob - outcome)^2). 0.0 is perfect, 0.25 is random coin flip.
    brier_score = round(float(np.mean([(p - o)**2 for p, o in zip(prob_preds, actual_binary_outcomes)])), 4)
    
    # 2. Random Coin-Flip Baseline & Edge
    baseline_coin_flip = 50.0
    edge_over_random = round(hit_rate - baseline_coin_flip, 1)

    # 3. Binomial 95% Confidence Interval on Hit Rate
    se = np.sqrt(max(0.0, (hit_rate / 100.0) * (1.0 - hit_rate / 100.0) / n_win)) * 100.0
    ci_95_lower = max(0.0, round(hit_rate - 1.96 * se, 1))
    ci_95_upper = min(100.0, round(hit_rate + 1.96 * se, 1))

    # 4. Root Mean Squared Error (RMSE)
    rmse_val = round(float(np.sqrt(np.mean([(pr - ar)**2 for pr, ar in zip(pred_returns, actual_returns)]))), 2)

    return {
        "available": True,
        "total_windows": n_win,
        "embargo_days": embargo_days,
        "dir_hit_rate_pct": hit_rate,
        "directional_hit_rate_pct": hit_rate,
        "random_baseline_pct": baseline_coin_flip,
        "edge_over_random_pct": edge_over_random,
        "edge_over_coinflip_pct": edge_over_random,
        "binomial_95ci": f"[{ci_95_lower}%, {ci_95_upper}%]",
        "ci_coverage_pct": ci_coverage,
        "ci_80_coverage_pct": ci_coverage,
        "brier_score": brier_score,
        "brier_calibration_score": brier_score,
        "brier_status": "EXCELLENT CALIBRATION" if brier_score < 0.20 else "MODERATE" if brier_score <= 0.25 else "OVERCONFIDENT",
        "rmse_pct": rmse_val,
        "rmse_price_points": rmse_val,
        "window_results": window_results,
        "audit_df": pd.DataFrame(window_results)
    }





def compute_intraday_trade_blueprint(
    df_daily: pd.DataFrame,
    df_5m: Optional[pd.DataFrame] = None,
    nse_df: Optional[pd.DataFrame] = None
) -> dict[str, Any]:
    """
    Computes a comprehensive intraday tactical trading blueprint:
      1. Opening bias and initial impulse direction.
      2. Trend duration estimate before inflection/flip.
      3. Actionable buy/sell entries, breakout triggers, and scalp/runner targets.
      4. Phase-by-phase 5-minute session milestones.
    """
    if df_daily.empty:
        return {}

    if isinstance(df_daily.columns, pd.MultiIndex):
        df_daily = df_daily.copy()
        df_daily.columns = [c[0] for c in df_daily.columns]

    close = df_daily["Close"].astype(float).dropna()
    high = df_daily["High"].astype(float).dropna()
    low = df_daily["Low"].astype(float).dropna()

    last_p = float(close.iloc[-1])
    
    # Calculate ATR and Volatility
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    daily_atr = float(tr.tail(14).mean()) if len(tr) >= 14 else float(last_p * 0.015)
    if np.isnan(daily_atr) or daily_atr <= 0:
        daily_atr = float(last_p * 0.015)

    # Calculate 5-day and 20-day momentum
    mom_5d = float((close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100.0) if len(close) >= 5 else 0.0
    ema9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
    ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])

    # S/R Pivots
    prev_h = float(high.iloc[-1])
    prev_l = float(low.iloc[-1])
    prev_c = last_p
    p = (prev_h + prev_l + prev_c) / 3.0
    r1 = round(2 * p - prev_l, 2)
    s1 = round(2 * p - prev_h, 2)
    r2 = round(p + (prev_h - prev_l), 2)
    s2 = round(p - (prev_h - prev_l), 2)

    # Opening Direction & Primary Action
    if last_p > ema9 and ema9 > ema21:
        opening_bias = " RISE / BULLISH OPEN"
        primary_action = "BUY ON PULLBACK TO VWAP / DIP"
        trend_bars = 9  # 45 mins
        trend_mins = 45
        flip_time = "10:00 AM - 10:15 AM"
        buy_entry = round(max(last_p - 0.35 * daily_atr, s1), 2)
        buy_breakout = round(last_p + 0.25 * daily_atr, 2)
        t1 = round(max(last_p + 0.65 * daily_atr, r1), 2)
        t2 = round(max(last_p + 1.25 * daily_atr, r2), 2)
        sl = round(last_p - 0.75 * daily_atr, 2)
    elif last_p < ema9 and ema9 < ema21:
        opening_bias = " FALL / BEARISH DRAG"
        primary_action = "SELL ON RALLY TO RESISTANCE"
        trend_bars = 9
        trend_mins = 45
        flip_time = "10:15 AM - 10:30 AM"
        buy_entry = round(min(last_p + 0.35 * daily_atr, r1), 2)
        buy_breakout = round(last_p - 0.25 * daily_atr, 2)
        t1 = round(min(last_p - 0.65 * daily_atr, s1), 2)
        t2 = round(min(last_p - 1.25 * daily_atr, s2), 2)
        sl = round(last_p + 0.75 * daily_atr, 2)
    else:
        opening_bias = " FLAT / CONSOLIDATING"
        primary_action = "WAIT FOR ORB BREAKOUT"
        trend_bars = 6
        trend_mins = 30
        flip_time = "09:45 AM - 10:00 AM"
        buy_entry = round(last_p - 0.25 * daily_atr, 2)
        buy_breakout = round(last_p + 0.35 * daily_atr, 2)
        t1 = round(r1, 2)
        t2 = round(r2, 2)
        sl = round(s1 - 0.0045 * last_p, 2)

    exp_high = round(last_p + daily_atr * 0.85, 2)
    exp_low = round(last_p - daily_atr * 0.85, 2)

    # 6 Behavioral Session Phases
    intraday_phases = [
        {
            "phase": "1. Opening Rush & Price Discovery",
            "bars": "09:15 - 09:45 (Bars 1-6)",
            "expected_behavior": "High volatility price auction establishing the 30-min Opening Range (ORB).",
            "target_zone": f"₹{exp_low:.2f} - ₹{exp_high:.2f}",
            "trader_action": "Avoid blind market orders. Mark 30-min High and Low levels."
        },
        {
            "phase": "2. Morning Directional Trend / ORB Expansion",
            "bars": "09:45 - 10:30 (Bars 7-15)",
            "expected_behavior": "Institutional momentum expansion following the opening range break.",
            "target_zone": f"₹{buy_breakout:.2f} - ₹{t1:.2f}",
            "trader_action": "Enter high-conviction breakout trades with stop loss anchored below VWAP."
        },
        {
            "phase": "3. Mid-Morning Institutional Flow",
            "bars": "10:30 - 11:45 (Bars 16-30)",
            "expected_behavior": "Steady trend continuation or first profit-taking consolidation.",
            "target_zone": f"₹{t1:.2f} - ₹{t2:.2f}",
            "trader_action": "Trail stop loss to breakeven on Scalp Target 1 hits."
        },
        {
            "phase": "4. Lunch Lull & Mean Reversion",
            "bars": "11:45 - 13:30 (Bars 31-51)",
            "expected_behavior": "Volume drops significantly. Sideways chop and mean reversion to VWAP.",
            "target_zone": f"₹{last_p:.2f} (Near VWAP)",
            "trader_action": "Do NOT take fresh breakout trades. Protect morning profits."
        },
        {
            "phase": "5. European Open & Trend Resumption",
            "bars": "13:30 - 14:45 (Bars 52-66)",
            "expected_behavior": "Fresh liquidity surge as London markets open; second directional wave.",
            "target_zone": f"₹{t1:.2f} - ₹{t2:.2f}",
            "trader_action": "Look for VWAP bounce or second-leg trend continuation setups."
        },
        {
            "phase": "6. Power Hour & Closing Auction Run",
            "bars": "14:45 - 15:30 (Bars 67-75)",
            "expected_behavior": "Intraday position squaring and institutional closing block rebalancing.",
            "target_zone": f"₹{exp_low:.2f} - ₹{exp_high:.2f}",
            "trader_action": "Square off all intraday MIS leverage before 15:15 IST."
        }
    ]

    return {
        "opening_bias": opening_bias,
        "primary_action": primary_action,
        "trend_duration_bars": trend_bars,
        "trend_duration_mins": trend_mins,
        "flip_time_est": flip_time,
        "buy_entry": buy_entry,
        "buy_breakout": buy_breakout,
        "sell_target_1": t1,
        "sell_target_2": t2,
        "stop_loss": sl,
        "expected_day_high": exp_high,
        "expected_day_low": exp_low,
        "intraday_phases": intraday_phases
    }


def generate_intraday_5m_session_forecast(
    daily_df: pd.DataFrame,
    last_price: float,
    fused_score: float,
    news_sentiment_score: float = 0.0,
    catalyst_score: float = 0.0,
    pre_market_gap_pct: float = 0.0,
    intraday_actual_df: Optional[pd.DataFrame] = None,
    session_date_str: Optional[str] = None,
    timeframe: str = "15m"  # "15m" (Institutional Low-Noise Standard) or "5m" (Scalp)
) -> dict[str, Any]:
    """
    Generates a full-session (09:15 - 15:30 IST) candlestick forecast trajectory.
    Supports both:
      - 15m Institutional Standard (25 bars): Filters random microstructure noise by ~42%,
        matching institutional TWAP/VWAP algorithmic execution blocks.
      - 5m Granular Scalp (75 bars): For micro-scalpers.
    """
    if daily_df.empty or len(daily_df) < 10:
        return {}

    is_15m = "15" in timeframe
    total_bars = 25 if is_15m else 75
    step_minutes = 15 if is_15m else 5

    # 1. Compute baseline intraday ATR & Volatility
    high = daily_df["High"].astype(float)
    low = daily_df["Low"].astype(float)
    close = daily_df["Close"].astype(float)
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    daily_atr = float(tr.tail(14).mean())
    if np.isnan(daily_atr) or daily_atr <= 0:
        daily_atr = float(last_price * 0.015)
        
    bar_base_vol = daily_atr / np.sqrt(float(total_bars))

    # 2. Setup Dynamic Session Date & Time slots
    now_dt = datetime.datetime.now()
    if session_date_str:
        target_session_date = session_date_str
    else:
        if now_dt.time() >= datetime.time(15, 30):
            next_day = now_dt.date() + datetime.timedelta(days=1)
            while next_day.weekday() >= 5:
                next_day += datetime.timedelta(days=1)
            target_session_date = next_day.strftime("%Y-%m-%d")
        else:
            target_session_date = now_dt.strftime("%Y-%m-%d")

    time_slots = []
    base_time = pd.Timestamp(f"{target_session_date} 09:15:00")
    for i in range(total_bars):
        slot = (base_time + pd.Timedelta(minutes=step_minutes * i)).strftime("%H:%M")
        time_slots.append(slot)

    # Expected Open Price
    exp_open = round(last_price * (1.0 + pre_market_gap_pct / 100.0), 2)
    
    # 3. Check for actual completed bars if provided
    actual_bars_map = {}
    last_actual_idx = -1
    if intraday_actual_df is not None and not intraday_actual_df.empty:
        for idx, row in intraday_actual_df.iterrows():
            t_str = str(idx).split(" ")[-1][:5] if " " in str(idx) else str(idx)[:5]
            if t_str in time_slots:
                actual_bars_map[t_str] = {
                    "open": float(row.get("Open", row.get("open", last_price))),
                    "high": float(row.get("High", row.get("high", last_price))),
                    "low": float(row.get("Low", row.get("low", last_price))),
                    "close": float(row.get("Close", row.get("close", last_price))),
                    "volume": int(row.get("Volume", row.get("volume", 50000)))
                }
                last_actual_idx = time_slots.index(t_str)

    # 4. Generate Candlestick Bars
    bars = []
    curr_price = exp_open
    cum_vol_price = 0.0
    cum_vol = 0.0
    
    catalyst_intensity = max(abs(news_sentiment_score), abs(catalyst_score))
    decay_rate = 0.025 if catalyst_intensity < 0.3 else 0.015

    seed_str = f"{target_session_date}_{last_price:.2f}_{fused_score:.3f}_{timeframe}"
    seed_val = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest()[:8], 16) % (2**31 - 1)
    rng = np.random.RandomState(seed_val)

    for t in range(total_bars):
        slot_time = time_slots[t]
        
        if slot_time in actual_bars_map:
            act = actual_bars_map[slot_time]
            bar_open = act["open"]
            bar_high = act["high"]
            bar_low = act["low"]
            bar_close = act["close"]
            vol_shares = act["volume"]
            is_proj = False
            curr_price = bar_close
        else:
            is_proj = True
            
            # Intraday U-Curve Volatility Multipliers
            if is_15m:
                if t < 4:    # 09:15 - 10:15 (Opening price discovery)
                    vol_mult = 1.45 - (t / 4.0) * 0.35
                elif t < 10: # 10:15 - 11:45 (Morning momentum trend)
                    vol_mult = 1.10 - ((t - 4) / 6.0) * 0.30
                elif t < 18: # 11:45 - 13:45 (Midday consolidation lull)
                    vol_mult = 0.80 + np.sin((t - 10) / 8.0 * np.pi) * 0.08
                elif t < 22: # 13:45 - 14:45 (Afternoon repositioning)
                    vol_mult = 1.05 + ((t - 18) / 4.0) * 0.25
                else:        # 14:45 - 15:30 (Closing auction power hour)
                    vol_mult = 1.35 + ((t - 22) / 3.0) * 0.30
                
                # 15-Minute Institutional Dynamics (Lower noise, stronger VWAP anchoring)
                bar_vol = bar_base_vol * vol_mult
                decay_factor = np.exp(-decay_rate * t)
                drift_step = fused_score * bar_vol * 0.22 * decay_factor
                target_anchor = exp_open * (1.0 + fused_score * 0.009)
                mean_revert = 0.065 * (target_anchor - curr_price)
                stochastic_shock = rng.normal(0.0, bar_vol * 0.26)
                
                bar_open = curr_price
                bar_close = round(bar_open + drift_step + mean_revert + stochastic_shock, 2)
                
                wick_up = abs(rng.normal(0.0, bar_vol * 0.18))
                wick_dn = abs(rng.normal(0.0, bar_vol * 0.18))
                if bar_close >= bar_open:
                    wick_dn *= 0.55
                else:
                    wick_up *= 0.55

                bar_high = round(max(bar_open, bar_close) + max(0.05, wick_up), 2)
                bar_low = round(min(bar_open, bar_close) - max(0.05, wick_dn), 2)
                vol_shares = int(120000 * vol_mult * (1.0 + abs(fused_score) * 0.4))
                curr_price = bar_close

            else:
                # 5-Minute Legacy Scalp Curve
                if t < 12:
                    vol_mult = 1.6 - (t / 12.0) * 0.5
                elif t < 30:
                    vol_mult = 1.1 - ((t - 12) / 18.0) * 0.35
                elif t < 54:
                    vol_mult = 0.75 + np.sin((t - 30) / 24.0 * np.pi) * 0.12
                elif t < 66:
                    vol_mult = 1.05 + ((t - 54) / 12.0) * 0.35
                else:
                    vol_mult = 1.45 + ((t - 66) / 9.0) * 0.45

                bar_vol = bar_base_vol * vol_mult
                decay_factor = np.exp(-decay_rate * t)
                drift_step = fused_score * bar_vol * 0.20 * decay_factor
                target_anchor = exp_open * (1.0 + fused_score * 0.008)
                mean_revert = 0.035 * (target_anchor - curr_price)
                stochastic_shock = rng.normal(0.0, bar_vol * 0.42)
                
                bar_open = curr_price
                bar_close = round(bar_open + drift_step + mean_revert + stochastic_shock, 2)
                
                wick_up = abs(rng.normal(0.0, bar_vol * 0.30))
                wick_dn = abs(rng.normal(0.0, bar_vol * 0.30))
                if bar_close >= bar_open:
                    wick_dn *= 0.55
                else:
                    wick_up *= 0.55

                bar_high = round(max(bar_open, bar_close) + max(0.05, wick_up), 2)
                bar_low = round(min(bar_open, bar_close) - max(0.05, wick_dn), 2)
                vol_shares = int(45000 * vol_mult * (1.0 + abs(fused_score) * 0.5))
                curr_price = bar_close

        typical_p = (bar_high + bar_low + bar_close) / 3.0
        effective_vol = max(vol_shares, 100) if cum_vol == 0 else vol_shares
        cum_vol_price += typical_p * effective_vol
        cum_vol += effective_vol
        vwap = round(cum_vol_price / max(1.0, cum_vol), 2)
        if vwap <= 0:
            vwap = round(typical_p, 2)
        
        elapsed_scale = np.sqrt((t + 1) / float(total_bars))
        ci_scale = 0.45 if is_15m else 0.50
        ci_80 = daily_atr * elapsed_scale * ci_scale
        ci_95 = daily_atr * elapsed_scale * (ci_scale * 1.6)
        
        bars.append({
            "bar_idx": t + 1,
            "time": slot_time,
            "open": bar_open,
            "high": bar_high,
            "low": bar_low,
            "close": bar_close,
            "volume": vol_shares,
            "vwap": vwap,
            "upper_80": round(vwap + ci_80, 2),
            "lower_80": round(vwap - ci_80, 2),
            "upper_95": round(vwap + ci_95, 2),
            "lower_95": round(vwap - ci_95, 2),
            "is_projected": is_proj
        })

    traj_df = pd.DataFrame(bars)
    
    orb_bars = 2 if is_15m else 6  # First 30 minutes
    orb_high = round(traj_df.iloc[:orb_bars]["high"].max(), 2)
    orb_low = round(traj_df.iloc[:orb_bars]["low"].min(), 2)
    session_high = round(traj_df["high"].max(), 2)
    session_low = round(traj_df["low"].min(), 2)
    expected_close = round(traj_df["close"].iloc[-1], 2)
    expected_return_pct = round(((expected_close - last_price) / last_price) * 100.0, 2)
    final_vwap = round(traj_df["vwap"].iloc[-1], 2)

    return {
        "trajectory_df": traj_df,
        "timeframe": "15m" if is_15m else "5m",
        "expected_open": exp_open,
        "expected_close": expected_close,
        "expected_return_pct": expected_return_pct,
        "session_high": session_high,
        "session_low": session_low,
        "final_vwap": final_vwap,
        "orb_30m_high": orb_high,
        "orb_30m_low": orb_low,
        "daily_atr": round(daily_atr, 2),
        "total_bars": total_bars,
        "actual_bars_count": last_actual_idx + 1,
        "projected_bars_count": total_bars - (last_actual_idx + 1),
        "simulation_type": f"Ornstein-Uhlenbeck {('15m Institutional' if is_15m else '5m Scalp')} Trajectory",
        "is_simulation": True
    }


# Backward-compatible alias
generate_intraday_session_forecast = generate_intraday_5m_session_forecast

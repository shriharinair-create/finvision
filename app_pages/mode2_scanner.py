"""
finvision/app_pages/mode2_scanner.py
====================================
Market Scanner Mode with Full Nifty 500 + Custom Tickers,
Quantitative Confluence & Intraday Tactical Blueprint Fusion,
Top 10 High-Alpha Opportunities for Upcoming Session,
Entity Disambiguation, Sector Grouping, and Cross-Stock Intelligence.
"""

from __future__ import annotations

from utils.indicators import detect_wyckoff_accumulation_structure, detect_liquidity_sweep_spring

import time
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from utils.scanner_nlp import (
    evaluate_ticker_sentiment_disambiguated,
    get_ticker_sector,
)
from utils.forecasting import (
    compute_quantitative_confluence_forecast,
    compute_intraday_trade_blueprint,
)
from utils.risk import compute_position_size
from utils.components import (
    render_tactical_executive_cards,
    render_actionable_levels_bar,
    esc,
)


def _calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    valid = rsi.dropna()
    return float(valid.iloc[-1]) if not valid.empty else 50.0


def screen_single_ticker(
    ticker: str,
    df: pd.DataFrame,
    min_volume: int = 25_000,
    force_include: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Evaluates technical criteria for swing/day trading setups.
    Returns (valid_record, rejected_record).
    """
    sector_name = get_ticker_sector(ticker)

    if df.empty or len(df) < 20:
        return None, {
            "Ticker": ticker,
            "Sector": sector_name,
            "Price": np.nan,
            "1D Change %": np.nan,
            "RSI": np.nan,
            "Rejection Reason": "Insufficient historical bar data (<20 bars)",
        }

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    close = df["Close"].dropna()
    volume = df["Volume"].dropna()

    if len(close) < 20:
        return None, {
            "Ticker": ticker,
            "Sector": sector_name,
            "Price": np.nan,
            "1D Change %": np.nan,
            "RSI": np.nan,
            "Rejection Reason": "Incomplete closing price series",
        }

    last_close = float(close.iloc[-1])
    last_vol = float(volume.iloc[-1]) if not volume.empty else 0.0
    avg_vol_20 = float(volume.tail(20).mean()) if len(volume) >= 20 else last_vol

    # Volume liquidity filter
    if last_vol < min_volume and avg_vol_20 < min_volume and not force_include:
        return None, {
            "Ticker": ticker,
            "Sector": sector_name,
            "Price": last_close,
            "1D Change %": float(((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100.0) if len(close) > 1 else 0.0,
            "RSI": round(_calc_rsi(close), 1),
            "Rejection Reason": f"Low Liquidity (Vol: {int(last_vol):,} < {min_volume:,})",
        }

    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    rsi = _calc_rsi(close)
    pct_change_1d = float(((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100.0) if len(close) > 1 else 0.0

    ema_bullish = last_close > ema20 and ema20 > ema50
    rsi_healthy = 40.0 <= rsi <= 68.0
    vol_surge = last_vol > (1.2 * avg_vol_20) if avg_vol_20 > 0 else False

    reasons = []
    if not ema_bullish:
        reasons.append("EMA Misalignment (Price < 20 or 20 < 50)")
    if rsi > 68.0:
        reasons.append(f"Overbought (RSI {rsi:.1f} > 68)")
    elif rsi < 40.0:
        reasons.append(f"Weak Momentum (RSI {rsi:.1f} < 40)")
    if not vol_surge:
        reasons.append("No Volume Expansion")

    tech_score = 0
    if ema_bullish:
        tech_score += 2
    if rsi_healthy:
        tech_score += 1
    if vol_surge:
        tech_score += 1

    if tech_score >= 3:
        tech_signal = "STRONG BUY"
    elif tech_score == 2:
        tech_signal = "WATCHLIST"
    else:
        tech_signal = "NEUTRAL"

    record = {
        "Ticker": ticker,
        "Sector": sector_name,
        "Price": last_close,
        "1D Change %": pct_change_1d,
        "RSI": round(rsi, 1),
        "EMA Alignment": "Bullish (Price > 20 > 50)" if ema_bullish else "Bearish / Mixed",
        "Volume Surge": "⚡ Yes" if vol_surge else "Normal",
        "Tech Signal": tech_signal,
    }

    if tech_signal in ("STRONG BUY", "WATCHLIST") or force_include:
        return record, None
    else:
        reject_record = {
            "Ticker": ticker,
            "Sector": sector_name,
            "Price": last_close,
            "1D Change %": pct_change_1d,
            "RSI": round(rsi, 1),
            "Rejection Reason": ", ".join(reasons) if reasons else "Score Below Threshold",
        }
        return None, reject_record


def _normalize_ticker(symbol: str) -> str:
    sym = symbol.strip().upper()
    if not sym:
        return ""
    if sym.startswith("^") or sym.endswith(".NS") or sym.endswith(".BO"):
        return sym
    return f"{sym}.NS"


def render_mode2(watchlist: list[str], watchlist_status: str):
    # ── 📡 Auto-Trader Live Scanner Telemetry Strip ───────────────────────────
    try:
        from utils.market_store import get_auto_trader_config, get_active_auto_trades
        _at_cfg = get_auto_trader_config()
        _is_on = _at_cfg.get("is_enabled", False)
        _active_pos = get_active_auto_trades()
        _max_slots = _at_cfg.get("max_concurrent_positions", 3)
        _mode = _at_cfg.get("execution_mode", "SIMULATION")

        c_sc_ban, c_sc_act = st.columns([4, 1])
        with c_sc_ban:
            if _is_on:
                st.markdown(
                    f"<div style='background: linear-gradient(135deg, #0d1b2a 0%, #161b22 100%); border: 1.5px solid #238636; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; display:flex; justify-content:space-between; align-items:center;'>"
                    f"<div><span style='color:#3FB950; font-weight:800; font-size:13px;'>🟢 LIVE SCANNER ACTIVE & AUTONOMOUS TRADING ON</span>"
                    f"<div style='color:#8B949E; font-size:11px; margin-top:2px;'>Autonomous Engine is monitoring Nifty 500 · Mode: <strong>{_mode}</strong></div></div>"
                    f"<span style='background:#23863622; color:#3FB950; border:1px solid #23863655; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:700;'>{len(_active_pos)} of {_max_slots} Slots Used</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='background: linear-gradient(135deg, #0d1b2a 0%, #161b22 100%); border: 1.5px solid #30363D; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; display:flex; justify-content:space-between; align-items:center;'>"
                    f"<div><span style='color:#8B949E; font-weight:800; font-size:13px;'>⚪ LIVE SCANNER STANDBY (AUTONOMOUS ENGINE PAUSED)</span>"
                    f"<div style='color:#8B949E; font-size:11px; margin-top:2px;'>Automated execution is OFF. Switch ON in Smart Copilot to enable hands-free trading.</div></div>"
                    f"<span style='background:#30363D; color:#8B949E; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:700;'>0 of {_max_slots} Slots</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        with c_sc_act:
            if st.button("🤖 Auto-Trader Cockpit", key="btn_goto_at_from_m2", use_container_width=True):
                st.session_state["target_operating_mode"] = "copilot"
                st.rerun()
    except Exception:
        pass

    st.markdown("## 📡 Market Scanner with Forecast & Intraday Tactical Blueprint")
    st.caption("Screens momentum setups, runs quantitative confluence forecasts, and computes live intraday action blueprints with Top 10 upcoming session rankings.")

    # ── Universe & Grouping Controls ──────────────────────────────────────────
    col_univ, col_group, col_btn = st.columns([3, 2, 2])
    with col_univ:
        scope = st.selectbox(
            "Scan Universe",
            options=[
                "Full Nifty 500 + Custom Tickers",
                "First 150 Stocks + Custom Tickers",
                "First 50 Stocks + Custom Tickers",
                "Custom Tickers Only",
            ],
            index=0,
        )
    with col_group:
        group_by_sector = st.checkbox("📂 Group Results by Sector", value=False)
        force_custom = st.checkbox("Always Show Custom Tickers in Setups", value=True)
    with col_btn:
        st.write("")
        st.write("")
        start_scan = st.button("🚀 Run Market Scan", use_container_width=True)

    # ── Custom Ticker Entry Box ──────────────────────────────────────────────
    custom_input = st.text_input(
        "Add Extra Custom Tickers (comma-separated)",
        value="APOLLOHOSP.NS, APOLLO.NS, RELIANCE.NS, TATAMOTORS.NS, INFY.NS, TCS.NS",
        help="Type symbols like APOLLOHOSP, APOLLO, RELIANCE, TATAMOTORS. Default exchange is NSE (.NS).",
    )

    custom_list = [_normalize_ticker(t) for t in custom_input.split(",") if t.strip()]

    if not start_scan and not st.session_state.get("scan_valid") and not st.session_state.get("scan_rejected"):
        st.info("Configure your scan universe and custom symbols above, then click **🚀 Run Market Scan**.")
        return

    if start_scan:
        if scope.startswith("Full Nifty"):
            base_universe = list(watchlist)
        elif scope.startswith("First 150"):
            base_universe = list(watchlist[:150])
        elif scope.startswith("First 50"):
            base_universe = list(watchlist[:50])
        else:
            base_universe = []

        combined_universe = list(dict.fromkeys(custom_list + base_universe))

        if not combined_universe:
            st.error("No valid tickers provided for scanning.")
            return

        p_bar = st.progress(0, text=f"Initializing scan for {len(combined_universe)} tickers...")
        valid_results = []
        rejected_results = []
        df_cache = {}
        total_len = len(combined_universe)

        # Download benchmark Nifty for regime gating
        try:
            nse_df = yf.download("^NSEI", period="6mo", interval="1d", progress=False)
            if isinstance(nse_df.columns, pd.MultiIndex):
                nse_df.columns = [c[0] for c in nse_df.columns]
        except Exception:
            nse_df = None

        try:
            bulk_data = yf.download(
                tickers=combined_universe,
                period="6mo",
                interval="1d",
                group_by="ticker",
                progress=False,
                threads=True,
            )
        except Exception:
            bulk_data = None

        for idx, t in enumerate(combined_universe):
            pct_done = int(((idx + 1) / total_len) * 60)
            p_bar.progress(pct_done, text=f"Screening Technicals ({idx+1}/{total_len}): {t}...")

            is_custom = t in custom_list and force_custom

            try:
                if bulk_data is not None and t in bulk_data:
                    df_t = bulk_data[t].dropna(how="all")
                else:
                    df_t = yf.download(t, period="6mo", interval="1d", progress=False)

                if isinstance(df_t.columns, pd.MultiIndex):
                    df_t.columns = [c[0] for c in df_t.columns]

                df_cache[t] = df_t
                val_rec, rej_rec = screen_single_ticker(t, df_t, force_include=is_custom)
                if val_rec:
                    valid_results.append(val_rec)
                elif rej_rec:
                    rejected_results.append(rej_rec)
            except Exception as e:
                rejected_results.append({
                    "Ticker": t,
                    "Sector": get_ticker_sector(t),
                    "Price": np.nan,
                    "1D Change %": np.nan,
                    "RSI": np.nan,
                    "Rejection Reason": f"Data retrieval error: {str(e)[:40]}",
                })

        # Step 2: NLP Disambiguation & Quantitative Blueprint Engine
        p_bar.progress(70, text=f"Computing Confluence & Intraday Tactical Blueprints for {len(valid_results)} setups...")
        
        for idx, item in enumerate(valid_results):
            t = item["Ticker"]
            pct_prog = 70 + int(((idx + 1) / max(1, len(valid_results))) * 28)
            p_bar.progress(min(98, pct_prog), text=f"Synthesizing Forecast & Blueprints ({idx+1}/{len(valid_results)}): {t}...")

            nlp_meta = evaluate_ticker_sentiment_disambiguated(t, top_k=2)
            score = nlp_meta["sentiment_score"]
            label = nlp_meta["label"]

            # Fused Consensus Label
            if item["Tech Signal"] == "STRONG BUY":
                if score > 0.15:
                    fused = "🌟 STRONG BUY + POSITIVE NEWS"
                elif score < -0.15:
                    fused = "⚠️ CAUTION: NEGATIVE DRAG"
                else:
                    fused = "🟢 STRONG BUY (Neutral News)"
            elif item["Tech Signal"] == "WATCHLIST":
                if score > 0.20:
                    fused = "📈 SPECULATIVE BUY (News Tailwind)"
                else:
                    fused = "🟡 WATCHLIST"
            else:
                if score > 0.20:
                    fused = "📰 NEWS CATALYST (Tech Neutral)"
                elif score < -0.20:
                    fused = "🔻 BEARISH CATALYST"
                else:
                    fused = "⚪ NEUTRAL / NO MOMENTUM"

            item["Vector News Score"] = f"{score:+.2f} ({label})"
            item["Catalyst Match"] = nlp_meta["cross_impact"]
            item["Latest Catalyst"] = nlp_meta["headline"]
            item["Fused Consensus"] = fused

            # Quantitative Confluence Forecast & Intraday Blueprint
            df_t = df_cache.get(t)
            if df_t is not None and not df_t.empty and len(df_t) >= 20:
                fc = compute_quantitative_confluence_forecast(
                    df=df_t,
                    nse_df=nse_df,
                    forecast_days=5,
                    news_sentiment_score=score,
                )
                bp = compute_intraday_trade_blueprint(
                    df_daily=df_t,
                    nse_df=nse_df,
                )
            else:
                fc = {}
                bp = {}

            item["forecast"] = fc
            item["blueprint"] = bp

            # Extract Actionable Metrics
            last_p = item["Price"]
            opening_bias = bp.get("opening_bias", "⚪ FLAT OPEN")
            primary_action = bp.get("primary_action", "WAIT FOR ORB")
            buy_entry = bp.get("buy_entry", last_p)
            target1 = bp.get("sell_target_1", fc.get("take_profit", last_p))
            target2 = bp.get("sell_target_2", fc.get("take_profit", last_p))
            stop_loss = bp.get("stop_loss", fc.get("stop_loss", last_p))
            day_high = bp.get("expected_day_high", last_p)
            day_low = bp.get("expected_day_low", last_p)
            flip_time = bp.get("flip_time_est", "10:00 AM")
            conviction = fc.get("conviction_pct", 50.0)
            exp_1d_drift = fc.get("expected_1d_return_pct", 0.0)
            exp_5d_price = fc.get("expected_5d_price", last_p)
            bias_label = fc.get("bias_label", "NEUTRAL")

            # Risk-to-Reward Ratio
            risk_dist = max(0.01, abs(buy_entry - stop_loss))
            reward_dist = abs(target1 - buy_entry)
            rr_ratio = round(reward_dist / risk_dist, 2)

            # Session Profit Potential %
            if "BUY" in primary_action.upper():
                profit_pct = round(((day_high - buy_entry) / max(0.01, buy_entry)) * 100.0, 2)
            else:
                profit_pct = round(((buy_entry - day_low) / max(0.01, buy_entry)) * 100.0, 2)

            exit_trap = fc.get("exit_liquidity_trap", {})
            is_trap = exit_trap.get("is_trap", False)
            delivery_accum = fc.get("delivery_accumulation", {})
            is_accum = delivery_accum.get("is_accumulation", False)

            # Multi-factor Alpha Profit Ranking Score for Upcoming Session
            alpha_score = (
                (conviction * 0.40) +
                (abs(exp_1d_drift) * 15.0) +
                (min(rr_ratio, 4.0) * 8.0) +
                (12.0 if item["Tech Signal"] == "STRONG BUY" else 5.0) +
                (score * 12.0) +
                (profit_pct * 2.0) +
                (8.0 if is_accum else 0.0) -
                (30.0 if is_trap else 0.0)  # Penalize exit distribution traps from Top 10
            )

            item["is_exit_trap"] = is_trap
            item["exit_trap_warning"] = exit_trap.get("warning_message", "")
            item["is_delivery_accumulation"] = is_accum
            item["Opening Bias"] = opening_bias
            item["Tactical Action"] = primary_action
            item["Quant Forecast"] = f"{bias_label} ({conviction:.0f}%)"
            item["Conviction %"] = conviction
            item["Expected 1D Drift %"] = exp_1d_drift
            item["Expected 5D Target"] = exp_5d_price
            item["Buy Entry"] = buy_entry
            item["Target 1 (Scalp)"] = target1
            item["Target 2 (Runner)"] = target2
            item["Stop Loss"] = stop_loss
            item["Risk : Reward"] = f"{rr_ratio}×"
            item["rr_numeric"] = rr_ratio
            item["Expected Session Range"] = f"H: ₹{day_high:,.1f} | L: ₹{day_low:,.1f}"
            item["Flip Time"] = flip_time
            item["Profit Potential %"] = profit_pct
            item["alpha_profit_score"] = round(alpha_score, 2)

        p_bar.progress(100, text=f"Scan & Forecast Complete! Found {len(valid_results)} candidates.")
        time.sleep(0.3)
        p_bar.empty()

        st.session_state.scan_valid = valid_results
        st.session_state.scan_rejected = rejected_results

    # ── Render Output ─────────────────────────────────────────────────────────
    results = st.session_state.get("scan_valid", [])
    rejected = st.session_state.get("scan_rejected", [])

    # Sort results by alpha score descending
    sorted_candidates = sorted(results, key=lambda x: x.get("alpha_profit_score", 0), reverse=True)
    top_10_stocks = sorted_candidates[:10]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Setups Discovered", len(results))
    k2.metric("Filtered Out (Rejected)", len(rejected))
    k3.metric("Top Alpha Candidates", len(top_10_stocks))
    k4.metric("Forecast & Blueprints", "Active (Live Confluence)")

    st.divider()

    # ── Master Tabs ───────────────────────────────────────────────────────────
    tab_top10, tab_valid, tab_rejected = st.tabs([
        f"🏆 Top 10 Stocks for Upcoming Session ({len(top_10_stocks)})",
        f"✅ All Scanned Candidates ({len(results)})",
        f"❌ Filtered Out Candidates ({len(rejected)})",
    ])

    total_cap = st.session_state.get("total_capital", 500_000.0)
    risk_pct = st.session_state.get("risk_pct", 0.01)

    # ── TAB 1: TOP 10 STOCKS FOR UPCOMING SESSION ─────────────────────────────
    with tab_top10:
        st.markdown("### 🏆 Top 10 High-Alpha Stocks for Upcoming Session")
        st.caption("Ranked for **Maximum Profit Potential** in the upcoming session by synthesizing directional conviction, expected 1-day drift, volatility expansion, risk-to-reward ratio, and catalyst tailwinds.")

        if not top_10_stocks:
            st.warning("No candidate setups discovered yet. Run a market scan above to generate the Top 10 setups.")
        else:
            # Filter controls for Top 10
            f_col1, f_col2 = st.columns([3, 1])
            with f_col1:
                t10_filter = st.radio(
                    "Filter Strategy",
                    options=["🌟 All Top 10 Opportunities", "🟢 Top Bullish Longs", "🔴 Top Bearish / Short Setups"],
                    horizontal=True,
                )
            with f_col2:
                card_view_mode = st.toggle("Show Executive Cards", value=True)

            filtered_top10 = top_10_stocks
            if "Bullish" in t10_filter:
                filtered_top10 = [s for s in top_10_stocks if "BUY" in s.get("Tactical Action", "").upper() or "RISE" in s.get("Opening Bias", "").upper()]
            elif "Bearish" in t10_filter:
                filtered_top10 = [s for s in top_10_stocks if "SELL" in s.get("Tactical Action", "").upper() or "FALL" in s.get("Opening Bias", "").upper()]

            if not filtered_top10:
                filtered_top10 = top_10_stocks

            # Leaderboard Table
            st.markdown("#### 📊 Top 10 Session Leaderboard")
            leaderboard_rows = []
            for rank_idx, s in enumerate(filtered_top10, start=1):
                leaderboard_rows.append({
                    "Rank": f"#{rank_idx}",
                    "Ticker": s["Ticker"],
                    "Sector": s["Sector"],
                    "Price": f"₹{s['Price']:,.2f}",
                    "Tactical Action": s.get("Tactical Action", "N/A"),
                    "Opening Direction": s.get("Opening Bias", "N/A"),
                    "1D Drift %": f"{s.get('Expected 1D Drift %', 0.0):+.2f}%",
                    "Optimal Entry": f"₹{s.get('Buy Entry', s['Price']):,.2f}",
                    "Target 1 (Scalp)": f"₹{s.get('Target 1 (Scalp)', s['Price']):,.2f}",
                    "Target 2 (Runner)": f"₹{s.get('Target 2 (Runner)', s['Price']):,.2f}",
                    "Stop Loss": f"₹{s.get('Stop Loss', s['Price']):,.2f}",
                    "Risk:Reward": s.get("Risk : Reward", "1.5×"),
                    "Profit Pot. %": f"+{s.get('Profit Potential %', 0.0):.1f}%",
                    "Conviction": f"{s.get('Conviction %', 50):.0f}%",
                    "Fused Consensus": s.get("Fused Consensus", "N/A"),
                })
            
            st.dataframe(pd.DataFrame(leaderboard_rows), use_container_width=True, hide_index=True)

            if card_view_mode:
                st.markdown("#### ⚡ Executive Opportunity Cards & Position Sizing")
                st.caption(f"Position sizes automatically calculated for **₹{total_cap:,.0f}** capital with **{risk_pct*100:.1f}%** risk per trade (₹{total_cap*risk_pct:,.0f} max loss).")

                for r_idx, stock in enumerate(filtered_top10, start=1):
                    tick = stock["Ticker"]
                    p = stock["Price"]
                    b_entry = stock.get("Buy Entry", p)
                    b_target1 = stock.get("Target 1 (Scalp)", p)
                    b_target2 = stock.get("Target 2 (Runner)", p)
                    b_stop = stock.get("Stop Loss", p)
                    act = stock.get("Tactical Action", "BUY ON PULLBACK")
                    bias = stock.get("Opening Bias", "🟢 EXPECTED TO RISE")
                    pot = stock.get("Profit Potential %", 0.0)
                    rr = stock.get("Risk : Reward", "2.0×")
                    flip = stock.get("Flip Time", "10:00 AM")
                    sec = stock["Sector"]
                    conv = stock.get("Conviction %", 50.0)

                    # Compute sizing
                    sizing = compute_position_size(total_cap, risk_pct, b_entry, b_stop)
                    sh = sizing.get("shares", 0)
                    pos_val = sizing.get("position_value", 0.0)
                    risk_val = sizing.get("cash_at_risk", 0.0)

                    rank_badge = f"#{r_idx} 🥇 TOP PICK" if r_idx == 1 else f"#{r_idx} 🥈 RUNNER-UP" if r_idx == 2 else f"#{r_idx} 🥉 TOP TIER" if r_idx == 3 else f"#{r_idx}"
                    rank_cls = "rank-gold" if r_idx <= 3 else ""

                    trap_pill = '<span class="tactical-badge" style="background:rgba(255,82,82,0.2);color:#FF5252;border:1px solid rgba(255,82,82,0.5);">🚨 EXIT TRAP RISK</span>' if stock.get("is_exit_trap") else ""
                    accum_pill = '<span class="tactical-badge" style="background:rgba(0,230,118,0.2);color:#00E676;border:1px solid rgba(0,230,118,0.5);">🛡️ FLOAT ABSORPTION</span>' if stock.get("is_delivery_accumulation") else ""

                    with st.container():
                        st.markdown(
                            f"""
                            <div class="top10-card">
                                <div class="top10-header">
                                    <div>
                                        <span class="top10-rank-pill {rank_cls}">{rank_badge}</span>
                                        <span class="top10-symbol">&nbsp;{esc(tick)}</span>
                                        <div class="top10-sector">{esc(sec)} · LTP: <strong>₹{p:,.2f}</strong></div>
                                    </div>
                                    <div style="text-align:right;">
                                        <div style="font-family:var(--mono);font-size:18px;font-weight:700;color:#3FB950;">
                                            +{pot:.1f}% Pot.
                                        </div>
                                        <div style="font-size:11px;color:var(--text-muted);font-family:var(--mono);">
                                            Conviction: {conv:.0f}% · R:R: {esc(rr)}
                                        </div>
                                    </div>
                                </div>
                                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px;">
                                    <span class="tactical-badge tactical-badge-action">⚡ {esc(act)}</span>
                                    <span class="tactical-badge tactical-badge-up">{esc(bias)}</span>
                                    {trap_pill}
                                    {accum_pill}
                                    <span style="font-size:11px;color:var(--amber);font-family:var(--mono);">Inflection @ {esc(flip)}</span>
                                </div>
                                <div class="top10-grid-levels">
                                    <div class="level-item">
                                        <span class="level-label">Optimal Entry</span>
                                        <span class="level-val val-buy">₹{b_entry:,.2f}</span>
                                    </div>
                                    <div class="level-item">
                                        <span class="level-label">Target 1 (Scalp)</span>
                                        <span class="level-val val-target">₹{b_target1:,.2f}</span>
                                    </div>
                                    <div class="level-item">
                                        <span class="level-label">Protective Stop</span>
                                        <span class="level-val val-stop">₹{b_stop:,.2f}</span>
                                    </div>
                                    <div class="level-item">
                                        <span class="level-label">Target 2 (Runner)</span>
                                        <span class="level-val val-profit">₹{b_target2:,.2f}</span>
                                    </div>
                                </div>
                                <div class="top10-sizing">
                                    <span>SUGGESTED ALLOCATION</span>
                                    <span><strong>{sh:,} shares</strong> · ₹{pos_val:,.0f} pos · ₹{risk_val:,.0f} at risk ({risk_pct*100:.1f}%)</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Action bar for this Top 10 stock
                        b_col1, b_col2, b_col3 = st.columns([2, 2, 3])
                        with b_col1:
                            if st.button(f"🔬 Forecast Lab: {tick}", key=f"btn_fc_{tick}", use_container_width=True):
                                st.session_state["bridged_forecast_ticker"] = tick
                                st.session_state["target_operating_mode"] = "Forecast & Correlation Lab"
                                st.toast(f"Switched to Forecast Lab for {tick}!", icon="🔬")
                                st.rerun()
                        with b_col2:
                            if st.button(f"⚡ Live Monitor: {tick}", key=f"btn_mon_{tick}", use_container_width=True):
                                st.session_state["bridged_monitor_ticker"] = tick
                                st.session_state["target_operating_mode"] = "Live Intraday Monitor"
                                st.toast(f"Bridged {tick} to Live Intraday Monitor!", icon="⚡")
                                st.rerun()
                        with b_col3:
                            with st.expander("📋 View Intraday Blueprint Details"):
                                bp_data = stock.get("blueprint", {})
                                if bp_data:
                                    phases = bp_data.get("intraday_phases", [])
                                    if phases:
                                        df_ph = pd.DataFrame([
                                            {"Phase": p["phase"], "Duration": p["bars"], "Expected Dynamics": p["expected_behavior"], "Target Zone": p["target_zone"]}
                                            for p in phases
                                        ])
                                        st.dataframe(df_ph, use_container_width=True, hide_index=True)
                                else:
                                    st.info("Blueprint details available.")

    # ── TAB 2: ALL SCANNED CANDIDATES ─────────────────────────────────────────
    with tab_valid:
        if not results:
            st.warning("No candidate setups matched the screener criteria in this scan run.")
        else:
            v_col1, v_col2 = st.columns([3, 2])
            with v_col1:
                table_view_mode = st.radio(
                    "Table View Columns",
                    options=["📊 Tactical & Forecast View", "📈 Technical & Execution View", "🧠 Vector News & Catalysts"],
                    horizontal=True,
                )
            with v_col2:
                st.write("")
                st.write(f"Total valid setups: **{len(results)}** stocks")

            df_out = pd.DataFrame(results)

            if table_view_mode.startswith("📊"):
                display_cols = [
                    "Ticker",
                    "Sector",
                    "Price",
                    "Tactical Action",
                    "Opening Bias",
                    "Quant Forecast",
                    "Expected 1D Drift %",
                    "Buy Entry",
                    "Target 1 (Scalp)",
                    "Stop Loss",
                    "Risk : Reward",
                    "Profit Potential %",
                    "Fused Consensus",
                ]
            elif table_view_mode.startswith("📈"):
                display_cols = [
                    "Ticker",
                    "Sector",
                    "Price",
                    "1D Change %",
                    "RSI",
                    "EMA Alignment",
                    "Volume Surge",
                    "Tech Signal",
                    "Buy Entry",
                    "Target 1 (Scalp)",
                    "Stop Loss",
                    "Risk : Reward",
                ]
            else:
                display_cols = [
                    "Ticker",
                    "Sector",
                    "Price",
                    "Tech Signal",
                    "Fused Consensus",
                    "Vector News Score",
                    "Catalyst Match",
                    "Latest Catalyst",
                ]

            if group_by_sector and "Sector" in df_out.columns:
                for sector, grp in df_out.groupby("Sector"):
                    st.markdown(f"#### 📂 Sector: {sector} ({len(grp)} setups)")
                    st.dataframe(
                        grp[[c for c in display_cols if c in grp.columns]],
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.dataframe(
                    df_out[[c for c in display_cols if c in df_out.columns]],
                    use_container_width=True,
                    hide_index=True,
                )

            st.divider()

            # ── Candidate Setup Deep-Dive Inspector ───────────────────────────
            st.markdown("### 🔍 Candidate Setup Deep-Dive Inspector")
            st.caption("Select any scanned candidate below to inspect its Executive Blueprint and Actionable Levels inline.")

            c_inspect_tick, c_inspect_btn1, c_inspect_btn2 = st.columns([3, 2, 2])
            with c_inspect_tick:
                chosen_candidate = st.selectbox("Select Candidate", options=[r["Ticker"] for r in results])
            with c_inspect_btn1:
                st.write("")
                st.write("")
                if st.button("🔬 Analyze in Forecast Lab ➡️", use_container_width=True):
                    st.session_state["bridged_forecast_ticker"] = chosen_candidate
                    st.session_state["target_operating_mode"] = "Forecast & Correlation Lab"
                    st.toast(f"Opening Forecast Lab for {chosen_candidate}...", icon="🔬")
                    st.rerun()
            with c_inspect_btn2:
                st.write("")
                st.write("")
                if st.button("⚡ Track in Live Monitor ➡️", use_container_width=True):
                    st.session_state["bridged_monitor_ticker"] = chosen_candidate
                    st.session_state["target_operating_mode"] = "Live Intraday Monitor"
                    st.toast(f"Bridged {chosen_candidate} to Live Monitor!", icon="⚡")
                    st.rerun()

            chosen_item = next((r for r in results if r["Ticker"] == chosen_candidate), None)
            if chosen_item:
                ib = chosen_item.get("blueprint", {})
                last_p = chosen_item["Price"]
                st_loss = chosen_item.get("Stop Loss", last_p)
                tk_prof = chosen_item.get("Target 1 (Scalp)", last_p)

                if ib:
                    render_tactical_executive_cards(last_price=last_p, ib=ib, stop_loss=st_loss, take_profit=tk_prof)
                    render_actionable_levels_bar(last_price=last_p, ib=ib, stop_loss=st_loss, take_profit=tk_prof)
                else:
                    st.info(f"Blueprint details for {chosen_candidate} can be fully computed in Forecast Lab.")

    # ── TAB 3: FILTERED OUT CANDIDATES ────────────────────────────────────────
    with tab_rejected:
        if not rejected:
            st.info("No candidates were filtered out.")
        else:
            st.caption("Inspect why stocks failed the technical screener criteria (EMA misalignment, weak liquidity, RSI out of bounds, etc.).")
            df_rej = pd.DataFrame(rejected)
            st.dataframe(df_rej, use_container_width=True, hide_index=True)
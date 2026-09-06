"""
Mode 1 — Pro Manual Trading Terminal (Kite & Groww Grade)
=========================================================
Institutional-grade manual trading station featuring:
  - Interactive multi-timeframe charting (5m, 15m, 1h, 1d, 1w)
  - Zerodha Kite & Groww style Market Stats (Today's Range, 52W Range, Circuit Limits, VWAP)
  - Technical Overlays (Supertrend, VWAP, Bollinger Bands, EMAs, Floor & Camarilla Pivots)
  - Interactive Pro Order Pad with automatic 1% risk position sizing
  - Indian regulatory tax & friction calculator (STT, GST, Brokerage)
  - 1-Click Paper Simulation Execution & Zerodha GTT order formatting
  - Live Ticker Positions table with 1-click square-off
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import textwrap
from typing import Optional

from utils.data import (
    analyse_ticker,
    fetch_timeframe_history,
    fetch_ticker_info,
    fetch_daily_history
)
from utils.charts import make_advanced_manual_trading_chart
from utils import indicators as ti
from utils.tax_calculator import compute_indian_market_friction
from utils.gtt import compute_gtt_order_parameters
from utils.market_store import log_paper_trade, get_all_paper_trades, close_paper_trade
from utils.user_prefs import get_current_user_id, get_user_preferences


POPULAR_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "TATAMOTORS.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS",
    "ZOMATO.NS", "BHARTIARTL.NS"
]


def render_mode1() -> None:
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-header" style="margin-bottom: 12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h1 style="margin:0; font-size: 24px; font-weight: 800; color: #E6EDF3;">
                        ⚡ Pro Manual Trading Terminal
                    </h1>
                    <p style="margin:4px 0 0 0; color: #8B949E; font-size: 13px;">
                        Dalal Street live depth, multi-timeframe institutional charts & risk-managed execution.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Top Bar: Ticker Selection & Quick Chips ──────────────────────────────
    active_user = get_current_user_id()
    prefs = get_user_preferences(active_user)
    user_capital = float(prefs.get("total_capital", prefs.get("capital_budget", 200000.0)))

    col_input, col_chips = st.columns([1.2, 2.8])

    default_ticker = st.session_state.get("mode1_active_ticker", "RELIANCE.NS")
    if st.session_state.get("bridged_tickers"):
        default_ticker = st.session_state["bridged_tickers"][0]

    with col_input:
        selected_ticker = st.text_input(
            "Enter Stock Ticker",
            value=default_ticker,
            placeholder="e.g. RELIANCE.NS, TCS.NS, AAPL",
            label_visibility="collapsed",
            key="mode1_ticker_input"
        ).strip().upper()

    with col_chips:
        st.markdown("<div style='font-size: 11px; color: #8B949E; margin-bottom: 2px;'>Quick Access:</div>", unsafe_allow_html=True)
        chip_cols = st.columns(len(POPULAR_TICKERS))
        for idx, chip in enumerate(POPULAR_TICKERS):
            with chip_cols[idx]:
                clean_name = chip.replace(".NS", "")
                if st.button(clean_name, key=f"chip_{chip}", use_container_width=True):
                    selected_ticker = chip
                    st.session_state["mode1_active_ticker"] = chip
                    st.rerun()

    if not selected_ticker:
        st.info("💡 Enter a ticker symbol above or click a quick-access stock.")
        return

    st.session_state["mode1_active_ticker"] = selected_ticker

    # ── Fetch Full Data ───────────────────────────────────────────────────────
    with st.spinner(f"Loading live depth & institutional data for {selected_ticker}…"):
        data = analyse_ticker(selected_ticker)

    if not data or data.get("current_price") is None:
        st.error(f"❌ Unable to load market data for **{selected_ticker}**. Please verify the symbol.")
        return

    current_price = float(data.get("current_price", 0.0))
    day_chg = float(data.get("day_change_pct", 0.0))
    name = data.get("name", selected_ticker)
    sector = data.get("sector", "Equities")
    industry = data.get("industry", "")
    info = data.get("info", {}) or {}

    # Extract high-resolution market statistics
    day_open = float(info.get("regularMarketOpen") or info.get("open") or current_price)
    prev_close = float(info.get("regularMarketPreviousClose") or info.get("previousClose") or current_price)
    day_high = float(info.get("regularMarketDayHigh") or info.get("dayHigh") or current_price * 1.01)
    day_low = float(info.get("regularMarketDayLow") or info.get("dayLow") or current_price * 0.99)
    w52_high = float(info.get("fiftyTwoWeekHigh") or current_price * 1.2)
    w52_low = float(info.get("fiftyTwoWeekLow") or current_price * 0.8)
    day_vol = float(info.get("regularMarketVolume") or info.get("volume") or data.get("avg_vol_10d", 0.0))
    mkt_cap = float(data.get("market_cap") or info.get("marketCap") or 0.0)
    pe_ratio = float(data.get("pe_ratio") or info.get("trailingPE") or 0.0)
    beta = float(data.get("beta") or info.get("beta") or 1.0)

    # Compute circuit limits & pivots
    circuits = ti.circuit_limits(prev_close, 10.0)
    daily_df = data.get("daily_df", pd.DataFrame())
    pivots = ti.pivot_points(daily_df)

    # Day price change in INR
    chg_inr = round(current_price - prev_close, 2)
    chg_color = "#3FB950" if chg_inr >= 0 else "#F85149"
    chg_sign = "+" if chg_inr >= 0 else ""

    # ── 1. Dalal Street Pro Quote Header (Zerodha / Groww Style) ──────────────
    ind_str = f" • {industry}" if industry else ""
    today_pct = max(2, min(98, int((current_price - day_low) / max(0.01, day_high - day_low) * 100)))
    w52_pct = max(2, min(98, int((current_price - w52_low) / max(0.01, w52_high - w52_low) * 100)))

    quote_card_html = (
        f'<div style="background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap: 14px;">'
        f'<div>'
        f'<div style="display:flex; align-items:center; gap: 8px;">'
        f'<span style="font-size: 20px; font-weight: 800; color: #E6EDF3;">{selected_ticker}</span>'
        f'<span style="background: #21262D; color: #58A6FF; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">NSE / BSE</span>'
        f'<span style="background: rgba(188, 140, 255, 0.15); color: #BC8CFF; font-size: 11px; padding: 2px 6px; border-radius: 4px;">{sector}</span>'
        f'</div>'
        f'<div style="color: #8B949E; font-size: 12px; margin-top: 2px;">{name}{ind_str}</div>'
        f'<div style="display:flex; align-items:baseline; gap: 10px; margin-top: 6px;">'
        f'<span style="font-size: 28px; font-weight: 800; color: {chg_color}; font-family: monospace;">₹{current_price:,.2f}</span>'
        f'<span style="font-size: 14px; font-weight: 700; color: {chg_color};">{chg_sign}₹{abs(chg_inr):.2f} ({chg_sign}{day_chg:.2f}%)</span>'
        f'</div>'
        f'</div>'
        f'<div style="flex: 1; min-width: 280px; max-width: 440px;">'
        f'<div style="margin-bottom: 8px;">'
        f'<div style="display:flex; justify-content:space-between; font-size: 11px; color: #8B949E; margin-bottom: 2px;">'
        f'<span>Today\'s Low: <b>₹{day_low:,.2f}</b></span><span style="color:#E6EDF3; font-weight:600;">Today\'s Range</span><span>High: <b>₹{day_high:,.2f}</b></span>'
        f'</div>'
        f'<div style="background: #21262D; height: 7px; border-radius: 4px; position: relative; overflow: hidden;">'
        f'<div style="background: linear-gradient(90deg, #F85149, #D29922, #3FB950); width: 100%; height: 100%; opacity: 0.3;"></div>'
        f'<div style="position: absolute; top:0; bottom:0; left: {today_pct}%; width: 4px; background: #FFFFFF; border-radius: 2px;"></div>'
        f'</div>'
        f'</div>'
        f'<div>'
        f'<div style="display:flex; justify-content:space-between; font-size: 11px; color: #8B949E; margin-bottom: 2px;">'
        f'<span>52W Low: <b>₹{w52_low:,.2f}</b></span><span style="color:#E6EDF3; font-weight:600;">52-Week Range</span><span>52W High: <b>₹{w52_high:,.2f}</b></span>'
        f'</div>'
        f'<div style="background: #21262D; height: 7px; border-radius: 4px; position: relative; overflow: hidden;">'
        f'<div style="background: linear-gradient(90deg, #38BDF8, #A855F7); width: 100%; height: 100%; opacity: 0.35;"></div>'
        f'<div style="position: absolute; top:0; bottom:0; left: {w52_pct}%; width: 4px; background: #38BDF8; border-radius: 2px;"></div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(quote_card_html, unsafe_allow_html=True)

    # ── 2. Market Depth & Stats Grid ──────────────────────────────────────────
    st_c1, st_c2, st_c3, st_c4, st_c5, st_c6 = st.columns(6)
    with st_c1:
        st.metric("Open", f"₹{day_open:,.2f}")
    with st_c2:
        st.metric("Prev Close", f"₹{prev_close:,.2f}")
    with st_c3:
        st.metric("Volume (Shares)", f"{day_vol:,.0f}")
    with st_c4:
        vwap_est = round((day_high + day_low + current_price) / 3.0, 2)
        st.metric("Est. VWAP", f"₹{vwap_est:,.2f}")
    with st_c5:
        st.metric("Upper Circuit (10%)", f"₹{circuits['upper']:,.2f}")
    with st_c6:
        st.metric("Lower Circuit (10%)", f"₹{circuits['lower']:,.2f}")

    # ── 3. Pivot Points & Key Institutional Reference Levels ───────────────────
    if pivots:
        with st.expander("📍 Floor & Camarilla Pivot Levels (Support & Resistance Targets)", expanded=False):
            p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns(5)
            with p_c1:
                st.markdown(f"**S2:** `₹{pivots.get('s2', 0):,.2f}`")
                st.caption(f"Cam S4: ₹{pivots.get('cam_s4', 0):,.2f}")
            with p_c2:
                st.markdown(f"**S1:** `₹{pivots.get('s1', 0):,.2f}`")
                st.caption(f"Cam S3: ₹{pivots.get('cam_s3', 0):,.2f}")
            with p_c3:
                st.markdown(f"**Central Pivot (P):** `₹{pivots.get('pivot', 0):,.2f}`")
                st.caption("Daily Balance Line")
            with p_c4:
                st.markdown(f"**R1:** `₹{pivots.get('r1', 0):,.2f}`")
                st.caption(f"Cam R3: ₹{pivots.get('cam_r3', 0):,.2f}")
            with p_c5:
                st.markdown(f"**R2:** `₹{pivots.get('r2', 0):,.2f}`")
                st.caption(f"Cam R4: ₹{pivots.get('cam_r4', 0):,.2f}")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # ── 4. Main Two-Column Layout: Pro Chart (Left) + Order Pad (Right) ───────
    chart_col, order_col = st.columns([2.1, 1.1], gap="medium")

    with chart_col:
        # Timeframe & Indicator Controls
        tf_row, ind_row = st.columns([1.1, 2.2])

        with tf_row:
            timeframe = st.segmented_control(
                "Timeframe",
                options=["5m", "15m", "1h", "1D", "1W"],
                default="1D",
                key="chart_tf_selector"
            ) or "1D"

        with ind_row:
            ind_c1, ind_c2, ind_c3, ind_c4 = st.columns(4)
            with ind_c1:
                show_vwap = st.checkbox("VWAP", value=True, key="cb_vwap")
            with ind_c2:
                show_ema = st.checkbox("EMA 9/21", value=True, key="cb_ema")
            with ind_c3:
                show_supertrend = st.checkbox("Supertrend", value=False, key="cb_st")
            with ind_c4:
                show_bollinger = st.checkbox("Bollinger", value=False, key="cb_bb")

        # Fetch timeframe-specific data
        chart_df = fetch_timeframe_history(selected_ticker, timeframe=timeframe)
        if chart_df.empty:
            chart_df = daily_df

        # Render Pro Chart
        pro_fig = make_advanced_manual_trading_chart(
            df=chart_df,
            ticker=selected_ticker,
            timeframe=timeframe,
            show_ema9=show_ema,
            show_ema21=show_ema,
            show_ema50=False,
            show_ema200=False,
            show_vwap=show_vwap,
            show_supertrend=show_supertrend,
            show_bollinger=show_bollinger,
            show_pivots=True,
            pivots_dict=pivots,
            show_rsi=True,
            show_macd=False,
        )
        st.plotly_chart(
            pro_fig,
            use_container_width=True,
            config={"displayModeBar": True, "scrollZoom": True},
            key=f"pro_chart_{selected_ticker}_{timeframe}"
        )

        # AI Quant Shield / Regime Check (The "Brain")
        plan_a = data.get("plan_a", {}) or {}
        plan_b = data.get("plan_b", {}) or {}
        conviction = data.get("conviction", {}) or {}

        with st.expander("🧠 Institutional AI Guidance & Regime Radar", expanded=True):
            r_c1, r_c2, r_c3 = st.columns(3)
            with r_c1:
                trend_data = data.get("trend", {})
                t_label = trend_data.get("label", "Neutral")
                st.markdown(f"**Market Regime:** `{t_label}`")
                st.caption(trend_data.get("description", "Normal trading conditions"))
            with r_c2:
                conv_score = conviction.get("composite_score") or conviction.get("score") or 50
                st.markdown(f"**AI Conviction Score:** `{conv_score}/100`")
                st.caption(conviction.get("verdict", "Neutral"))
            with r_c3:
                atr_val = float(data.get("atr_14", current_price * 0.015))
                st.markdown(f"**14-Period ATR Volatility:** `₹{atr_val:.2f}`")
                st.caption("Recommended dynamic stop buffer")

    # ── 5. Pro Order Pad & Execution Terminal (Right Column) ──────────────────
    with order_col:
        st.markdown(
            """
            <div style="background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 700; font-size: 15px; color: #E6EDF3; display:flex; justify-content:space-between; align-items:center;">
                    <span>📝 Pro Order Pad</span>
                    <span style="font-size: 11px; background: rgba(56, 189, 248, 0.15); color: #38BDF8; padding: 2px 6px; border-radius: 4px;">Kite / Groww Ready</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Side Selection (BUY / SELL)
        order_side = st.radio(
            "Transaction Type",
            options=["BUY (LONG)", "SELL (SHORT)"],
            horizontal=True,
            label_visibility="collapsed"
        )
        is_buy = "BUY" in order_side

        # Product Type (MIS vs CNC)
        prod_col1, prod_col2 = st.columns(2)
        with prod_col1:
            product_type = st.selectbox(
                "Product",
                options=["CNC (Delivery / Swing)", "MIS (Intraday - 5x)"],
                index=0
            )
        with prod_col2:
            order_type = st.selectbox(
                "Order Type",
                options=["LIMIT", "MARKET", "SL-LIMIT", "GTT OCO"],
                index=0
            )

        is_intraday = "MIS" in product_type

        # Pre-calculated Suggested Entries & Stops from Plan A / Plan B
        plan = plan_a if is_intraday else plan_b
        suggested_entry = round(float(plan.get("entry", current_price)), 2)
        suggested_target = round(float(plan.get("target", current_price * 1.04)), 2)
        suggested_stop = round(float(plan.get("stop", current_price * 0.98)), 2)

        # Price Inputs
        p_in1, p_in2 = st.columns(2)
        with p_in1:
            entry_price_input = st.number_input(
                "Entry Price (₹)",
                value=suggested_entry if order_type != "MARKET" else current_price,
                min_value=0.05,
                step=0.5,
                format="%.2f"
            )
        with p_in2:
            stop_loss_input = st.number_input(
                "Stop Loss (₹)",
                value=suggested_stop,
                min_value=0.05,
                step=0.5,
                format="%.2f"
            )

        target_input = st.number_input(
            "Target Exit (₹)",
            value=suggested_target,
            min_value=0.05,
            step=0.5,
            format="%.2f"
        )

        # Quantity & Smart 1% Risk Sizer
        risk_per_share = abs(entry_price_input - stop_loss_input)
        max_risk_amount = user_capital * 0.01  # 1% Rule
        auto_shares = max(1, int(max_risk_amount / max(0.1, risk_per_share)))

        q_col1, q_col2 = st.columns([1.8, 1.2])
        with q_col1:
            shares_input = st.number_input(
                "Quantity (Shares)",
                min_value=1,
                max_value=100000,
                value=min(auto_shares, 500),
                step=1
            )
        with q_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🎯 1% Risk", help=f"Auto-sizes shares so max loss is ₹{max_risk_amount:,.0f} (1% of your ₹{user_capital:,.0f} capital)", use_container_width=True):
                shares_input = auto_shares
                st.rerun()

        # ── Live Financial & Friction Calculations ────────────────────────────
        margin_required = (entry_price_input * shares_input) / (5.0 if is_intraday else 1.0)
        potential_loss = round(risk_per_share * shares_input, 2)
        potential_gain = round(abs(target_input - entry_price_input) * shares_input, 2)
        rr_ratio = round(potential_gain / max(1.0, potential_loss), 2)

        friction = compute_indian_market_friction(
            entry_price=entry_price_input,
            exit_price=target_input,
            shares=shares_input,
            is_intraday=is_intraday
        )
        taxes_and_brokerage = friction.get("total_friction", 0.0)
        net_profit_takehome = friction.get("net_profit", 0.0)

        st.markdown(
            f"""
            <div style="background: #0D1117; border: 1px solid #21262D; border-radius: 6px; padding: 10px 12px; margin: 10px 0; font-size: 12px;">
                <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                    <span style="color:#8B949E;">Margin Required:</span>
                    <span style="color:#E6EDF3; font-weight:600;">₹{margin_required:,.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                    <span style="color:#8B949E;">Risk at Stop Loss:</span>
                    <span style="color:#F85149; font-weight:600;">-₹{potential_loss:,.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                    <span style="color:#8B949E;">Target Reward:</span>
                    <span style="color:#3FB950; font-weight:600;">+₹{potential_gain:,.2f} (R:R 1:{rr_ratio})</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                    <span style="color:#8B949E;">Est. Indian Taxes & Fees:</span>
                    <span style="color:#D29922;">₹{taxes_and_brokerage:,.2f}</span>
                </div>
                <div style="border-top: 1px solid #21262D; margin-top: 4px; padding-top: 4px; display:flex; justify-content:space-between;">
                    <span style="color:#8B949E;">Est. Net Profit:</span>
                    <span style="color:#3FB950; font-weight:700;">₹{net_profit_takehome:,.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ── Execution Buttons ─────────────────────────────────────────────────
        exec_sim_btn = st.button(
            f"🚀 Execute Paper {order_side.split()[0]} ({shares_input} Shares)",
            type="primary",
            use_container_width=True
        )

        if exec_sim_btn:
            horizon = "DAY_TRADE" if is_intraday else "SWING"
            trade_action = "BUY" if is_buy else "SHORT"
            tid = log_paper_trade(
                ticker=selected_ticker,
                trade_type=trade_action,
                entry_price=entry_price_input,
                target_price=target_input,
                stop_loss_price=stop_loss_input,
                shares=shares_input,
                notes=f"Manual execution from Pro Order Pad ({product_type})",
                is_auto_trade=0,
                execution_mode="SIMULATION",
                horizon=horizon,
                user_id=active_user
            )
            st.success(f"✅ Trade #{tid} successfully logged to your private journal ({active_user.title()})!")
            st.rerun()

        # Broker GTT Copy Box
        with st.expander("📋 Copy Zerodha Kite GTT / Upstox Order", expanded=False):
            gtt_params = compute_gtt_order_parameters(
                ticker=selected_ticker,
                current_price=current_price,
                entry_price=entry_price_input,
                stop_loss=stop_loss_input,
                target1=target_input,
                shares=shares_input,
                is_intraday=is_intraday
            )
            st.markdown("**Zerodha Kite / Groww GTT Values:**")
            st.code(
                f"Trigger Price : ₹{gtt_params.get('buy_trigger', entry_price_input):,.2f}\n"
                f"Limit Price   : ₹{entry_price_input:,.2f}\n"
                f"Stop Trigger  : ₹{gtt_params.get('sl_trigger', stop_loss_input):,.2f}\n"
                f"Target Trigger: ₹{gtt_params.get('tgt1_trigger', target_input):,.2f}\n"
                f"Quantity      : {shares_input}",
                language="text"
            )

    # ── 6. Active Ticker Positions Table ──────────────────────────────────────
    st.divider()
    st.markdown(f"### 📊 Open Positions for {selected_ticker} (`{active_user.title()}`)")

    all_trades = get_all_paper_trades(user_id=active_user)
    open_trades_this_ticker = [
        t for t in all_trades
        if t.get("ticker") == selected_ticker and str(t.get("status", "")).upper() == "OPEN"
    ]

    if not open_trades_this_ticker:
        st.caption(f"No active positions in {selected_ticker} for {active_user.title()}. Use the order pad above to log a trade.")
    else:
        for trade in open_trades_this_ticker:
            t_id = trade["id"]
            t_side = trade["trade_type"]
            t_shares = trade["shares"]
            t_entry = float(trade["entry_price"])
            t_target = float(trade["target_price"])
            t_stop = float(trade["stop_loss_price"])

            if "SHORT" in t_side:
                cur_pnl = (t_entry - current_price) * t_shares
                cur_pnl_pct = ((t_entry - current_price) / max(0.01, t_entry)) * 100.0
            else:
                cur_pnl = (current_price - t_entry) * t_shares
                cur_pnl_pct = ((current_price - t_entry) / max(0.01, t_entry)) * 100.0

            pnl_c = "#3FB950" if cur_pnl >= 0 else "#F85149"
            pnl_s = "+" if cur_pnl >= 0 else ""

            pos_c1, pos_c2, pos_c3, pos_c4, pos_c5, pos_c6 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5, 1.2])
            with pos_c1:
                st.markdown(f"**Trade #{t_id}**")
                st.caption(f"{t_side} • {t_shares} shares")
            with pos_c2:
                st.markdown(f"**Entry:** ₹{t_entry:,.2f}")
                st.caption(f"Now: ₹{current_price:,.2f}")
            with pos_c3:
                st.markdown(f"**Target:** ₹{t_target:,.2f}")
                st.caption(f"Stop: ₹{t_stop:,.2f}")
            with pos_c4:
                st.markdown(f"<span style='color:{pnl_c}; font-weight:700;'>{pnl_s}₹{cur_pnl:,.2f}</span>", unsafe_allow_html=True)
                st.caption(f"{pnl_s}{cur_pnl_pct:.2f}%")
            with pos_c5:
                st.caption(f"Opened: {trade.get('timestamp', '—')}")
            with pos_c6:
                if st.button("Square Off", key=f"sq_off_{t_id}", type="secondary", use_container_width=True):
                    close_paper_trade(t_id, exit_price=current_price, reason="MANUAL_SQUARE_OFF")
                    st.success(f"Position #{t_id} squared off at ₹{current_price:,.2f}!")
                    st.rerun()

    st.caption("⚠️ FinVision is an institutional research and simulation terminal. All live trading decisions are your own responsibility.")

"""
finvision/app_pages/mode0_copilot.py
====================================
Smart Trade & Wealth Copilot (0-Knowledge Autopilot & Mentor).
Empowers anyone to generate profits in both fast-paced Day Trading
and Long-Term Wealth Compounding with plain-English guidance,
ELI5 rationale, budget-based position sizing, and 1-click paper trading.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from utils.forecasting import (
    compute_quantitative_confluence_forecast,
    compute_intraday_trade_blueprint,
)
from utils.fundamental_wealth import (
    analyze_stock_fundamentals,
    BLUE_CHIP_COMPOUNDERS,
)
from utils.risk import compute_position_size
from utils.market_store import log_paper_trade
from utils.components import render_eli5_box, esc


RECOMMENDED_DAY_TICKERS = [
    "RELIANCE.NS", "TATAMOTORS.NS", "INFY.NS", "TCS.NS",
    "HDFCBANK.NS", "ICICIBANK.NS", "BAJFINANCE.NS", "TITAN.NS"
]


def render_mode0():
    # ── Hero Banner ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="copilot-hero-card">
            <div class="copilot-hero-title">🤖 FinVision Smart Trade & Wealth Copilot</div>
            <div class="copilot-hero-subtitle">
                Zero-Knowledge AI Mentor & Execution Autopilot. Whether you want <strong>quick intraday profits</strong>
                or <strong>multi-year wealth compounding</strong>, the Copilot guides your every step with exact price levels,
                budget-based position sizing, and plain-English ELI5 explanations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Persona & Track Selector ──────────────────────────────────────────────
    c_track, c_budget, c_risk = st.columns([3, 2, 2])
    with c_track:
        track_choice = st.radio(
            "🎯 Select Your Trading / Investing Goal",
            options=[
                "⚡ Quick Profits & Day Trading (Intraday Scalps: Minutes to 1 Day)",
                "🌱 Multi-Year Wealth Compounding (Long-Term Stocks: 1 to 5 Years)",
            ],
            index=0,
        )
    with c_budget:
        user_budget = st.number_input(
            "💰 Your Trading Budget (₹)",
            min_value=1_000.0,
            max_value=10_000_000.0,
            value=st.session_state.get("total_capital", 50_000.0),
            step=5_000.0,
            help="The amount of capital you want to allocate for these setups.",
        )
        st.session_state["total_capital"] = user_budget

    with c_risk:
        risk_profile = st.selectbox(
            "🛡️ Risk Appetite",
            options=["Conservative (0.5% max risk)", "Balanced (1.0% max risk)", "Active (2.0% max risk)"],
            index=1,
            help="Strict mathematical stop-loss cap on capital per trade.",
        )
        risk_pct = 0.005 if "Conservative" in risk_profile else 0.02 if "Active" in risk_profile else 0.01
        st.session_state["risk_pct"] = risk_pct

    st.divider()

    # ── Custom Stock Lookup ──────────────────────────────────────────────────
    st.markdown("#### 🔍 Check Any Custom Stock")
    c_in, c_act = st.columns([4, 1])
    with c_in:
        custom_input = st.text_input(
            "Enter Stock Symbol (e.g. TATASTEEL, ZOMATO, SBIN, ITC, HAL, AAPL)",
            key="copilot_custom_ticker",
            placeholder="Type any symbol (e.g. ZOMATO, TATASTEEL, SBIN, HAL)...",
            label_visibility="collapsed"
        ).strip().upper()
    with c_act:
        check_btn = st.button("🔎 Analyze", use_container_width=True)

    active_custom_ticker = None
    if custom_input:
        t_clean = custom_input
        if not (t_clean.endswith(".NS") or t_clean.endswith(".BO") or "=" in t_clean or "^" in t_clean):
            t_clean = f"{t_clean}.NS"
        active_custom_ticker = t_clean
        st.success(f"🎯 Copilot is analyzing custom stock: **{active_custom_ticker}**")

    # ── ⚡ TRACK 1: DAY TRADING & QUICK PROFITS ────────────────────────────────
    if track_choice.startswith("⚡"):
        st.markdown("### ⚡ Today's AI Master Day Trading Setups")
        st.caption(f"Mathematically sized for a **₹{user_budget:,.0f}** account with **₹{user_budget*risk_pct:,.0f}** maximum risk protection.")

        day_tickers_to_scan = list(RECOMMENDED_DAY_TICKERS)
        if active_custom_ticker:
            day_tickers_to_scan = [active_custom_ticker] + [t for t in RECOMMENDED_DAY_TICKERS if t != active_custom_ticker]

        # Download sample universe for today's top picks
        with st.spinner("🤖 Copilot is scanning market order flow, volatility bands & news catalysts..."):
            try:
                bulk_df = yf.download(day_tickers_to_scan, period="3mo", interval="1d", group_by="ticker", progress=False)
            except Exception:
                bulk_df = None

        setups = []
        for tick in day_tickers_to_scan:
            try:
                if bulk_df is not None and tick in bulk_df:
                    df_t = bulk_df[tick].dropna(how="all")
                else:
                    df_t = yf.download(tick, period="3mo", interval="1d", progress=False)

                if isinstance(df_t.columns, pd.MultiIndex):
                    df_t.columns = [c[0] for c in df_t.columns]

                if df_t.empty or len(df_t) < 20:
                    continue

                bp = compute_intraday_trade_blueprint(df_t)
                fc = compute_quantitative_confluence_forecast(df_t)
                last_p = float(df_t["Close"].iloc[-1])

                b_entry = bp.get("buy_entry", last_p)
                t1 = bp.get("sell_target_1", last_p * 1.015)
                t2 = bp.get("sell_target_2", last_p * 1.03)
                sl = bp.get("stop_loss", last_p * 0.985)
                act = bp.get("primary_action", "BUY ON PULLBACK")
                bias = bp.get("opening_bias", "🟢 EXPECTED TO RISE")
                flip = bp.get("flip_time_est", "10:00 AM")
                conv = fc.get("conviction_pct", 65.0)

                # Profit % and Risk:Reward
                profit_pct = round(((t1 - b_entry) / max(0.01, b_entry)) * 100.0, 2)
                risk_dist = max(0.01, abs(b_entry - sl))
                reward_dist = abs(t1 - b_entry)
                rr = round(reward_dist / risk_dist, 2)

                sizing = compute_position_size(user_budget, risk_pct, b_entry, sl)

                setups.append({
                    "ticker": tick,
                    "price": last_p,
                    "entry": b_entry,
                    "target1": t1,
                    "target2": t2,
                    "stop_loss": sl,
                    "action": act,
                    "bias": bias,
                    "flip_time": flip,
                    "conviction": conv,
                    "profit_pct": profit_pct,
                    "rr_ratio": rr,
                    "shares": sizing.get("shares", 0),
                    "pos_val": sizing.get("position_value", 0.0),
                    "risk_val": sizing.get("cash_at_risk", 0.0),
                })
            except Exception:
                continue

        # Sort setups by conviction
        sorted_setups = sorted(setups, key=lambda x: x["conviction"], reverse=True)[:3]

        if not sorted_setups:
            st.info("Market data is refreshing. Click below to analyze setups.")
        else:
            for s_idx, s in enumerate(sorted_setups, start=1):
                tick = s["ticker"]
                est_profit_inr = round(s["shares"] * (s["target1"] - s["entry"]), 0)

                with st.container():
                    st.markdown(
                        f"""
                        <div class="top10-card" style="border-left: 4px solid #58A6FF;margin-bottom:18px;">
                            <div class="top10-header">
                                <div>
                                    <span class="top10-rank-pill">🎯 SETUP #{s_idx}</span>
                                    <span class="top10-symbol">&nbsp;{esc(tick)}</span>
                                    <div class="top10-sector">Reference Price: <strong>₹{s['price']:,.2f}</strong></div>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-family:var(--mono);font-size:18px;font-weight:700;color:#3FB950;">
                                        +₹{est_profit_inr:,.0f} Expected Gain
                                    </div>
                                    <div style="font-size:11px;color:var(--text-muted);font-family:var(--mono);">
                                        Target: +{s['profit_pct']:.1f}% · R:R: {s['rr_ratio']}×
                                    </div>
                                </div>
                            </div>
                            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
                                <span class="tactical-badge tactical-badge-action">⚡ {esc(s['action'])}</span>
                                <span class="tactical-badge tactical-badge-up">{esc(s['bias'])}</span>
                                <span style="font-size:11px;color:var(--amber);font-family:var(--mono);">Expected Inflection @ {esc(s['flip_time'])}</span>
                            </div>
                            <div class="top10-grid-levels">
                                <div class="level-item">
                                    <span class="level-label">1. Place Buy Limit</span>
                                    <span class="level-val val-buy">₹{s['entry']:,.2f}</span>
                                </div>
                                <div class="level-item">
                                    <span class="level-label">2. Take Profit (Scalp)</span>
                                    <span class="level-val val-target">₹{s['target1']:,.2f}</span>
                                </div>
                                <div class="level-item">
                                    <span class="level-label">3. Emergency Stop Loss</span>
                                    <span class="level-val val-stop">₹{s['stop_loss']:,.2f}</span>
                                </div>
                                <div class="level-item">
                                    <span class="level-label">4. Runner Target</span>
                                    <span class="level-val val-profit">₹{s['target2']:,.2f}</span>
                                </div>
                            </div>
                            <div class="top10-sizing">
                                <span>EXACT SIZED ORDER</span>
                                <span>Buy <strong>{s['shares']:,} shares</strong> (₹{s['pos_val']:,.0f} value) · Max Loss strictly capped at ₹{s['risk_val']:,.0f}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Interactive actions & ELI5
                    col_act1, col_act2, col_act3 = st.columns([2, 2, 3])
                    with col_act1:
                        if st.button(f"📓 Paper Trade: {tick}", key=f"btn_pt_{tick}_{s_idx}", use_container_width=True):
                            trade_id = log_paper_trade(
                                ticker=tick,
                                trade_type="BUY_INTRADAY",
                                entry_price=s["entry"],
                                target_price=s["target1"],
                                stop_loss_price=s["stop_loss"],
                                shares=s["shares"],
                                notes=f"Copilot Setup #{s_idx}: {s['action']}",
                            )
                            st.toast(f"✅ Paper Trade #{trade_id} logged for {tick} ({s['shares']} shares)!", icon="📓")
                    with col_act2:
                        if st.button(f"🔬 Forecast Lab: {tick}", key=f"btn_fc_cop_{tick}_{s_idx}", use_container_width=True):
                            st.session_state["bridged_forecast_ticker"] = tick
                            st.session_state["target_operating_mode"] = "Forecast & Correlation Lab"
                            st.rerun()
                    with col_act3:
                        with st.expander("🧠 Explain This Trade Like I'm 5 (ELI5)"):
                            render_eli5_box(
                                title=f"How to safely trade {tick} today",
                                explanation=(
                                    f"1. Why buy here: Price is sitting near strong institutional support at ₹{s['entry']:,.2f}. "
                                    f"Big buyers usually defend this price.\n"
                                    f"2. Your exit plan: As soon as price rises to ₹{s['target1']:,.2f}, sell your shares and lock in your profit of +₹{est_profit_inr:,.0f}.\n"
                                    f"3. Your safety net: If the market drops unexpectedly, your stop loss triggers at ₹{s['stop_loss']:,.2f}. "
                                    f"You only lose ₹{s['risk_val']:,.0f} (which is just {risk_pct*100:.1f}% of your budget)."
                                ),
                                key_rules=[
                                    "Never trade without entering the stop loss in your broker app (Zerodha/Groww).",
                                    "Lock profits at Target 1 and do not get greedy if market turns choppy.",
                                    f"Watch for the 10:00 AM inflection window ({s['flip_time']}).",
                                ]
                            )

    # ── 🌱 TRACK 2: LONG-TERM WEALTH COMPOUNDING ──────────────────────────────
    else:
        st.markdown("### 🌱 AI Long-Term Wealth Multiplier (Multi-Year Compounding)")
        st.caption("Invest in wide-moat, high-ROE compounders that generate continuous dividend growth and multi-year capital appreciation.")

        # Analyze top blue-chip compounders
        compounders = []
        top_picks = ["RELIANCE.NS", "TCS.NS", "TITAN.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]
        if active_custom_ticker:
            top_picks = [active_custom_ticker] + [t for t in top_picks if t != active_custom_ticker]
        
        with st.spinner(f"🤖 Copilot is analyzing balance sheet debt, ROE profitability & Moat resilience for {len(top_picks)} stocks..."):
            for tick in top_picks:
                try:
                    f_data = analyze_stock_fundamentals(tick)
                    if f_data.get("current_price", 0) > 0:
                        compounders.append(f_data)
                except Exception:
                    continue

        if not compounders:
            st.info("Loading fundamental data...")
        else:
            for c_idx, c_stock in enumerate(compounders, start=1):
                tick = c_stock["ticker"]
                name = c_stock["company_name"]
                p = c_stock["current_price"]
                cagr = c_stock["expected_cagr_pct"]
                t3y = c_stock["target_3y"]
                t5y = c_stock["target_5y"]
                moat = c_stock["moat_badge"]
                tier = c_stock["compounder_tier"]
                score = c_stock["fundamental_quality_score"]

                # SIP sizing based on budget
                monthly_sip = max(1_000.0, round(user_budget * 0.10, 0))
                sip_5y_val = monthly_sip * (((1 + (cagr/100)/12)**60 - 1) / ((cagr/100)/12)) * (1 + (cagr/100)/12)
                sip_invested = monthly_sip * 60

                with st.container():
                    st.markdown(
                        f"""
                        <div class="top10-card" style="border-top: 4px solid #3FB950;margin-bottom:18px;">
                            <div class="top10-header">
                                <div>
                                    <span class="moat-pill moat-wide">🏰 {esc(moat)}</span>
                                    <span class="top10-symbol">&nbsp;{esc(tick)}</span>
                                    <div class="top10-sector">{esc(name)} · LTP: <strong>₹{p:,.2f}</strong></div>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-family:var(--mono);font-size:18px;font-weight:700;color:#3FB950;">
                                        ~{cagr:.1f}% Projected CAGR
                                    </div>
                                    <div style="font-size:11px;color:var(--text-muted);font-family:var(--mono);">
                                        Quality: {score:.0f}/100 · {esc(tier.split(' ')[1])}
                                    </div>
                                </div>
                            </div>
                            <div class="top10-grid-levels" style="grid-template-columns: repeat(3, 1fr);">
                                <div class="level-item">
                                    <span class="level-label">P/E Valuation</span>
                                    <span class="level-val">{c_stock['trailing_pe']}</span>
                                </div>
                                <div class="level-item">
                                    <span class="level-label">Return on Equity (ROE)</span>
                                    <span class="level-val" style="color:#3FB950;">{c_stock['roe_pct']}%</span>
                                </div>
                                <div class="level-item">
                                    <span class="level-label">Debt / Equity</span>
                                    <span class="level-val">{c_stock['debt_to_equity']}</span>
                                </div>
                            </div>
                            <div class="top10-grid-levels" style="grid-template-columns: repeat(2, 1fr);background:#161B22;">
                                <div class="level-item">
                                    <span class="level-label">3-Year Compounded Target</span>
                                    <span class="level-val val-target">₹{t3y:,.0f} (+{round(((t3y-p)/p)*100, 1)}%)</span>
                                </div>
                                <div class="level-item">
                                    <span class="level-label">5-Year Wealth Multiplier</span>
                                    <span class="level-val val-profit">₹{t5y:,.0f} (+{round(((t5y-p)/p)*100, 1)}%)</span>
                                </div>
                            </div>
                            <div class="top10-sizing">
                                <span>SUGGESTED SIP PLAN</span>
                                <span>Invest <strong>₹{monthly_sip:,.0f}/month</strong> → Projected to grow from ₹{sip_invested:,.0f} to <strong>₹{sip_5y_val:,.0f}</strong> in 5 years</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    col_w1, col_w2, col_w3 = st.columns([2, 2, 3])
                    with col_w1:
                        if st.button(f"📓 Paper Buy: {tick}", key=f"btn_pt_lt_{tick}_{c_idx}", use_container_width=True):
                            shares_buy = max(1, int(user_budget / max(1.0, p)))
                            trade_id = log_paper_trade(
                                ticker=tick,
                                trade_type="BUY_LONGTERM",
                                entry_price=p,
                                target_price=t3y,
                                stop_loss_price=round(p * 0.80, 2),
                                shares=shares_buy,
                                notes=f"Long-term Wealth Compounder (3Y Target ₹{t3y:,.0f})",
                            )
                            st.toast(f"✅ Paper Investment #{trade_id} logged for {tick} ({shares_buy} shares)!", icon="🌱")
                    with col_w2:
                        if st.button(f"🌱 Wealth Lab: {tick}", key=f"btn_wl_{tick}_{c_idx}", use_container_width=True):
                            st.session_state["target_operating_mode"] = "Long-Term Wealth & Compounder Lab"
                            st.rerun()
                    with col_w3:
                        with st.expander("🧠 Why is this a 0-Risk Long-Term Bet? (ELI5)"):
                            render_eli5_box(
                                title=f"Why {name} is a Wealth Compounding Machine",
                                explanation=(
                                    f"{name} is a dominant market leader with a Wide Moat. "
                                    f"It generates strong Return on Equity ({c_stock['roe_pct']}%) and consistent free cash flow. "
                                    f"Even if the stock price wobbles in the short term, earnings continue growing year after year, "
                                    f"pulling the stock price towards the 3-Year target of ₹{t3y:,.0f}."
                                ),
                                key_rules=[
                                    "Do NOT panic sell during routine 5–10% market dips.",
                                    "Use Systematic Investment Plans (SIP) to buy more shares automatically every month.",
                                    "Hold for a minimum of 3 to 5 years to let the power of compounding work.",
                                ]
                            )

    # ── 🎓 Pro Mentorship Academy Banner ──────────────────────────────────────
    st.divider()
    st.markdown("### 🎓 Zero to Hero: The 3 Golden Rules of Smart Trading")
    
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        st.info("🛡️ **Rule 1: Always Protect Capital**\n\nNever enter a trade without a strict Stop Loss. If a trade is wrong, exit early and keep your capital intact.")
    with r_col2:
        st.success("🎯 **Rule 2: Asymmetric 2:1 R:R**\n\nOnly take trades where your target gain is at least double your risk. That way, winning just 4 out of 10 trades makes you profitable!")
    with r_col3:
        st.warning("⏳ **Rule 3: Patience Beats Emotion**\n\nWait for price to come to your Buy Limit level. Never chase a green candle that has already run.")

"""
finvision/app_pages/mode5_wealth.py
===================================
Long-Term Wealth & Compounder Lab.
Fundamental Quality Scoring, Moat Classification, Valuation Analysis,
and Interactive Multi-Year SIP Wealth Multiplier Simulator.
"""

from __future__ import annotations

from typing import Any, Dict, List
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.fundamental_wealth import (
    analyze_stock_fundamentals,
    compute_sip_wealth_projection,
    compute_asymmetric_multibagger_score,
    BLUE_CHIP_COMPOUNDERS,
    COMPOUNDER_BASKETS,
    ASYMMETRIC_MEGATRENDS,
)
from utils.components import (
    render_wealth_compounder_card,
    render_eli5_box,
    esc,
)
from utils.market_store import log_paper_trade


def render_mode5():
    st.markdown("## 🌱 Long-Term Wealth & Compounder Lab")
    st.caption("Identify wide-moat market leaders, evaluate balance sheet quality, and simulate multi-year SIP compounding.")

    # ── Master Tabs ───────────────────────────────────────────────────────────
    tab_baskets, tab_analyzer, tab_sip_sim = st.tabs([
        "🏛️ Curated Wealth Baskets",
        "🔬 Single-Stock Fundamental Deep Dive",
        "📈 Interactive SIP & Compounding Simulator",
    ])

    # ── TAB 1: CURATED WEALTH BASKETS ─────────────────────────────────────────
    
    # --------------------------------------------------------------------------
    # TAB 1: ASYMMETRIC 10x MEGATREND HUNTER
    # --------------------------------------------------------------------------
    with tab_megatrends:
        st.markdown("### 🚀 Asymmetric 10x Megatrends & Second-Order Supply Chains")
        st.caption("Discover pre-boom smallcaps & midcaps positioned at structural bottlenecks (AI Power, Defense Avionics, Semiconductor OSAT, Critical Minerals) before mainstream discovery.")

        selected_theme = st.selectbox(
            "Select Emerging Secular Megatrend",
            options=list(ASYMMETRIC_MEGATRENDS.keys()),
            index=0
        )

        theme_data = ASYMMETRIC_MEGATRENDS[selected_theme]
        c_th1, c_th2 = st.columns([3, 2])
        with c_th1:
            st.info(f"**Structural Thesis:** {theme_data['description']}")
        with c_th2:
            st.warning(f"**⚡ Supply Bottleneck:** {theme_data['bottleneck_factor']}")

        st.markdown("#### 🔍 Real-Time Multi-Bagger Screening & Float Absorption")
        
        tickers_to_scan = theme_data["tickers"]
        
        scan_results = []
        with st.spinner(f"Evaluating {len(tickers_to_scan)} supply chain leaders..."):
            for t_sym in tickers_to_scan:
                res = compute_asymmetric_multibagger_score(t_sym)
                if "error" not in res:
                    scan_results.append(res)

        if scan_results:
            df_mega = pd.DataFrame(scan_results)
            # Format display dataframe
            df_display = pd.DataFrame([
                {
                    "Ticker": r["ticker"],
                    "Company Name": r["company_name"],
                    "Asymmetry Score": f"{r['score']}/100",
                    "Tier Rating": r["tier"],
                    "Mkt Cap (Cr)": f"₹{r['market_cap_cr']:,.0f}",
                    "Float Absorption (30)": f"{r['float_absorption_score']:.1f}",
                    "15D Consolidation Range": f"{r['consolidation_range_15d']:.1f}%",
                    "ROE %": f"{r['roe_pct']:.1f}%",
                    "Forward P/E": f"{r['forward_pe']:.1f}",
                    "D/E Ratio": f"{r['debt_to_equity']:.2f}"
                }
                for r in scan_results
            ])
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### 💡 How to Capitalize on This Theme")
            st.write(
                "• **Stage 1 (Stealth Accumulation):** Look for stocks with *Float Absorption > 20* and *15D Range < 6%*. Insiders are locking the free float.\n"
                "• **Stage 2 (Earnings Catalyst):** Hold for 18-36 months as order books convert to revenue on quarterly filings.\n"
                "• **Stage 3 (Exit at Peak Hype):** Offload when mainstream media begins running front-page bull market cover stories."
            )

    with tab_baskets:
        st.markdown("### 🏛️ Pre-Curated High-Quality Compounding Baskets")
        st.caption("Constructed using strict institutional criteria: Return on Equity > 15%, Low Debt, Pricing Power, and Wide Economic Moats.")

        basket_choice = st.selectbox(
            "Select Investment Theme",
            options=list(COMPOUNDER_BASKETS.keys()),
            index=0,
        )

        tickers_in_basket = COMPOUNDER_BASKETS[basket_choice]

        with st.spinner(f"Analyzing fundamentals for {basket_choice}..."):
            basket_results = []
            for t in tickers_in_basket:
                try:
                    f_data = analyze_stock_fundamentals(t)
                    if f_data.get("current_price", 0) > 0:
                        basket_results.append(f_data)
                except Exception:
                    continue

        if basket_results:
            st.markdown("#### 📊 Theme Overview Table")
            df_table = pd.DataFrame([
                {
                    "Ticker": b["ticker"],
                    "Company": b["company_name"],
                    "Sector": b["sector"],
                    "LTP": f"₹{b['current_price']:,.2f}",
                    "P/E": b["trailing_pe"],
                    "ROE %": f"{b['roe_pct']}%" if b["roe_pct"] != "N/A" else "N/A",
                    "Debt/Eq": b["debt_to_equity"],
                    "Moat Rating": b["moat_badge"],
                    "Quality Score": f"{b['fundamental_quality_score']:.0f}/100",
                    "Exp. CAGR": f"~{b['expected_cagr_pct']:.1f}%",
                    "3-Year Target": f"₹{b['target_3y']:,.0f}",
                }
                for b in basket_results
            ])
            st.dataframe(df_table, use_container_width=True, hide_index=True)

            st.markdown("#### 🏰 Detailed Compounder Cards")
            for b in basket_results:
                render_wealth_compounder_card(b)

    # ── TAB 2: SINGLE-STOCK FUNDAMENTAL DEEP DIVE ─────────────────────────────
    with tab_analyzer:
        st.markdown("### 🔬 Single-Stock Fundamental & Moat Analysis")
        st.caption("Inspect financial health, valuation ratios, margin safety, and long-term price targets.")

        c_in, c_go = st.columns([3, 1])
        with c_in:
            chosen_ticker = st.text_input("Enter NSE Stock Symbol", value="RELIANCE.NS", help="e.g. RELIANCE.NS, TCS.NS, TITAN.NS, HDFCBANK.NS")
        with c_go:
            st.write("")
            st.write("")
            run_fund = st.button("🔍 Analyze Fundamentals", use_container_width=True)

        if chosen_ticker:
            sym = chosen_ticker.strip().upper()
            if not sym.endswith(".NS") and not sym.endswith(".BO") and not sym.startswith("^"):
                sym = f"{sym}.NS"

            f_res = analyze_stock_fundamentals(sym)
            if f_res.get("current_price", 0) <= 0:
                st.error(f"Could not retrieve fundamental data for {sym}. Check the symbol.")
            else:
                p = f_res["current_price"]
                st.divider()

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Current Market Price", f"₹{p:,.2f}", f"Market Cap: ₹{f_res['market_cap_cr']:,.0f} Cr")
                m2.metric("Fundamental Quality", f"{f_res['fundamental_quality_score']:.0f} / 100", f_res["tier_code"])
                m3.metric("Moat Strength", f_res["moat_badge"], help="Economic barrier preventing competitors from taking market share")
                m4.metric("Expected CAGR", f"~{f_res['expected_cagr_pct']:.1f}%", f"3Y Target: ₹{f_res['target_3y']:,.0f}")

                render_wealth_compounder_card(f_res)

                # Valuation discount & Margin of Safety
                st.markdown("#### ⚖️ Valuation & Margin of Safety")
                pe_val = f_res["trailing_pe"]
                peg_val = f_res["peg_ratio"]

                v1, v2 = st.columns(2)
                with v1:
                    render_eli5_box(
                        title="Valuation Rationale",
                        explanation=(
                            f"{f_res['company_name']} is currently trading at a P/E of {pe_val} (PEG: {peg_val}). "
                            f"With Return on Equity of {f_res['roe_pct']}% and Debt-to-Equity at {f_res['debt_to_equity']}, "
                            f"the business retains high capital efficiency."
                        ),
                        key_rules=[
                            "PEG Ratio below 1.5 indicates reasonable price relative to growth.",
                            "High ROE (>15%) means every rupee invested generates strong profits.",
                            "Low debt ensures the company easily survives high-interest rate cycles.",
                        ]
                    )
                with v2:
                    st.markdown("##### 🎯 Multi-Year Price Horizons")
                    st.write(f"• **1-Year Target:** ₹{f_res['target_1y']:,.2f} (+{round(((f_res['target_1y']-p)/p)*100, 1)}%)")
                    st.write(f"• **3-Year Target:** ₹{f_res['target_3y']:,.2f} (+{round(((f_res['target_3y']-p)/p)*100, 1)}%)")
                    st.write(f"• **5-Year Target:** ₹{f_res['target_5y']:,.2f} (+{round(((f_res['target_5y']-p)/p)*100, 1)}%)")
                    
                    if st.button(f"📓 Log Long-Term Paper Investment for {sym}", use_container_width=True):
                        trade_id = log_paper_trade(
                            ticker=sym,
                            trade_type="BUY_LONGTERM",
                            entry_price=p,
                            target_price=f_res['target_3y'],
                            stop_loss_price=round(p * 0.80, 2),
                            shares=10,
                            notes=f"Fundamental Lab: 3Y Target ₹{f_res['target_3y']:,.0f}",
                        )
                        st.success(f"Log ID #{trade_id}: Added 10 shares of {sym} to Paper Trading Journal!")

    # ── TAB 3: SIP & COMPOUNDING SIMULATOR ─────────────────────────────────────
    with tab_sip_sim:
        st.markdown("### 📈 Interactive SIP & Wealth Compounding Simulator")
        st.caption("Visualizes how consistent monthly investing compounds exponentially over 3, 5, 10, and 15 years.")

        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            sip_monthly = st.number_input("Monthly SIP Amount (₹)", min_value=500.0, value=10_000.0, step=1_000.0)
        with s_col2:
            sip_years = st.slider("Investment Horizon (Years)", min_value=1, max_value=25, value=10)
        with s_col3:
            sip_cagr = st.slider("Expected Annual CAGR (%)", min_value=8.0, max_value=30.0, value=16.0, step=0.5)

        sip_data = compute_sip_wealth_projection(sip_monthly, sip_years, sip_cagr)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Money Invested", f"₹{sip_data['total_invested']:,.0f}")
        k2.metric("Estimated Portfolio Value", f"₹{sip_data['future_value']:,.0f}")
        k3.metric("Wealth Created (Gain)", f"+₹{sip_data['wealth_gain']:,.0f}", f"{sip_data['wealth_multiplier']}× Multiplier")
        k4.metric("Annual Compounding Rate", f"{sip_cagr:.1f}% CAGR")

        st.divider()

        # Compounding Curve Chart
        df_prog = pd.DataFrame(sip_data["progression"])
        if not df_prog.empty:
            fig_sip = go.Figure()
            fig_sip.add_trace(go.Bar(
                x=df_prog["Year"], y=df_prog["Invested Amount"],
                name="Total Invested Amount (₹)", marker_color="#30363D"
            ))
            fig_sip.add_trace(go.Bar(
                x=df_prog["Year"], y=df_prog["Compounded Profit"],
                name="Compounded Profit Gain (₹)", marker_color="#3FB950"
            ))
            fig_sip.update_layout(
                barmode="stack",
                title=f"Exponential Wealth Accumulation Curve ({sip_years} Years @ {sip_cagr}% CAGR)",
                template="plotly_dark",
                height=380,
                legend=dict(orientation="h", y=1.12),
                yaxis_title="Portfolio Value (₹)",
            )
            st.plotly_chart(fig_sip, use_container_width=True)

            st.dataframe(df_prog, use_container_width=True, hide_index=True)

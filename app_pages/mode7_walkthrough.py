"""
finvision/app_pages/mode7_walkthrough.py
========================================
Interactive App Walkthrough & User Guide for FinVision v3.0.
Provides an easy, visual, step-by-step masterclass on how to navigate,
utilize, and profit with every institutional feature in FinVision.
"""

from __future__ import annotations

import streamlit as st
import textwrap


def render_mode7():
    st.markdown(
        textwrap.dedent("""
        <div class="copilot-hero-card" style="margin-bottom:20px;">
            <div class="copilot-hero-title">📖 FinVision v3.0 Master Walkthrough & Field Manual</div>
            <div class="copilot-hero-subtitle">
                Welcome to <strong>FinVision</strong> — India's premier quantitative decision terminal, multi-broker gateway,
                and AI mentor. Whether you are trading intraday momentum on Dalal Street or building a generational equity portfolio,
                this interactive field guide explains how to get the maximum statistical edge from every feature.
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    tabs = st.tabs([
        "🚀 60-Second Quickstart",
        "🤖 Mode 0: Smart Copilot",
        "🏛️ BSE & Dual-Exchange",
        "💰 Tax & GTT Order Math",
        "🌱 Wealth Multiplier",
        "🎓 AI Autopsy & Academy",
        "🔌 API & MCP Servers",
    ])

    # ── TAB 1: 60-Second Quickstart ───────────────────────────────────────────
    with tabs[0]:
        st.markdown("### ⚡ Zero to Your First Trade in 60 Seconds")
        
        st.info(
            "FinVision is engineered with an **Institutions-First, 0-Knowledge** philosophy. "
            "You do not need to be a chart expert or a chartered financial analyst — the AI handles the math, "
            "risk sizing, and regulatory checks for you."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:10px; padding:16px; height:100%;">
                    <div style="font-size:24px; margin-bottom:8px;">1️⃣</div>
                    <div style="font-weight:700; color:#58A6FF; font-size:15px; margin-bottom:6px;">Set Capital in Sidebar</div>
                    <div style="font-size:13px; color:#8B949E; line-height:1.5;">
                        Open the left sidebar and enter your available <strong>Trading Capital (₹)</strong> and risk tolerance (e.g. 1.0%). 
                        FinVision saves this to its local database so you never have to re-enter it.
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:10px; padding:16px; height:100%;">
                    <div style="font-size:24px; margin-bottom:8px;">2️⃣</div>
                    <div style="font-weight:700; color:#00E676; font-size:15px; margin-bottom:6px;">Read the Regime Radar</div>
                    <div style="font-size:13px; color:#8B949E; line-height:1.5;">
                        Check the top card on <strong>Mode 0</strong>. If it's <strong>🟢 Bull Markup</strong>, buy breakouts. If 
                        <strong>⚠️ High Volatility Chop</strong>, buy pullbacks. If <strong>🔴 Bear Markdown</strong>, focus strictly on capital preservation.
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:10px; padding:16px; height:100%;">
                    <div style="font-size:24px; margin-bottom:8px;">3️⃣</div>
                    <div style="font-weight:700; color:#E3B341; font-size:15px; margin-bottom:6px;">Deploy 1-Click GTT or Sim</div>
                    <div style="font-size:13px; color:#8B949E; line-height:1.5;">
                        Scroll down to <strong>Setup #1</strong>. Expand the <strong>📋 Zerodha / Upstox GTT</strong> box to copy pre-calculated triggers, 
                        or tap <strong>📝 Simulate Paper Trade</strong> for risk-free execution!
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("#### 🗺️ Navigation Map")
        st.markdown(
            "Use the **Mode Selection** dropdown in the sidebar to navigate between specialized desks:\n"
            "* **🤖 Smart Copilot**: The central AI mission control. Generates ready-to-execute day trades and blue-chip compounders.\n"
            "* **📡 Market Scanner & Top 10 Alpha**: Institutional screener parsing 500+ stocks for momentum bursts and delivery accumulation.\n"
            "* **🌱 Long-Term Wealth & Compounder Lab**: Value investing engine scoring ROCE, Free Cash Flow, and margin of safety.\n"
            "* **⚡ Live Intraday Monitor**: Real-time tick tracker with VWAP bands and microsecond volume flow.\n"
            "* **🔬 Forecast & Correlation Lab**: Monte Carlo probabilistic cones and Lopez de Prado meta-labeling analysis.\n"
            "* **🔍 Manual Ticker Analysis**: In-depth multi-timeframe deep-dive for any NSE/BSE security.\n"
            "* **🎓 AI Academy & Paper Trading**: Live trade journal, automated autopsies, and the Mentor Wisdom Fact-Checker."
        )

    # ── TAB 2: Mode 0 Smart Copilot ───────────────────────────────────────────
    with tabs[1]:
        st.markdown("### 🤖 Mode 0: Smart Trade & Wealth Copilot")
        st.markdown(
            "The Copilot is designed to be your full-time quantitative trading partner. "
            "Here is how its proprietary institutional layers work:"
        )

        with st.expander("1. 🏛️ Dual-Exchange Regime Radar & Macro Barometer", expanded=True):
            st.markdown(
                textwrap.dedent("""
                * **Nifty 50 & BSE Sensex Alignment**: Instead of looking at individual stocks in isolation, FinVision evaluates broad market structure. 
                  If Nifty and Sensex are both trending above their 20 EMAs, you get full position sizing.
                * **Cross-Asset Macro Barometer**: Streams live Brent Crude Oil, USD/INR foreign exchange, and Gold prices. 
                  Surging oil hurts Indian corporate margins; a weakening rupee causes foreign institutional selling. FinVision warns you before macro drags hit your stocks.
                * **Permanent Live Dalal Street Feed**: Real-time price tracking for Nifty 50, Sensex, Bank Nifty, Reliance, TCS, HDFC Bank, Infosys, and SBI.
                """)
            )

        with st.expander("2. 🧠 Lopez de Prado Meta-Labeler ('The Veteran Brain')", expanded=True):
            st.markdown(
                textwrap.dedent("""
                Traditional retail indicators give frequent false breakouts. FinVision uses a two-stage institutional filter:
                1. **Primary Confluence Model**: Evaluates Trend, Momentum, S&R, Volume, and News Sentiment to spot opportunities.
                2. **The Meta-Labeler (The Veteran)**: Evaluates whether market conditions actually support taking this trade.
                
                **Verdict Badges:**
                * <span style="color:#00E676; font-weight:700;">✅ FULL CONVICTION (1.0x Size)</span>: High statistical edge; deploy full calculated budget.
                * <span style="color:#FFB300; font-weight:700;">⚠️ HALF SIZE (0.5x Size)</span>: Chop risk detected; position size sliced 50% automatically to protect capital.
                * <span style="color:#FF5252; font-weight:700;">⛔ AI VETO (0.0x Size)</span>: Model predicts high probability of a stop-out or whipsaw. FinVision actively prevents you from trading it.
                """, )
            , unsafe_allow_html=True)

        with st.expander("3. 📉 Tail-Risk Engine: 1-Day 95% VaR & Expected Shortfall (CVaR)", expanded=True):
            st.markdown(
                textwrap.dedent("""
                Instead of arbitrary percentage stops, FinVision calculates Wall Street risk metrics:
                * **1-Day 95% Value-at-Risk (VaR)**: The maximum loss expected over a 1-day holding horizon under 95% of normal market conditions.
                * **Conditional Value-at-Risk (CVaR / Expected Shortfall)**: The average loss in the extreme 5% tail event (e.g. surprise rate hike or flash crash).
                * Both metrics are displayed in **exact ₹ amounts** tailored to your active budget!
                """)
            )

    # ── TAB 3: BSE & Dual-Exchange ────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### 🏛️ First-Class BSE (Bombay Stock Exchange) Support")
        st.markdown(
            "FinVision treats BSE as an equal institutional partner alongside NSE, "
            "unlocking distinct quantitative edges available only on the Bombay Stock Exchange."
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px; margin-bottom:12px;">
                    <div style="color:#58A6FF; font-weight:700; font-size:15px; margin-bottom:6px;">🔢 6-Digit Scrip Code Resolution</div>
                    <div style="font-size:12px; color:#C9D1D9; line-height:1.5;">
                        Type <code>500325</code>, <code>500209</code>, or <code>532540</code> in search boxes. FinVision instantly resolves them 
                        to <strong>Reliance</strong>, <strong>Infosys</strong>, and <strong>TCS</strong> with dual exchange symbols (<code>.NS</code> / <code>.BO</code>).
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px;">
                    <div style="color:#00E676; font-weight:700; font-size:15px; margin-bottom:6px;">🔍 3,000+ BSE-Exclusive Universe</div>
                    <div style="font-size:12px; color:#C9D1D9; line-height:1.5;">
                        While NSE lists ~2,100 equities, BSE lists over 5,400. FinVision detects and routes securities that trade 
                        exclusively on the BSE (e.g. <code>500111.BO</code>), allowing you to scan early-stage smallcaps.
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px; margin-bottom:12px;">
                    <div style="color:#FFB300; font-weight:700; font-size:15px; margin-bottom:6px;">📢 BSE Direct Regulatory Disclosures</div>
                    <div style="font-size:12px; color:#C9D1D9; line-height:1.5;">
                        Under SEBI guidelines, public companies must submit official regulatory filings directly to BSE first. 
                        FinVision indexes these raw corporate disclosures straight into ChromaDB Vector News before financial blogs write about them.
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px;">
                    <div style="color:#F85149; font-weight:700; font-size:15px; margin-bottom:6px;">⚠️ Binary Corporate Event Risk Guard</div>
                    <div style="font-size:12px; color:#C9D1D9; line-height:1.5;">
                        FinVision checks whether a company has an upcoming quarterly earnings board meeting or dividend record date within 72 hours. 
                        If so, it attaches a warning badge to prevent holding swing trades into unpredictable binary gap events.
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )

    # ── TAB 4: Tax & GTT Order Math ───────────────────────────────────────────
    with tabs[3]:
        st.markdown("### 💰 Indian Tax Friction & Automated GTT Math")

        st.markdown("#### 1. Indian Statutory Friction Engine")
        st.markdown(
            "Every trade card in FinVision features an automated regulatory tax calculator. "
            "It computes the exact statutory friction breakdown in real time:"
        )

        st.markdown(
            textwrap.dedent("""
            | Component | Intraday (MIS) Rate | Delivery (CNC) Rate | Authority |
            | :--- | :--- | :--- | :--- |
            | **STT (Securities Transaction Tax)** | 0.025% on Sell Turnover | 0.10% on Buy & Sell Turnover | Government of India |
            | **Exchange Turnover Fee** | 0.00297% on Turnover | 0.00297% on Turnover | NSE / BSE |
            | **SEBI Turnover Charges** | ₹10 per Crore (0.0001%) | ₹10 per Crore (0.0001%) | SEBI |
            | **Stamp Duty** | 0.003% on Buy Turnover | 0.015% on Buy Turnover | State Governments |
            | **GST (Goods & Services Tax)** | 18% on (Brokerage + Exchange + SEBI) | 18% on (Brokerage + Exchange + SEBI) | Central & State GST |
            | **Flat Brokerage** | ₹20 per order (₹40 round-trip) | ₹0 to ₹20 per order | Discount Broker (Zerodha/Groww) |
            """)
        )

        st.markdown(
            "> 💡 **Net Take-Home ₹**: The setup badge shows `Gross Profit` minus `Taxes & Brokerage` to give you the true net cash that enters your bank account, along with the exact **Break-Even Exit Price**!"
        )

        st.markdown("---")
        st.markdown("#### 2. Automated GTT (Good-Till-Triggered) Order Math")
        st.markdown(
            "GTT orders stay active on the exchange for up to 1 year without requiring daily placement. "
            "FinVision calculates exchange tick offsets (0.20% buffer on trigger price) to prevent missed executions during fast momentum spikes:"
        )

        st.code(
            textwrap.dedent("""
            GTT BUY TATASTEEL
            Trigger: ₹185.25 | Limit Price: ₹185.62 | Qty: 336

            GTT OCO TATASTEEL
            [STOP-LOSS] Trigger: ₹187.61 (+0.9%) | Price: ₹187.24
            [TARGET 1]  Trigger: ₹181.20 (-2.2%) | Price: ₹181.56 | Qty: 336
            """),
            language="text"
        )
        st.caption("Simply click the copy icon inside the GTT box and paste directly into Zerodha Kite, Groww, or Upstox.")

    # ── TAB 5: Wealth Multiplier ──────────────────────────────────────────────
    with tabs[4]:
        st.markdown("### 🌱 Mode 5: Long-Term Wealth & Multi-Bagger Compounder Lab")
        st.markdown(
            "Day trading generates cash flow; long-term investing creates generational wealth. "
            "Mode 5 focuses on fundamental quality, pricing power, and return on invested capital."
        )

        st.markdown(
            textwrap.dedent("""
            #### 🏆 The 4 Pillars of a FinVision Wealth Multiplier:
            1. **Return on Capital Employed (ROCE > 18%)**: Company generates high cash earnings without taking excessive debt.
            2. **Free Cash Flow (FCF) Yield**: Business generates real net cash after capital expenditure, funding dividend compounding and share buybacks.
            3. **Low Debt / Equity (< 0.5x)**: High survivability during economic recessions and high interest rate cycles.
            4. **Valuation Margin of Safety**: Uses historical P/E bands, PEG ratio, and price-to-book to ensure you never overpay for growth.
            """)
        )

        st.info(
            "💡 **Compounder Tip**: Use the built-in SIP Wealth Calculator to simulate how investing ₹25,000/month "
            "in top compounders at 18% CAGR accumulates into multi-crore wealth over 10 to 15 years."
        )

    # ── TAB 6: AI Autopsy & Academy ───────────────────────────────────────────
    with tabs[5]:
        st.markdown("### 🎓 Mode 6: AI Academy & Post-Mortem Autopsy Lab")
        st.markdown(
            "Most trading systems never learn from their mistakes. FinVision continuously evolves "
            "by performing automated forensic autopsies on every closed trade in your SQLite journal."
        )

        st.markdown(
            textwrap.dedent("""
            #### 🔬 Automated Root-Cause Autopsies:
            * **`LIQUIDITY_SWEEP_HUNT`**:
              * *Diagnosis*: Price breached your stop loss by less than 0.85% and immediately reversed back into your target.
              * *Adaptive Learning*: Automatically widens that stock's adaptive ATR stop multiplier from $1.0\\text{x} \\rightarrow 1.35\\text{x}$ to place stops beyond institutional stop hunts.
            * **`MACRO_REGIME_DRAG`**:
              * *Diagnosis*: Stock was technically sound, but failed purely because Nifty dumped $>1.25\\%$ during the trade.
              * *Adaptive Learning*: Does not penalize the stock's technical setup; reinforces broad market regime gating.
            * **`TARGET_BLOWOFF_RUNNER`**:
              * *Diagnosis*: Momentum exploded beyond Target 2 by $>2\\%$.
              * *Adaptive Learning*: Activates trailing ratchets to capture larger runners.
            """)
        )

        st.markdown("---")
        st.markdown("#### 🎖️ Veteran Wisdom Fact-Check & Ingestion Lab")
        st.markdown(
            "Heard a rule from a mentor, YouTuber, or floor trader? Type it in plain English "
            "(e.g., *'Buy Tata Motors when RSI drops below 30 on daily chart and hold for 2 weeks'*). "
            "FinVision will run a 2-year empirical walk-forward backtest across real historical NSE/BSE candles. "
            "If it achieves $>55\\%$ win rate and positive expectancy, it is validated and ingested into your AI knowledge base. "
            "If it fails, the unbacked folklore is debunked with hard data."
        )

    # ── TAB 7: API & MCP Servers ──────────────────────────────────────────────
    with tabs[6]:
        st.markdown("### 🔌 API Server & Model Context Protocol (MCP)")
        st.markdown(
            "FinVision is a headless quantitative engine that can be accessed from external automation tools, "
            "TradingView alerts, Claude Desktop, Cursor, or your custom Python scripts."
        )

        st.markdown("#### 1. Headless REST API (`api_server.py`)")
        st.markdown("Run the high-performance FastAPI server locally:")
        st.code("python api_server.py --port 8000", language="bash")
        
        st.markdown(
            "* `GET /api/regime`: Returns live market regime, Nifty/Sensex trend, India VIX, and macro score.\n"
            "* `GET /api/setup/{ticker}`: Returns quantitative setup, entry/target/SL, GTT math, and VaR tail risk.\n"
            "* `GET /api/bse/resolve/{query}`: Universally resolves 6-digit BSE scrip codes (`500325` -> `RELIANCE`).\n"
            "* `POST /api/webhook/tradingview`: Webhook listener for TradingView Pine Script alerts with AI divergence veto."
        )

        st.markdown("---")
        st.markdown("#### 2. Claude Desktop & Cursor MCP Server (`mcp_server.py`)")
        st.markdown("To let Claude or Cursor talk to FinVision natively, add this to your `claude_desktop_config.json`:")
        st.code(
            textwrap.dedent("""
            {
              "mcpServers": {
                "finvision": {
                  "command": "python",
                  "args": ["g:/AI/Stock/Stock_Claude/finvision_bkp/mcp_server.py"]
                }
              }
            }
            """),
            language="json"
        )
        st.caption("Exposes `get_market_regime`, `analyze_stock_setup`, `calculate_gtt_order`, `calculate_indian_market_taxes`, and `resolve_bse_security` over standard JSON-RPC 2.0 stdio.")

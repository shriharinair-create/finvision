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
    c_back, _ = st.columns([1.5, 3])
    with c_back:
        if st.button("🔙 Back to Smart Copilot", key="walkthrough_back_to_copilot_btn", use_container_width=True):
            st.session_state["target_operating_mode"] = "copilot"
            st.rerun()

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
        "📱 Cross-Device & Auto-Failover",
        "👥 Multi-User, Friends & iPhone",
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

        with st.expander("4. 🇮🇳 Official Indian Macro Economic Feed & Financial Conditions Index (FCI)", expanded=True):
            st.markdown(
                textwrap.dedent("""
                FinVision bridges real-time macro indicators from official RBI and MoSPI data releases:
                * **RBI Policy Repo Rate (6.50%)**: Baseline benchmark rate determining system-wide liquidity cost.
                * **India CPI Inflation (5.08%)**: Evaluated against RBI's 4.0% midpoint target to gauge real interest rates.
                * **Real GDP Growth (6.70%)**: Underpins corporate earnings expansion.
                * **Indian Financial Conditions Index (FCI)**: Synthesizes rates, inflation, crude oil, and USD/INR into a single macro risk badge (`🟢 Expansive`, `⚪ Balanced`, `🟡 Restrictive`, `🔴 Severe Drag`).
                """)
            )

        with st.expander("5. 🎯 Dynamic Regime-Adaptive Confluence Weighting Engine", expanded=True):
            st.markdown(
                textwrap.dedent("""
                No more static, fixed indicator weights. FinVision dynamically evolves its 6-factor confluence matrix based on the active market regime:
                * **🟢 Bull Markup**: Trend (35%) and Momentum (30%) dominate — buy breakouts and ride EMA hierarchies.
                * **⚠️ High Volatility Chop**: Support/Resistance Mean Reversion (40%) and Oversold Oscillators (30%) dominate; Trend is slashed to 10% to prevent whipsaws.
                * **🔴 Bear Markdown**: Overhead Resistance Supply (35%) and Volatility Bands (25%) dominate — protect capital.
                * **⚪ Consolidation Base**: Volume Accumulation (30%) and Range Boundaries (25%) dominate — identify coiling spring setups before the explosion.
                """)
            )

        with st.expander("6. 🎯 The 3 Autonomous & Assisted Ways to Trade", expanded=True):
            st.markdown(
                textwrap.dedent("""
                FinVision supports three distinct execution workflows tailored to different trader preferences:
                
                #### 1️⃣ Way 1: Full AI Autopilot (Hands-Free Dalal Street Radar)
                * **How to use**: In the Auto-Trader Cockpit settings, select `🤖 Full AI Autopilot (Nifty 500 Radar)` and toggle Auto-Trade ON.
                * **Who decides what**: The AI scans 500+ Indian equities, checks Lopez de Prado win probability (>55%), sizes to your 1% risk rule, and handles entry, trailing stop-losses, and profit exits automatically.
                * **Best for**: Traders who want a disciplined, emotions-free quantitative assistant running in the background.

                #### 2️⃣ Way 2: Targeted Watchlist (You Pick Stocks — AI Decides Timing)
                * **How to use**: In Cockpit settings, select `🎯 Custom Watchlist (My Stocks Only)` and enter your tickers (e.g. `TATAMOTORS, INFY, RELIANCE, HDFCBANK`).
                * **Who decides what**: You specify the stocks you believe in. The AI ignores the rest of Dalal Street, monitors your tickers' 15-minute candles and volume flow, and executes only when an institutional breakout forms.
                * **Best for**: Sector specialists, portfolio builders, or traders with a favorite stock basket.

                #### 3️⃣ Way 3: Custom Bracket Queue (You Pick Stocks & Exact Prices — AI Executes)
                * **How to use**: Expand `⚡ Queue Custom Bracket Order` directly in the Copilot. Enter your stock, exact Entry Price (e.g. ₹980), Target Price (₹1020), and Stop Loss (₹960).
                * **Who decides what**: You define your exact trade plan. The Auto-Trader background daemon takes custody, monitoring live market ticks every 3 minutes and executing the exit automatically when Target or Stop Loss is reached!
                * **Best for**: Executing mentor tips, chartist levels, or planned swing setups without sitting in front of the screen.
                """)
            )

        with st.expander("7. ⏱️ Why the 3-Minute Scanner Frequency is the Institutional Sweet Spot", expanded=True):
            st.markdown(
                textwrap.dedent("""
                #### ❓ Does scanning every 3 minutes cause you to miss good deals?
                **No.** In quantitative trading, a 3-minute aggregation cycle is the proven institutional standard for retail and prop desks. Here is why:

                1. **Candle Alignment (15-Minute & 1-Hour Waves)**:
                   * FinVision's intraday momentum models trade **15-minute and 1-hour candle structures**.
                   * A 15-minute candle takes 900 seconds to form. A 3-minute scanner evaluates the candle **5 separate times** while it develops!
                   * Real institutional breakouts and accumulation unfold over **15 to 45 minutes**, not in 10 seconds. You are never late to a sustainable move.
                
                2. **The "Noise vs Signal" Trap (Avoiding Fake Wicks)**:
                   * Scanning every 5 or 10 seconds traps retail traders in **"False Wick Chasing"**: algorithms frequently spike a stock for 30 seconds to trigger retail breakout orders, only to dump it back down before the candle closes.
                   * A 3-minute window allows tick volume to settle, confirming whether buying pressure is genuine institutional accumulation or spoofed noise.
                
                3. **Microsecond Execution via GTT Limits**:
                   * You do **not** rely on scanner polling speed to exit trades!
                   * FinVision calculates exchange-native **Good-Till-Triggered (GTT) OCO bracket orders** with pre-calculated tick buffers.
                   * Once parked on the exchange matching engine (Zerodha/Upstox), **your order triggers at 0-millisecond speed** the instant price touches your level.
                
                4. **Exchange & Broker Rate Limit Safety**:
                   * Discount brokers (Zerodha Kite, Upstox) strictly enforce API rate limits (typically 3 requests/sec).
                   * Polling 500 stocks every 10 seconds fires 3,000 requests per minute—guaranteeing HTTP 429 rate-limit blocks or IP bans.
                   * A 3-minute cycle ensures 100% compliance, zero server crashes, and minimal battery drain on mobile phones.
                """)
            )

        with st.expander("8. 🛡️ The 8 Institutional Circuit Breakers & Risk Shields", expanded=True):
            st.markdown(
                textwrap.dedent("""
                To permanently eliminate catastrophic loss vulnerabilities, FinVision embeds an institutional defense-in-depth matrix:

                | Risk Shield | Trigger Condition | Automated Protective Action |
                | :--- | :--- | :--- |
                | **1. Daily Drawdown Breaker** | Account P&L drops below **-2.5%** in a single session | Halts all autonomous entries for 24h; preserves remaining 97.5% of capital. |
                | **2. Consecutive Loss Cooldown** | **3 consecutive stop-outs** in a 24-hour window | 12-hour timeout; prevents revenge trading and algorithmic tilt during chop. |
                | **3. Data Anomaly Guard** | Quote timestamp stale (>10m) or single candle jump **>25%** | Vetoes order immediately; prevents trading on corrupted broker data feeds. |
                | **4. Circuit Limit Trap Shield** | Stock price within **0.8%** of 5%/10%/20% exchange band | Blocks entry; prevents getting trapped in lower-circuit illiquidity freeze. |
                | **5. India VIX Panic Governor** | India VIX exceeds **22.0** or surges **>15%** intraday | Switches to Capital Preservation; suppresses breakout long entries. |
                | **6. Sample-Gated Retraining** | Closed trade sample size **$N < 50$** | Defers ML ensemble retraining to eliminate small-sample recency overfitting. |
                | **7. Friday Weekend Blackout** | Friday afternoon past **14:30 IST** | Disallows new multi-day swing holds into weekend geopolitical gap risk. |
                | **8. Emergency Kill Button** | Trader clicks **`🚨 EMERGENCY KILL`** | Immediately shuts off Auto-Trader and locks shields for the day. |
                """)
            )

    # ── TAB 3: Cross-Device & Auto-Failover ───────────────────────────────────
    with tabs[2]:
        st.markdown("### 📱 Cross-Device Synchronisation & Automated Failover")
        st.markdown(
            "FinVision's hybrid architecture is engineered for Dalal Street traders who move between "
            "a multi-monitor PC trading desk and a mobile phone on the go. "
            "The system uses an **Autonomous Leader / Standby Companion** model to ensure you never miss a setup "
            "while strictly preventing duplicate trade executions."
        )

        st.info(
            "🛡️ **Single-Leader Safety Guarantee**: Even if both your PC and phone are open at the exact same moment, "
            "only **one device** is authorized as the Execution Leader. All other connected devices act as high-convenience "
            "telemetry and monitoring consoles."
        )

        with st.expander("Scenario 1: Starting on PC 🖥️ ➡️ Switching to Phone 📱", expanded=True):
            st.markdown(
                textwrap.dedent("""
                #### 🖥️ Desk to 📱 Mobile Transition Procedure:
                1. **Morning Market Open (9:15 AM)**: Open FinVision on your PC. In the **Auto-Trader Cockpit**, set your capital, risk %, and toggle Auto-Trade **ON**.
                2. **Verify Leader Role**: The top banner will display: `🖥️ LEADER: PC (Active & Executing)`. Your PC daemon scans Dalal Street every 3 minutes.
                3. **Step Away From Your Desk**: Leave your PC running. When you open FinVision on your phone (via mobile browser, Android APK, or iOS PWA), it automatically pulls the latest trade state via Cloud Relay.
                4. **Mobile Companion Mode**: Your phone displays `📱 COMPANION (Monitoring PC Execution)`. You can monitor live P&L, stop-loss ratchets, and scanner telemetry.
                5. **Want to Turn Off Your PC?**:
                   * *Option A (Manual)*: In the Cockpit settings expander, change **Strategy** to `☁️ Cloud 24/7 Primary`. The Cloud engine takes custody; you can now safely shut down your PC.
                   * *Option B (Automatic)*: Just shut down your PC! FinVision's **Auto-Failover** will detect the missing heartbeat and take over automatically.
                """)
            )

        with st.expander("Scenario 2: Starting on Phone 📱 ➡️ Switching to PC 🖥️", expanded=True):
            st.markdown(
                textwrap.dedent("""
                #### 📱 Mobile to 🖥️ Desk Transition Procedure:
                1. **Morning Commute**: Open FinVision on your phone. Turn Auto-Trader ON. The execution role defaults to `☁️ Cloud 24/7 Primary`. The cloud scans stocks and executes orders.
                2. **Arrive at Desk**: Power on your PC and launch FinVision (`http://localhost:8501`).
                3. **Sync State**: Click the **`[☁️ Sync PC & Mobile Now]`** button in the Auto-Trader Cockpit (or let the auto-sync daemon pull within 3 minutes).
                4. **PC Assumes Leadership**: Your PC detects the cloud session, imports all active positions and trailing stops, and automatically becomes the **`🖥️ LEADER: PC`**.
                5. **Cloud Demotes to Watchdog**: The cloud node safely steps down to secondary standby to prevent duplicate order placement on Dalal Street.
                """)
            )

        with st.expander("Scenario 3: PC Sudden Crash or Power Outage (Automated Failover)", expanded=True):
            st.markdown(
                textwrap.dedent("""
                #### ⚡ Automated Watchdog & Crash Protection:
                * **Continuous Heartbeat**: While your PC is running, it emits a heartbeat timestamp (`pc_heartbeat_timestamp`) into the sync cloud every 3 minutes.
                * **Failure Detection**: If your PC crashes, freezes, loses internet, or suffers a power cut, the heartbeat stops updating.
                * **Automated Takeover**: FinVision's cloud watchdog runs `check_pc_heartbeat_health()`. If no heartbeat is received for **> 8 minutes**, the cloud node automatically promotes itself to:
                  <div style="background:#1B3A24; border:1px solid #00E676; border-radius:6px; padding:8px 12px; margin:8px 0; color:#00E676; font-weight:700;">
                      ⚡ AUTO-FAILOVER ACTIVE: PC Offline — Cloud Managing Positions
                  </div>
                * **Position Custody**: The cloud immediately assumes control of all open positions, tracks trailing stop triggers, and guarantees strict **3:15 PM Intraday (MIS) Square-Off**.
                * **Graceful Recovery**: When your PC reboots and reconnects, it detects the cloud's management, pulls the latest exit logs, and reclaims Leader custody smoothly.
                """),
                unsafe_allow_html=True
            )

        with st.expander("Scenario 4: Cloud Server Disruption / Streamlit Reboot", expanded=False):
            st.markdown(
                textwrap.dedent("""
                * All active trades, stop-loss ratchets, and settings are persistently written to SQLite (`db/finvision.db`) and synced as JSON state.
                * If the Streamlit Cloud container sleeps or restarts, the auto-trader daemon reloads existing open positions from disk on boot.
                * No trade data or order triggers are lost during container reboots.
                """)
            )

        with st.expander("Scenario 5: Zero-Trade Standby Mode ('I do not want to trade today')", expanded=False):
            st.markdown(
                textwrap.dedent("""
                * Simply leave the **Master Auto-Trader Switch** in the Cockpit toggled **`OFF`** (or select `Manual Approval Only` in Execution Mode).
                * The **📡 Live Scanner Radar** will still scan the entire Nifty 500, calculate technical confluences, evaluate Wyckoff structures, and display top trade setups.
                * **Zero orders** (neither paper nor live broker) will ever be placed until you explicitly toggle the switch ON.
                """)
            )

    # ── TAB 4: Multi-User, Friends & iPhone ───────────────────────────────────
    with tabs[3]:
        st.markdown("### 👥 Multi-User Architecture, Sharing & iPhone Setup")
        st.markdown(
            "FinVision is built to empower both individual quantitative traders and trading syndicates. "
            "Here is how you can share FinVision with friends, run distinct personal portfolios, and install on iOS."
        )

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px; height:100%;">
                    <div style="color:#58A6FF; font-weight:700; font-size:15px; margin-bottom:6px;">🔗 Sharing via Cloud Web URL</div>
                    <div style="font-size:13px; color:#C9D1D9; line-height:1.5;">
                        Send your friend the live deployment link:<br>
                        <a href="https://finvision-8ysyduhykcish78fnyoxrf.streamlit.app" target="_blank" style="color:#58A6FF; font-weight:700;">
                            finvision.streamlit.app
                        </a><br>
                        They can open it instantly in any web browser on Windows, Mac, Linux, Android, iPad, or iPhone with <strong>zero installation</strong> required!
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with col_s2:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px; height:100%;">
                    <div style="color:#00E676; font-weight:700; font-size:15px; margin-bottom:6px;">🏠 Local Wi-Fi / LAN Sharing</div>
                    <div style="font-size:13px; color:#C9D1D9; line-height:1.5;">
                        If your friend is at your home or office on the same Wi-Fi network, they can access your high-speed PC server directly by navigating to:<br>
                        <code style="color:#00E676;">http://&lt;YOUR-PC-IP&gt;:8501</code><br>
                        This provides zero-latency access to your local GPU/CPU compute and SQLite database.
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("#### 🧠 Multi-User Feasibility: Isolated Wallets with Shared Collective AI")
        st.info(
            "💡 **Can multiple friends trade independently with separate settings while sharing AI learnings?**\n\n"
            "**YES, 100% FEASIBLE!** In quantitative finance, this is known as **Multi-Tenant Profile Isolation with a Shared Feature Store**."
        )

        st.markdown(
            textwrap.dedent("""
            | Dimension | How It Works in FinVision | Separation Level |
            | :--- | :--- | :--- |
            | **Trading Capital & Risk** | User A sets ₹50,000 (1% risk); User B sets ₹5,00,000 (0.5% risk). Sizing math and stops are strictly individual. | 🔒 **100% Isolated** |
            | **Execution Mode** | User A runs **Paper Simulation**; User B runs **Semi-Auto Manual**; User C connects **Live Zerodha/Groww API**. | 🔒 **100% Isolated** |
            | **Stock Whitelist / Universe** | User A lets AI pick any Nifty 500 stock; User B restricts to `TATAMOTORS, INFY, RELIANCE`; User C trades only PSU Banks. | 🔒 **100% Isolated** |
            | **Portfolio & Trade Journal** | Active positions, P&L history, and GTT trigger logs are isolated per user profile in SQLite (`paper_trades WHERE user_id = ?`). | 🔒 **100% Isolated** |
            | **AI Forensic Autopsies** | When User A gets wicked out by a stop-hunt on Tata Motors, the AI widens the **Adaptive ATR Multiplier** ($1.0\\text{x} \\rightarrow 1.35\\text{x}$) in the shared knowledge base. | 🌐 **Shared Collective Edge** |
            | **Causal News & Market Regime** | Real-time RBI rate analysis, crude oil shocks, and Wyckoff market regimes are computed once and guide all users simultaneously. | 🌐 **Shared Collective Edge** |
            """)
        )

        st.markdown(
            "> 🤝 **The Collective Advantage**: Each user's private capital and stock selections remain strictly their own, "
            "but every mistake or market anomaly encountered by one user enriches the AI's forensic memory, making the trading engine "
            "smarter for everyone in your syndicate!"
        )

        st.markdown("---")
        st.markdown("#### 🍏 iPhone & iOS Setup Guide (Native PWA Mode)")
        st.markdown(
            "Apple does not allow side-loading APKs, but FinVision is fully engineered as an **iOS Progressive Web App (PWA)**. "
            "Your friends on iPhone can install FinVision as a native home-screen app in 30 seconds:"
        )

        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        with col_i1:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:12px; height:100%;">
                    <div style="font-size:20px; font-weight:700; color:#58A6FF;">Step 1</div>
                    <div style="font-size:12px; color:#C9D1D9; margin-top:6px;">
                        Open <strong>Safari</strong> on your iPhone and navigate to:<br>
                        <code>finvision.streamlit.app</code>
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with col_i2:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:12px; height:100%;">
                    <div style="font-size:20px; font-weight:700; color:#00E676;">Step 2</div>
                    <div style="font-size:12px; color:#C9D1D9; margin-top:6px;">
                        Tap the <strong>Share</strong> button at the bottom of the screen (the square with an arrow pointing upward).
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with col_i3:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:12px; height:100%;">
                    <div style="font-size:20px; font-weight:700; color:#FFB300;">Step 3</div>
                    <div style="font-size:12px; color:#C9D1D9; margin-top:6px;">
                        Scroll down the share sheet and tap <strong>"Add to Home Screen"</strong> (with the <code>[+]</code> icon).
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with col_i4:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:12px; height:100%;">
                    <div style="font-size:20px; font-weight:700; color:#F85149;">Step 4</div>
                    <div style="font-size:12px; color:#C9D1D9; margin-top:6px;">
                        Confirm the name as <strong>FinVision</strong> and tap <strong>Add</strong> in the top-right corner. Done!
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )

        st.caption(
            "✨ **Why the iOS PWA is awesome**: When launched from the iPhone home screen, FinVision opens in full-screen standalone mode "
            "— no Safari URL bar, no bottom navigation chrome, silky 60fps pinch-to-zoom TradingView charts, and persistent biometric dark mode!"
        )

        st.markdown("---")
        st.markdown("#### 🛠️ Friend Setup Guide: Pure Cloud vs Dedicated Local PC")
        st.markdown(
            "Can your friend also run FinVision on their PC and switch back and forth to their phone like you do? "
            "**Yes!** It depends on whether they want an instant cloud setup or their own physical PC execution engine:"
        )

        with st.expander("Option 1: Pure Cloud Mode (⚡ 0 Seconds Setup — 100% Instant)", expanded=True):
            st.markdown(
                textwrap.dedent("""
                * **How it works**: Your friend opens `finvision.streamlit.app` on their PC browser (Chrome/Edge/Safari) and on their phone (or iPhone PWA).
                * **Pros**: Requires **zero installation**, no Python, no Git, and works on low-end laptops, Chromebooks, or iPads.
                * **Switching back and forth**: Instant! They can research and analyze on their desktop monitor, then walk outside and monitor on mobile.
                * **Setup Required**: None! Simply open the link.
                """)
            )

        with st.expander("Option 2: Dedicated Local PC Engine + Cloud Failover (🖥️ 5-Minute Setup)", expanded=True):
            st.markdown(
                textwrap.dedent("""
                If your friend wants their own computer hardware to be the **Execution Leader** (running the 3-minute background scanner, with automated failover when their PC turns off):
                
                ##### 📋 5-Minute Setup Instructions:
                1. **Clone the Repository**:
                ```bash
                git clone https://github.com/shriharinair-create/finvision.git
                cd finvision
                ```
                2. **Install Dependencies**:
                ```bash
                pip install -r requirements.txt
                ```
                3. **Launch Desktop Terminal**:
                ```bash
                streamlit run app.py
                ```
                4. **Connect Their Own Phone**:
                   * *Local Wi-Fi*: Connect their phone to their home network and navigate to `http://<THEIR-PC-IP>:8501`.
                   * *Private Cloud Fork*: They can fork your GitHub repository and deploy their own free instance on [Streamlit Cloud](https://share.streamlit.io) in 2 clicks. That gives them their own private cloud relay tied strictly to their PC's heartbeat!
                """)
            )

        st.markdown("---")
        st.markdown("#### 🔐 Bank-Grade Security & Per-User Credential Vault")
        st.markdown(
            "When multiple people use FinVision—especially with real brokerage accounts—**credential security, "
            "privacy, and financial isolation are non-negotiable**."
        )

        sec_col1, sec_col2 = st.columns(2)
        with sec_col1:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px; height:100%;">
                    <div style="color:#58A6FF; font-weight:700; font-size:15px; margin-bottom:6px;">👤 Profile PIN & Data Privacy</div>
                    <div style="font-size:13px; color:#C9D1D9; line-height:1.5;">
                        • Each user profile is secured by a private <strong>4-to-6 digit PIN</strong>.<br>
                        • PINs are stored as salted cryptographic hashes (<code>PBKDF2-HMAC-SHA256</code>) — never in plaintext.<br>
                        • Prevents friends from viewing each other's capital, trade journal, or active positions.
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
        with sec_col2:
            st.markdown(
                textwrap.dedent("""
                <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:14px; height:100%;">
                    <div style="color:#00E676; font-weight:700; font-size:15px; margin-bottom:6px;">🔑 Zero-Knowledge AES-256 Broker Vault</div>
                    <div style="font-size:13px; color:#C9D1D9; line-height:1.5;">
                        • Broker API keys (Zerodha Kite, Upstox, Groww) are encrypted at rest with <strong>AES-256-GCM</strong>.<br>
                        • The decryption key is derived strictly from that <strong>user's personal PIN</strong>.<br>
                        • Keys exist <strong>only in volatile RAM</strong> during an active session and vanish when the tab is closed.
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )

        st.markdown(
            textwrap.dedent("""
            #### 🛡️ Institutional Guardrails & Fail-Safe Protection:
            * **Simulation Mode Guarantee**: By default, FinVision runs in **100% Risk-Free Paper Trading**. No broker credentials, API keys, or banking details are ever required to simulate trades or test custom watchlists.
            * **Max Daily Loss Kill-Switch**: If an account drops by more than the user's defined risk limit (e.g. 2% in a day), all automated trading is permanently halted for the day.
            * **Per-Order Capital Caps**: Hard ceiling on the maximum ₹ amount deployed per trade to prevent fat-finger or sizing errors.
            * **Local PC Isolation**: When your friend runs Option 2 on their own PC, their broker credentials **never leave their machine**—they stay strictly on `localhost` without ever touching the cloud or your server.
            """)
        )

    # ── TAB 5: BSE & Dual-Exchange ────────────────────────────────────────────
    with tabs[4]:
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

    # ── TAB 6: Tax & GTT Order Math ───────────────────────────────────────────
    with tabs[5]:
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

    # ── TAB 7: Wealth Multiplier ──────────────────────────────────────────────
    with tabs[6]:
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

    # ── TAB 8: AI Autopsy & Academy ───────────────────────────────────────────
    with tabs[7]:
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

    # ── TAB 9: API & MCP Servers ──────────────────────────────────────────────
    with tabs[8]:
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

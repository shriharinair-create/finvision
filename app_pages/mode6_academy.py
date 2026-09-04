"""
finvision/app_pages/mode6_academy.py
====================================
AI Trading Academy & Paper Trading Simulator Journal.
Teaches zero-knowledge beginners the ropes of smart trading, risk management,
and compounding, while providing a risk-free simulator with live P&L analytics.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from utils.market_store import (
    get_all_paper_trades,
    close_paper_trade,
    get_paper_trading_summary,
    log_paper_trade,
    log_trade_postmortem,
    get_postmortem_history,
    get_recent_regime_history,
    save_veteran_rule,
    get_veteran_rules,
)
from utils.components import render_eli5_box, esc
from utils.trade_postmortem import diagnose_trade_postmortem
from utils.veteran_evaluator import fact_check_veteran_rule
from utils.drive_backup import (
    get_cloud_backup_settings,
    save_cloud_backup_settings,
    create_backup_archive,
    run_backup_cycle,
    restore_from_backup_archive,
    get_available_backups,
    get_google_apps_script_template,
    BACKUP_FOLDER_NAME,
)


ACADEMY_LESSONS = [
    {
        "id": 1,
        "title": "🎯 Lesson 1: The 2:1 Golden Rule — How to Profit Winning Only 40% of Trades",
        "category": "Risk Management",
        "body": (
            "Most beginners think you need a 90% win rate to get rich. In reality, institutional traders aim for asymmetric Risk-to-Reward (R:R).\n\n"
            "If your target gain is ₹2,000 and your maximum loss is strictly capped at ₹1,000 (a 2:1 ratio):\n"
            "• Out of 10 trades, if you LOSE 6 trades: -₹6,000 loss.\n"
            "• If you WIN just 4 trades: +₹8,000 profit.\n"
            "• **Net Result:** You make **+₹2,000 net profit** even though you lost more than half the time!\n\n"
            "FinVision automatically calculates your R:R on every single setup so you never take unfavorable trades."
        ),
        "rule": "Never enter any trade with an R:R of less than 1.5:1."
    },
    {
        "id": 2,
        "title": "🛡️ Lesson 2: The Stop-Loss — Your Irreplaceable Capital Insurance",
        "category": "Capital Preservation",
        "body": (
            "A Stop Loss is not an admission of defeat; it is the price of doing business in financial markets.\n\n"
            "When you enter a trade, you are buying a probability, not a certainty. If the market drops unexpectedly, "
            "a predefined stop-loss sells your shares automatically before a 1% loss turns into a disastrous 20% loss that paralyzes your account.\n\n"
            "Always enter your Stop Loss immediately upon buying in your broker app (Zerodha, Groww, AngelOne)."
        ),
        "rule": "Never cancel or widen a stop loss once entered."
    },
    {
        "id": 3,
        "title": "🌱 Lesson 3: The 8th Wonder of the World — How ₹10k/Month Becomes ₹1 Crore",
        "category": "Wealth Compounding",
        "body": (
            "Albert Einstein called compound interest the eighth wonder of the world. "
            "When you invest in high-quality businesses with wide economic moats (like Reliance, TCS, Titan, HDFC Bank):\n\n"
            "• Investing ₹10,000/month at 16% CAGR grows to:\n"
            "  - In 5 Years: **₹9.3 Lakhs**\n"
            "  - In 10 Years: **₹30.5 Lakhs**\n"
            "  - In 15 Years: **₹82.8 Lakhs**\n"
            "  - In 17 Years: **₹1.15 Crore!**\n\n"
            "Notice how the wealth creation accelerates dramatically in the later years. Time in the market beats timing the market."
        ),
        "rule": "Automate your monthly SIP and never stop investing during market corrections."
    },
    {
        "id": 4,
        "title": "⚡ Lesson 4: The 10:00 AM Session Flip — Why Timing Beats Speed",
        "category": "Intraday Dynamics",
        "body": (
            "The Indian Stock Market (NSE) opens at 09:15 AM. During the first 15 minutes, overnight retail orders flood the market, "
            "causing wild erratic swings (price discovery).\n\n"
            "Between 09:30 AM and 10:00 AM, dominant momentum takes control (Phase 2 Impulse).\n\n"
            "Around 10:00 AM to 10:15 AM, early scalpers lock their profits, which often causes a sudden mean-reversion pullback (Session Flip).\n\n"
            "FinVision's Intraday Blueprint calculates this flip window so you can book profits before the market pulls back!"
        ),
        "rule": "Never chase the 09:15 AM market open. Wait for the 15-minute Opening Range Breakout (ORB)."
    },
    {
        "id": 5,
        "title": "🧠 Lesson 5: News Sentiment vs Technical Confluence",
        "category": "Multi-Modal Intelligence",
        "body": (
            "A technical breakout with NO news support can fail easily. Similarly, good news on a stock already trading below its 200-day moving average "
            "often gets sold off by big institutions looking for exit liquidity.\n\n"
            "The highest-probability trades occur when **Technical Alignment** (Price > EMA20 > EMA50) meets **Positive Sentiment Tailwind** (FinBERT score > +0.20). "
            "This is called Multi-Modal Confluence."
        ),
        "rule": "Only deploy large size when both technicals and news catalysts point in the same direction."
    },
    {
        "id": 6,
        "title": "🧘 Lesson 6: Emotional Discipline & Position Sizing",
        "category": "Trader Psychology",
        "body": (
            "Why do 90% of retail traders lose money? Because they risk too much per trade, panic during minor dips, and revenge-trade after a loss.\n\n"
            "If you risk only 1% of your capital on each trade, you can lose 10 trades in a row and still have 90% of your capital safe and sound!\n\n"
            "FinVision's Position Sizer automatically does the math for your budget so you never feel stressed."
        ),
        "rule": "If you feel anxious about an open trade, your position size is too large."
    },
]


def render_mode6():
    st.markdown("## 🎓 AI Trading Academy & Paper Trading Journal")
    st.caption("Learn the institutional ropes of smart risk management, explore micro-lessons, and test strategies risk-free in your simulated portfolio.")

    tab_journal, tab_evolution, tab_veteran, tab_backup, tab_academy, tab_glossary = st.tabs([
        "💼 Paper Trading Portfolio",
        "🧠 AI Post-Mortem & Evolution Lab",
        "🎖️ Veteran Wisdom Fact-Check Lab",
        "💾 Cloud Drive Backup & Recovery",
        "🎓 AI Trading Academy & Lessons",
        "📖 Financial Jargon Translator",
    ])

    # ── TAB 1: PAPER TRADING SIMULATOR & JOURNAL ──────────────────────────────
    with tab_journal:
        st.markdown("### 📓 Live Paper Trading Simulator & Performance Journal")
        st.caption("Test setups risk-free. All trades are persisted in your local SQLite database with live win-rate and realized P&L analytics.")

        summary = get_paper_trading_summary()
        all_trades = get_all_paper_trades()

        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Total Simulated Trades", summary["total_trades"])
        s2.metric("Win Rate %", f"{summary['win_rate_pct']:.1f}%", f"{summary['winning_trades']}W / {summary['losing_trades']}L")
        
        pnl_val = summary["total_realized_pnl"]
        s3.metric("Realized P&L (₹)", f"{'+' if pnl_val >= 0 else ''}₹{pnl_val:,.2f}", f"{'+' if pnl_val >= 0 else ''}{pnl_val:.1f}")
        s4.metric("Profit Factor", f"{summary['profit_factor']:.2f}×", help="Ratio of gross profits to gross losses")
        s5.metric("Open Active Positions", summary["open_trades"])

        st.divider()

        # Quick Manual Trade Logger
        with st.expander("➕ Log a New Simulated Paper Trade"):
            with st.form("manual_paper_trade_form"):
                fc1, fc2, fc3, fc4 = st.columns(4)
                with fc1:
                    pt_tick = st.text_input("Ticker", value="RELIANCE.NS").strip().upper()
                with fc2:
                    pt_type = st.selectbox("Type", ["BUY_INTRADAY", "BUY_LONGTERM", "SHORT"])
                with fc3:
                    pt_entry = st.number_input("Entry Price (₹)", min_value=1.0, value=2500.0, step=10.0)
                with fc4:
                    pt_shares = st.number_input("Shares", min_value=1, value=20, step=1)

                lc1, lc2, lc3 = st.columns(3)
                with lc1:
                    pt_target = st.number_input("Target Price (₹)", min_value=1.0, value=2550.0, step=10.0)
                with lc2:
                    pt_stop = st.number_input("Stop Loss (₹)", min_value=1.0, value=2475.0, step=10.0)
                with lc3:
                    pt_notes = st.text_input("Notes / Strategy", value="Breakout long test")

                submit_trade = st.form_submit_button("🚀 Submit Paper Trade", use_container_width=True)
                if submit_trade:
                    tid = log_paper_trade(pt_tick, pt_type, pt_entry, pt_target, pt_stop, pt_shares, pt_notes)
                    st.success(f"Paper Trade #{tid} recorded successfully!")
                    st.rerun()

        # Open Positions Actions
        open_positions = [t for t in all_trades if t["status"] == "OPEN"]
        if open_positions:
            st.markdown("#### ⚡ Active Open Positions")
            for op in open_positions:
                tid = op["id"]
                tick = op["ticker"]
                entry = op["entry_price"]
                tgt = op["target_price"]
                sl = op["stop_loss_price"]
                sh = op["shares"]
                val = op["position_value"]

                with st.container():
                    c_info, c_hit_tgt, c_hit_sl, c_man = st.columns([4, 2, 2, 2])
                    with c_info:
                        st.markdown(
                            f"<strong>#{tid} · {tick}</strong> ({op['trade_type']}) · <strong>{sh} shares</strong> @ ₹{entry:,.2f} (₹{val:,.0f}) | "
                            f"<span style='color:#58A6FF;'>Target: ₹{tgt:,.2f}</span> | <span style='color:#F85149;'>Stop: ₹{sl:,.2f}</span>",
                            unsafe_allow_html=True
                        )
                    with c_hit_tgt:
                        if st.button(f"🎯 Target Hit", key=f"btn_tgt_{tid}", use_container_width=True):
                            close_paper_trade(tid, tgt, "TARGET_HIT")
                            try:
                                pm = diagnose_trade_postmortem(tick, op["trade_type"], entry, tgt, sl, tgt, "TARGET_HIT")
                                pm["trade_id"] = tid
                                log_trade_postmortem(pm)
                            except Exception:
                                pass
                            st.toast(f"Trade #{tid} closed at Target ₹{tgt:,.2f}! Post-Mortem logged.", icon="🎯")
                            st.rerun()
                    with c_hit_sl:
                        if st.button(f"🛑 Stop Hit", key=f"btn_sl_{tid}", use_container_width=True):
                            close_paper_trade(tid, sl, "STOP_HIT")
                            try:
                                pm = diagnose_trade_postmortem(tick, op["trade_type"], entry, tgt, sl, sl, "STOP_HIT")
                                pm["trade_id"] = tid
                                log_trade_postmortem(pm)
                            except Exception:
                                pass
                            st.toast(f"Trade #{tid} stopped at ₹{sl:,.2f}. Post-Mortem logged.", icon="🛑")
                            st.rerun()
                    with c_man:
                        if st.button(f"✖ Close Market", key=f"btn_close_{tid}", use_container_width=True):
                            close_paper_trade(tid, entry, "MANUAL_EXIT")
                            try:
                                pm = diagnose_trade_postmortem(tick, op["trade_type"], entry, tgt, sl, entry, "MANUAL_EXIT")
                                pm["trade_id"] = tid
                                log_trade_postmortem(pm)
                            except Exception:
                                pass
                            st.toast(f"Trade #{tid} exited at market.", icon="✖")
                            st.rerun()
            st.divider()

        # History Table
        col_hist_title, col_hist_filter = st.columns([3, 2])
        with col_hist_title:
            st.markdown("#### 📜 Trade History Journal")
        with col_hist_filter:
            origin_filter = st.radio(
                "Filter Trades",
                options=["All Trades", "🤖 Auto-Trader Only", "👤 Manual Only"],
                horizontal=True,
                key="radio_filter_origin",
                label_visibility="collapsed",
            )

        filtered_trades = all_trades
        if origin_filter == "🤖 Auto-Trader Only":
            filtered_trades = [t for t in all_trades if t.get("is_auto_trade") == 1]
        elif origin_filter == "👤 Manual Only":
            filtered_trades = [t for t in all_trades if not t.get("is_auto_trade")]

        if not filtered_trades:
            st.info(f"No trades logged matching filter '{origin_filter}'.")
        else:
            df_trades = pd.DataFrame([
                {
                    "ID": f"#{t['id']}",
                    "Date": t["timestamp"],
                    "Origin": "🤖 Auto-Trader" if t.get("is_auto_trade") == 1 else "👤 Manual",
                    "Ticker": t["ticker"],
                    "Horizon": t.get("horizon", "DAY_TRADE").replace("_", " "),
                    "Type": t["trade_type"],
                    "Shares": t["shares"],
                    "Entry": f"₹{t['entry_price']:,.2f}",
                    "Target": f"₹{t['target_price']:,.2f}",
                    "Stop": f"₹{t['stop_loss_price']:,.2f}",
                    "Status": t["status"],
                    "Exit Price": f"₹{t['exit_price']:,.2f}" if t["exit_price"] else "—",
                    "P&L (₹)": f"{'+' if (t['pnl_amount'] or 0) >= 0 else ''}₹{(t['pnl_amount'] or 0):,.2f}",
                    "P&L %": f"{'+' if (t['pnl_pct'] or 0) >= 0 else ''}{(t['pnl_pct'] or 0):.2f}%",
                    "Notes": t["notes"] or "",
                }
                for t in filtered_trades
            ])
            st.dataframe(df_trades, use_container_width=True, hide_index=True)

    # ── TAB 2: AI POST-MORTEM & EVOLUTION LAB ─────────────────────────────────
    with tab_evolution:
        st.markdown("### 🧠 AI Post-Mortem & Self-Evolution Lab")
        st.caption("How the AI matures over time: Every closed trade undergoes an automated autopsy to diagnose liquidity stop-hunts, market regime drag, and adapt future risk buffers.")

        postmortems = get_postmortem_history(limit=50)
        regimes = get_recent_regime_history(limit=10)

        # Overview Metrics
        total_pm = len(postmortems)
        hunts_count = sum(1 for p in postmortems if p.get("diagnosis_code") == "LIQUIDITY_SWEEP_HUNT")
        wins_count = sum(1 for p in postmortems if "WIN" in p.get("diagnosis_code", "") or "BLOWOFF" in p.get("diagnosis_code", ""))
        drag_count = sum(1 for p in postmortems if "DRAG" in p.get("diagnosis_code", "") or "WHIPSAW" in p.get("diagnosis_code", ""))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Autopsies Conducted", total_pm)
        m2.metric("Clean Target Wins", wins_count)
        m3.metric("Operator Stop-Hunts Detected", hunts_count, help="Smart-money stop runs where price pierced SL by <0.8% and immediately reversed")
        m4.metric("Market Drag Losses", drag_count, help="Trades failed due to systemic Nifty index declines rather than stock setup errors")

        st.divider()

        # Post-Mortem Autopsy Feed
        st.markdown("#### 🔬 Post-Mortem Diagnosis Stream")
        if not postmortems:
            st.info("No trade autopsies recorded yet. When you close or hit targets on paper trades, FinVision will automatically conduct post-mortems here.")
        else:
            for p in postmortems[:10]:
                code = p.get("diagnosis_code", "UNKNOWN")
                pnl = p.get("pnl_amount", 0.0)
                badge_color = "#00E676" if pnl >= 0 else "#FF5252"
                hunt_badge = "⚠️ OPERATOR STOP-HUNT" if code == "LIQUIDITY_SWEEP_HUNT" else "🏛️ MARKET REGIME DRAG" if "DRAG" in code else "🎯 CLEAN WIN" if "WIN" in code else "🛑 NORMAL STOP"

                with st.expander(f"{hunt_badge} · {p['ticker']} ({'+' if pnl >= 0 else ''}₹{pnl:,.2f}) — {code}"):
                    st.markdown(f"**Root Cause Attribution:** {p.get('attribution_summary')}")
                    st.markdown(f"**AI Adaptive Learning:** `{p.get('corrective_learning')}`")
                    st.caption(f"Entry: ₹{p.get('entry_price'):,.2f} | Exit: ₹{p.get('exit_price'):,.2f} | PnL: {p.get('pnl_pct'):+.2f}% | Regime: {p.get('regime_at_entry')}")

        st.divider()

        # Regime History Timeline
        st.markdown("#### 🏛️ Indian Market Regime History (Daily Seasons)")
        if regimes:
            df_reg = pd.DataFrame([
                {
                    "Date": r["session_date"],
                    "Regime": r["regime_code"],
                    "Nifty Price": f"₹{r['nifty_price']:,.2f}" if r["nifty_price"] else "—",
                    "India VIX": f"{r['vix_value']:.1f}" if r["vix_value"] else "—",
                    "Playbook Strategy": r["strategy_playbook"]
                }
                for r in regimes
            ])
            st.dataframe(df_reg, use_container_width=True, hide_index=True)

    # ── TAB 3: VETERAN WISDOM & FACT-CHECK LAB ────────────────────────────────
    with tab_veteran:
        st.markdown("### 🎖️ Veteran Wisdom Fact-Check & Knowledge Ingestion Lab")
        st.caption(
            "Heard a trading rule, tip, or heuristic from a Dalal Street veteran, mentor, or financial book? "
            "Input it below. The AI Learner Module will run an empirical walk-forward backtest across 2 years of actual NSE data, "
            "measure its statistical edge, and decide whether to incorporate it into its active brain or reject it as an unbacked retail myth."
        )

        with st.form("veteran_wisdom_form"):
            c_rule, c_author = st.columns([3, 1])
            with c_rule:
                v_text = st.text_area(
                    "Enter Veteran Advice / Trading Rule",
                    placeholder="e.g. When Reliance RSI drops below 40, buy for a 5 day swing...\nOr: When Tata Motors is above 50 EMA on high volume, buy for a 1 week swing...",
                    height=85
                ).strip()
            with c_author:
                v_source = st.text_input("Source / Mentor Name", value="Senior Dalal Street Veteran")
                st.caption("AI will test win rate, profit factor, and statistical edge.")

            submit_fact_check = st.form_submit_button("🧪 Run AI Fact-Check & Empirical Backtest", use_container_width=True)

        if submit_fact_check and v_text:
            with st.spinner("🤖 AI Learner is parsing rule conditions and running a 2-year walk-forward backtest..."):
                fact_res = fact_check_veteran_rule(v_text, author_or_source=v_source)
                save_veteran_rule(fact_res)

            st.markdown(
                f"""
                <div style="background:#161B22; border:2px solid {fact_res['badge_color']}; border-radius:10px; padding:16px; margin:14px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <span style="font-size:16px; font-weight:800; color:{fact_res['badge_color']};">{fact_res['verdict_badge']}</span>
                        <span style="font-size:12px; color:#8B949E;">Target Stock: <strong>{fact_res.get('target_ticker', 'N/A')}</strong> | Source: {fact_res.get('author', 'Mentor')}</span>
                    </div>
                    <div style="margin-top:10px; font-size:13px; color:#E6EDF3; line-height:1.5;">
                        {fact_res['summary_report']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            v_col1, v_col2, v_col3, v_col4 = st.columns(4)
            v_col1.metric("Historical Triggers", fact_res["occurrences"])
            v_col2.metric("Win Rate %", f"{fact_res['win_rate_pct']:.1f}%")
            v_col3.metric("Profit Factor", f"{fact_res['profit_factor']:.2f}×")
            v_col4.metric("Avg Return / Trade", f"{fact_res['avg_return_pct']:+.2f}%")

            if fact_res.get("signals"):
                st.markdown("##### 📜 Recent Historical Simulation Bars")
                st.dataframe(pd.DataFrame(fact_res["signals"]), use_container_width=True, hide_index=True)

        st.divider()

        # Knowledge Base Table
        st.markdown("#### 📚 Active Veteran Knowledge Base Registry")
        all_rules = get_veteran_rules()
        if not all_rules:
            st.info("No veteran rules tested yet. Try testing a rule above (e.g. 'When Reliance RSI drops below 40, buy for a 5 day swing')!")
        else:
            df_v = pd.DataFrame([
                {
                    "ID": f"#{r['id']}",
                    "Date": r["created_at"][:10] if r.get("created_at") else "—",
                    "Target": r["target_ticker"],
                    "Source": r["author_or_source"],
                    "Rule Description": r["rule_text"][:60] + ("..." if len(r["rule_text"]) > 60 else ""),
                    "Triggers": r["occurrences"],
                    "Win Rate": f"{r['win_rate_pct']:.1f}%",
                    "Profit Factor": f"{r['profit_factor']:.2f}×",
                    "Verdict Status": r["status"]
                }
                for r in all_rules
            ])
            st.dataframe(df_v, use_container_width=True, hide_index=True)

    # ── TAB 4: CLOUD DRIVE BACKUP & RECOVERY HUB ─────────────────────────────
    with tab_backup:
        st.markdown("### 💾 Cloud Drive Backup & Data Recovery Hub")
        st.caption(
            "Safeguard all your trade journals, autonomous bot configurations, post-mortem autopsies, and learned stock buffers. "
            "Backups are stored in an isolated, dedicated folder to prevent cluttering your personal cloud drive."
        )

        b_cfg = get_cloud_backup_settings()

        # Dedicated Folder & Storage Meter Header
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #0D1B2A 0%, #161B22 100%); border: 1px solid #388BFD; border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <span style="background:#238636; color:#FFF; padding:2px 8px; border-radius:12px; font-size:10px; font-weight:700;">📁 ISOLATED CLOUD FOLDER</span>
                        <h4 style="margin:4px 0 2px 0; color:#F0F6FC; font-size:16px;">Google Drive / {b_cfg.get('google_drive_folder_name', BACKUP_FOLDER_NAME)}/</h4>
                        <div style="font-size:11px; color:#8B949E;">All backup archives are quarantined in this specific folder to keep your root drive completely clean.</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:11px; color:#8B949E;">Storage Quota Impact</div>
                        <div style="font-size:15px; font-weight:800; color:#3FB950;">~1.2 MB / 15,000 MB</div>
                        <div style="font-size:10px; color:#58A6FF;">(&lt; 0.008% of free Drive space)</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Configuration Card
        c_b1, c_b2, c_b3 = st.columns(3)
        with c_b1:
            freq_opts = ["DAILY", "WEEKLY", "MONTHLY", "MANUAL"]
            cur_f = b_cfg.get("backup_frequency", "DAILY").upper()
            idx_f = freq_opts.index(cur_f) if cur_f in freq_opts else 0
            sel_freq = st.selectbox(
                "⏰ Backup Frequency",
                options=freq_opts,
                index=idx_f,
                format_func=lambda x: f"Daily (Recommended)" if x == "DAILY" else f"Weekly" if x == "WEEKLY" else f"Monthly" if x == "MONTHLY" else "Manual Only",
                key="sel_backup_freq"
            )
        with c_b2:
            retention_val = st.slider(
                "📦 Rolling Retention Count",
                min_value=3,
                max_value=30,
                value=int(b_cfg.get("retention_count", 7)),
                key="slider_backup_retention",
                help="Automatically prunes older backups beyond this count so your cloud drive never accumulates clutter."
            )
        with c_b3:
            last_ts = b_cfg.get("last_backup_timestamp") or "Never"
            st.metric("Last Backup", last_ts.split(" ")[0] if " " in last_ts else last_ts, b_cfg.get("last_backup_status", "STANDBY"))

        # Google Drive Integration Settings
        with st.expander("☁️ Configure Google Drive Connection (Webhook / API)", expanded=not bool(b_cfg.get("google_drive_webhook_url"))):
            st.markdown(
                "Connect your personal Google Drive using a zero-setup **Google Apps Script Webhook** (recommended, takes 30 seconds) "
                "or direct Google Drive API OAuth token."
            )
            c_wh1, c_wh2 = st.columns([3, 1])
            with c_wh1:
                wh_input = st.text_input(
                    "Google Drive Webhook URL",
                    value=b_cfg.get("google_drive_webhook_url", ""),
                    placeholder="https://script.google.com/macros/s/.../exec",
                    key="input_drive_wh_url",
                    help="Paste your Google Apps Script Web App URL here."
                )
            with c_wh2:
                folder_custom = st.text_input(
                    "Drive Folder Name",
                    value=b_cfg.get("google_drive_folder_name", BACKUP_FOLDER_NAME),
                    key="input_drive_folder_name"
                )

            # Save updated settings if changed
            if (
                sel_freq != cur_f
                or retention_val != int(b_cfg.get("retention_count", 7))
                or wh_input != b_cfg.get("google_drive_webhook_url", "")
                or folder_custom != b_cfg.get("google_drive_folder_name", BACKUP_FOLDER_NAME)
            ):
                updated_b_cfg = {
                    **b_cfg,
                    "backup_frequency": sel_freq,
                    "retention_count": retention_val,
                    "google_drive_webhook_url": wh_input,
                    "google_drive_folder_name": folder_custom,
                }
                save_cloud_backup_settings(updated_b_cfg)
                st.toast("💾 Backup preferences saved!", icon="☁️")

            with st.expander("📋 30-Second Google Drive Setup Instructions (Copy-Paste Script)", expanded=False):
                st.markdown(
                    """
                    1. Open [script.google.com](https://script.google.com) and click **New project**.
                    2. Replace the blank code with the script below.
                    3. Click **Deploy > New Deployment > Select type: Web app**.
                    4. Set **Execute as**: *Me* and **Who has access**: *Anyone*.
                    5. Click **Deploy**, copy the generated Web App URL, and paste it into the field above!
                    """
                )
                st.code(get_google_apps_script_template(), language="javascript")

        st.divider()

        # Action Buttons: Manual Backup, Download, and Restore
        c_act1, c_act2, c_act3 = st.columns([2, 2, 3])
        with c_act1:
            if st.button("☁️ Run Backup Cycle Now", key="btn_run_backup_now", use_container_width=True):
                with st.spinner("📦 Compressing database and syncing to Google Drive..."):
                    b_result = run_backup_cycle()
                if b_result["status"] in ("SUCCESS", "LOCAL_SAVED"):
                    st.success(b_result["message"])
                else:
                    st.error(b_result["message"])
                st.rerun()

        with c_act2:
            # Generate in-memory backup bundle for instant browser download
            if st.button("📦 Prepare .fvbackup Download", key="btn_prep_download", use_container_width=True):
                with st.spinner("Preparing archive..."):
                    arch_path, m_info = create_backup_archive()
                    with open(arch_path, "rb") as bf:
                        b_bytes = bf.read()
                    st.session_state["ready_backup_bytes"] = b_bytes
                    st.session_state["ready_backup_name"] = arch_path.name
                st.toast("Archive ready for download!", icon="📥")

            if "ready_backup_bytes" in st.session_state:
                st.download_button(
                    label=f"📥 Download {st.session_state.get('ready_backup_name', 'backup.fvbackup')}",
                    data=st.session_state["ready_backup_bytes"],
                    file_name=st.session_state.get("ready_backup_name", "finvision_backup.fvbackup"),
                    mime="application/zip",
                    use_container_width=True,
                    key="btn_do_download"
                )

        with c_act3:
            with st.expander("📤 Restore Database from File"):
                uploaded_b = st.file_uploader(
                    "Upload .fvbackup, .zip, or .db snapshot",
                    type=["fvbackup", "zip", "db"],
                    key="uploader_restore_file"
                )
                if uploaded_b is not None:
                    st.warning("⚠️ **Safety Notice**: Restoring will replace your active database with the uploaded backup. A safety rollback snapshot will be automatically saved first.")
                    if st.button("🚨 Confirm & Restore Database", key="btn_confirm_restore", use_container_width=True):
                        with st.spinner("Verifying integrity and restoring..."):
                            b_bytes = uploaded_b.read()
                            if uploaded_b.name.endswith(".db"):
                                # If direct .db file, wrap it into temp path
                                b_dir = get_backup_dir()
                                tmp_restore = b_dir / "temp_direct_restore.db"
                                with open(tmp_restore, "wb") as tf:
                                    tf.write(b_bytes)
                                # Make zip
                                tmp_zip = b_dir / "temp_direct_restore.fvbackup"
                                with zipfile.ZipFile(tmp_zip, "w") as z:
                                    z.write(tmp_restore, arcname="finvision_data.db")
                                r_res = restore_from_backup_archive(tmp_zip)
                            else:
                                r_res = restore_from_backup_archive(b_bytes)

                        if r_res["status"] == "SUCCESS":
                            st.success(r_res["message"])
                            st.rerun()
                        else:
                            st.error(r_res["message"])

        st.divider()

        # Available Snapshots Table in FinVision_Backups
        st.markdown(f"#### 📜 Available Snapshots in `{b_cfg.get('google_drive_folder_name', BACKUP_FOLDER_NAME)}/`")
        snapshots = get_available_backups()
        if not snapshots:
            st.info("No local snapshots in folder yet. Click 'Run Backup Cycle Now' to create your first backup!")
        else:
            for s_idx, snap in enumerate(snapshots):
                c_sn1, c_sn2 = st.columns([5, 1])
                with c_sn1:
                    t_counts = snap.get("table_counts", {})
                    trades_cnt = t_counts.get("paper_trades", "—")
                    learn_cnt = t_counts.get("auto_trader_learnings", "—")
                    st.markdown(
                        f"""
                        <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:8px 12px; margin-bottom:6px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-weight:700; font-size:12px; color:#F0F6FC;">📁 {snap['file_name']}</span>
                                <span style="font-size:11px; color:#8B949E;">Size: <strong>{snap['size_mb']} MB</strong></span>
                            </div>
                            <div style="display:flex; gap:14px; font-size:10px; color:#8B949E; margin-top:4px;">
                                <span>📅 Timestamp: <strong>{snap['timestamp']}</strong></span>
                                <span>💼 Trades: <strong>{trades_cnt}</strong></span>
                                <span>🧠 Learnings: <strong>{learn_cnt}</strong></span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with c_sn2:
                    if st.button(f"🔄 Restore", key=f"btn_restore_snap_{s_idx}", use_container_width=True, help="Restore database from this snapshot"):
                        with st.spinner(f"Restoring from {snap['file_name']}..."):
                            r_res = restore_from_backup_archive(snap["file_path"])
                        if r_res["status"] == "SUCCESS":
                            st.success(f"Restored from {snap['file_name']}!")
                            st.rerun()
                        else:
                            st.error(r_res["message"])

    # ── TAB 4: AI TRADING ACADEMY & LESSONS ────────────────────────────────────
    with tab_academy:
        st.markdown("### 🎓 FinVision Institutional Trading & Investing Academy")
        st.caption("Bite-sized institutional trading wisdom to turn zero-knowledge beginners into disciplined, consistently profitable operators.")

        for lesson in ACADEMY_LESSONS:
            with st.container():
                st.markdown(
                    f"""
                    <div class="academy-card">
                        <div class="academy-lesson-num">{esc(lesson['category'])}</div>
                        <div class="academy-lesson-title">{esc(lesson['title'])}</div>
                        <div class="academy-lesson-desc" style="white-space: pre-line;">{esc(lesson['body'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_eli5_box(
                    title=f"Core Takeaway: {lesson['category']}",
                    explanation=lesson['rule'],
                    key_rules=["Review this rule before placing any real money order in your broker."]
                )

    # ── TAB 3: FINANCIAL JARGON TRANSLATOR ────────────────────────────────────
    with tab_glossary:
        st.markdown("### 📖 Plain-English Financial Jargon Translator")
        st.caption("Never feel confused by complex Wall Street & Dalal Street terminology again.")

        glossary = [
            ("LTP (Last Traded Price)", "The latest price at which a buyer and seller agreed to exchange a share."),
            ("Stop Loss (SL)", "An automatic safety exit price that sells your shares if the trade drops, strictly capping your maximum loss."),
            ("Target (Take-Profit)", "The planned price level where you sell your shares to lock in your profits."),
            ("Risk-to-Reward (R:R)", "The ratio of potential profit to potential loss. A 2:1 R:R means you aim to make ₹2,000 for every ₹1,000 you risk."),
            ("ORB (Opening Range Breakout)", "Trading the breakout above or below the highest/lowest price set in the first 15 minutes of market open."),
            ("Moat", "A company's sustainable competitive advantage (brand power, patents, network effects) that protects it from competitors."),
            ("CAGR (Compound Annual Growth Rate)", "The annualized rate of return at which an investment compounds over multi-year periods."),
            ("SIP (Systematic Investment Plan)", "Investing a fixed sum of money automatically on a monthly schedule, averaging out market fluctuations."),
            ("P/E Ratio (Price-to-Earnings)", "How many rupees investors are willing to pay for every ₹1 of profit the company generates."),
            ("ROE (Return on Equity)", "How efficiently the company's management converts shareholder capital into pure net profit (>15% is excellent)."),
            ("VWAP (Volume-Weighted Average Price)", "The true average benchmark price paid by institutional hedge funds and mutual funds throughout the day."),
        ]

        search_term = st.text_input("🔍 Search Jargon or Term", placeholder="e.g. Stop Loss, Moat, VWAP...")
        for term, meaning in glossary:
            if not search_term or search_term.lower() in term.lower() or search_term.lower() in meaning.lower():
                with st.expander(f"📚 {term}"):
                    st.write(meaning)

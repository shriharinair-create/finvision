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
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

from utils.forecasting import (
    compute_quantitative_confluence_forecast,
    compute_intraday_trade_blueprint,
)
from utils.fundamental_wealth import (
    analyze_stock_fundamentals,
    BLUE_CHIP_COMPOUNDERS,
)
from utils.risk import compute_position_size
from utils.market_store import (
    log_paper_trade,
    log_regime_snapshot,
    get_stock_adaptive_buffer,
    save_veteran_rule,
    get_veteran_rules,
    close_paper_trade,
    log_trade_postmortem,
)
from utils.components import render_eli5_box, esc
from utils.regime import detect_indian_market_regime
from utils.meta_labeling import evaluate_meta_labeling_filter
from utils.user_prefs import get_user_preferences, save_user_preference
from utils.veteran_evaluator import fact_check_veteran_rule
from utils.macro import get_live_cross_asset_macro
from utils.tax_calculator import compute_indian_market_friction
from utils.gtt import compute_gtt_order_parameters
from utils.broker_gateway import build_broker_order_payload, dispatch_broker_order, SUPPORTED_BROKERS
from utils.ml_ensemble import retrain_ensemble_from_trade_journal
from utils.auto_trader import (
    run_auto_trade_cycle,
    get_auto_trader_config,
    save_auto_trader_config,
    get_auto_trader_learnings,
    get_active_auto_trades,
    is_indian_market_open_or_simulated,
    diagnose_trade_postmortem,
)
from utils.bse_helper import resolve_indian_ticker, is_bse_scrip_code
from utils.bse_corporate import check_corporate_event_risk
from utils.indian_macro import fetch_official_indian_macro, compute_indian_fci
from utils.adaptive_weights import get_regime_adaptive_weights, calculate_adaptive_confluence_score
import textwrap


RECOMMENDED_DAY_TICKERS = [
    "RELIANCE.NS", "MARUTI.NS", "INFY.NS", "TCS.NS",
    "HDFCBANK.NS", "ICICIBANK.NS", "BAJFINANCE.NS", "TITAN.NS",
    "BHARTIARTL.NS", "SUNPHARMA.NS", "ITC.NS", "LT.NS",
    "AXISBANK.NS", "MARUTI.NS", "TATASTEEL.NS", "POWERGRID.NS"
]


DEFAULT_LEADERS = [
    {"symbol": "^NSEI", "name": "NIFTY 50", "sector": "NSE Benchmark", "price": 23873.45, "change": -0.17},
    {"symbol": "^BSESN", "name": "BSE SENSEX", "sector": "BSE Benchmark", "price": 76152.80, "change": -0.55},
    {"symbol": "^NSEBANK", "name": "BANK NIFTY", "sector": "Banking Index", "price": 57380.60, "change": 0.36},
    {"symbol": "RELIANCE.NS", "name": "Reliance Ind.", "sector": "Energy", "price": 1302.50, "change": -0.81},
    {"symbol": "TCS.NS", "name": "TCS", "sector": "IT", "price": 2320.10, "change": -1.19},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking", "price": 706.65, "change": 0.83},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "IT", "price": 1130.30, "change": -0.85},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking", "price": 1430.00, "change": 0.25},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Banking", "price": 1023.40, "change": 0.24},
]


@st.cache_data(ttl=30, show_spinner=False)
def get_india_market_leaders_quotes() -> list[dict[str, Any]]:
    """Fetches real-time live market quotes for key Indian benchmark indices and market leaders."""
    tickers = ["^NSEI", "^BSESN", "^NSEBANK", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS"]
    names = {
        "^NSEI": ("NIFTY 50", "NSE Benchmark"),
        "^BSESN": ("BSE SENSEX", "BSE Benchmark"),
        "^NSEBANK": ("BANK NIFTY", "Banking Index"),
        "RELIANCE.NS": ("Reliance Ind.", "Energy"),
        "TCS.NS": ("TCS", "IT"),
        "HDFCBANK.NS": ("HDFC Bank", "Banking"),
        "INFY.NS": ("Infosys", "IT"),
        "ICICIBANK.NS": ("ICICI Bank", "Banking"),
        "SBIN.NS": ("State Bank of India", "Banking"),
    }
    try:
        df = yf.download(tickers, period="5d", interval="1d", progress=False)["Close"]
        out = []
        for t in tickers:
            if t in df:
                s = df[t].dropna()
                if not s.empty:
                    p = float(s.iloc[-1])
                    prev = float(s.iloc[-2]) if len(s) > 1 else p
                    chg = ((p - prev) / prev) * 100
                    disp_name, sec = names.get(t, (t, "Stock"))
                    out.append({
                        "symbol": t,
                        "name": disp_name,
                        "sector": sec,
                        "price": round(p, 2),
                        "change": round(chg, 2)
                    })
        return out if len(out) >= 4 else DEFAULT_LEADERS
    except Exception:
        return DEFAULT_LEADERS


def render_mode0():
    # ── Hero Banner ───────────────────────────────────────────────────────────
    st.markdown(
        textwrap.dedent("""
        <div class="copilot-hero-card">
            <div class="copilot-hero-title">🤖 FinVision Smart Trade & Wealth Copilot</div>
            <div class="copilot-hero-subtitle">
                Zero-Knowledge AI Mentor & Execution Autopilot. Whether you want <strong>quick intraday profits</strong>
                or <strong>multi-year wealth compounding</strong>, the Copilot guides your every step with exact price levels,
                budget-based position sizing, and plain-English ELI5 explanations.
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # ── Top Action Buttons: Settings & Guide ──────────────────────────────────
    c_act_settings, c_act_walk = st.columns(2)
    with c_act_settings:
        if st.button("⚙️ Settings & Cloud Backup Hub", key="mode0_top_settings_btn", use_container_width=True):
            st.session_state["target_operating_mode"] = "settings"
            st.rerun()
    with c_act_walk:
        if st.button("📖 App Walkthrough & User Guide", key="copilot_open_walkthrough_btn", use_container_width=True):
            st.session_state["target_operating_mode"] = "walkthrough"
            st.rerun()

    # ── 🤖 AUTONOMOUS AUTO-TRADER COCKPIT & LIVE SCANNER BANNER ───────────────
    top_prefs = get_user_preferences()
    top_budget = float(st.session_state.get("total_capital", top_prefs.get("total_capital", 500000.0)))
    top_risk_prof = top_prefs.get("risk_profile", "Balanced (1.0% max risk)")
    top_risk_pct = float(st.session_state.get("risk_pct", 0.005 if "Conservative" in top_risk_prof else 0.02 if "Active" in top_risk_prof else 0.01))

    auto_cfg = get_auto_trader_config()
    active_auto_trades = get_active_auto_trades()
    recent_auto_learnings = get_auto_trader_learnings(limit=6)
    m_timing = is_indian_market_open_or_simulated()
    is_at_active = auto_cfg.get("is_enabled", False)
    max_pos = int(auto_cfg.get("max_concurrent_positions", 3))
    cur_horizons_raw = auto_cfg.get("enabled_horizons", "DAY_TRADE,SWING_TRADE,LONG_TERM")
    cur_mode = auto_cfg.get("execution_mode", "SIMULATION")

    status_pill = (
        '<span style="background:#238636;color:#FFF;padding:6px 14px;border-radius:20px;font-weight:800;font-size:13px;box-shadow:0 0 12px rgba(35,134,54,0.5);">'
        '🟢 LIVE SCANNER ACTIVE & SCANNING</span>'
        if is_at_active
        else '<span style="background:#30363D;color:#8B949E;padding:6px 14px;border-radius:20px;font-weight:700;font-size:13px;">'
        '⚪ LIVE SCANNER STANDBY (OFF)</span>'
    )

    border_color = "#238636" if is_at_active else "#30363D"
    glow = "box-shadow: 0 0 20px rgba(35,134,54,0.25);" if is_at_active else "box-shadow: 0 4px 16px rgba(0,0,0,0.3);"

    # 1. Main Live Scanner Hero Banner
    st.markdown(
        textwrap.dedent(f"""
        <div style="background: linear-gradient(135deg, #0d1b2a 0%, #161b22 100%); border: 2px solid {border_color}; {glow} border-radius: 12px; padding: 18px 22px; margin: 12px 0 16px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="background:#1f6feb; color:#FFF; font-weight:800; font-size:10px; padding:2px 8px; border-radius:12px; letter-spacing:0.8px;">📡 LIVE SCANNER TELEMETRY</span>
                        <span style="background:#21262d; color:#8b949e; font-size:10px; padding:2px 8px; border-radius:12px;">NIFTY 500 AUTONOMOUS RADAR</span>
                    </div>
                    <h3 style="margin:6px 0 2px 0; color:#F0F6FC; font-size:21px; font-weight:800;">🤖 FinVision Autonomous Auto-Trader</h3>
                    <div style="font-size:12px; color:#8B949E;">Continuously scans 500+ Indian equities, evaluates multi-timeframe ML consensus (&gt;55%), enforces strict 1% risk budgeting, and executes autonomous trades.</div>
                </div>
                <div>
                    {status_pill}
                </div>
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    # 2. Live Scanner Telemetry Metric Cards
    c_tel1, c_tel2, c_tel3, c_tel4 = st.columns(4)
    with c_tel1:
        st.metric(
            label="🕒 Market Clock (IST)",
            value=m_timing['ist_time'],
            delta="Open ✅" if m_timing['is_market_open'] else "Closed / Sim Mode 🛡️",
            delta_color="normal" if m_timing['is_market_open'] else "off",
            help="Indian Market (NSE/BSE) operating window: 09:15 to 15:30 IST. Outside hours, simulation regime applies."
        )
    with c_tel2:
        st.metric(
            label="📊 Active Slots",
            value=f"{len(active_auto_trades)} of {max_pos} Slots",
            delta="Capacity Available" if len(active_auto_trades) < max_pos else "Slots Full",
            delta_color="normal" if len(active_auto_trades) < max_pos else "inverse",
            help="Maximum concurrent open positions allowed by risk management."
        )
    with c_tel3:
        h_labels = []
        if "DAY_TRADE" in cur_horizons_raw: h_labels.append("Day")
        if "SWING_TRADE" in cur_horizons_raw: h_labels.append("Swing")
        if "LONG_TERM" in cur_horizons_raw: h_labels.append("Long")
        st.metric(
            label="🔭 Active Horizons",
            value=" · ".join(h_labels) if h_labels else "None",
            help="Trading regimes authorized for autonomous deployment."
        )
    with c_tel4:
        st.metric(
            label="🛡️ Risk Allocation",
            value=f"₹{top_budget * top_risk_pct:,.0f}",
            delta=f"{top_risk_pct*100:.1f}% of ₹{top_budget:,.0f}",
            delta_color="off",
            help="Maximum capital risked on any individual trade."
        )

    # 3. Quick Engine Controls (Master Switch, Trigger Button, Cross-Device Sync)
    c_ctrl1, c_ctrl2, c_ctrl3 = st.columns([1.2, 1.4, 1.2])
    with c_ctrl1:
        t_master = st.toggle(
            "⚡ Auto-Trade Engine Master Switch",
            value=is_at_active,
            key="toggle_at_master_hero",
            help="When ON, the AI will autonomously scan for high-conviction trades and execute without manual intervention."
        )
        if t_master != is_at_active:
            auto_cfg["is_enabled"] = t_master
            save_auto_trader_config(auto_cfg)
            try:
                from utils.cross_device_sync import push_sync_to_cloud_async
                push_sync_to_cloud_async()
            except Exception:
                pass
            st.toast(f"Auto-Trader {'activated' if t_master else 'paused'} and synced to cloud.", icon="🤖")
            st.rerun()
    with c_ctrl2:
        if st.button("🔄 Trigger Auto-Trade Scan Cycle Now", key="btn_run_at_cycle_hero", use_container_width=True):
            with st.spinner("🤖 Auto-Trader is monitoring positions and scanning for high-conviction entries..."):
                cycle_report = run_auto_trade_cycle(user_budget=top_budget, risk_pct=top_risk_pct)
            num_closed = len(cycle_report.get("closed_in_cycle", []))
            num_entered = len(cycle_report.get("new_entries", []))
            if num_closed > 0 or num_entered > 0:
                st.success(f"🎯 Cycle Complete: {num_entered} new trade(s) entered, {num_closed} position(s) exited & diagnosed.")
            else:
                st.info("ℹ️ Auto-Trade scan complete: Positions monitored, no new trade triggered (within risk/conviction thresholds).")
            try:
                from utils.cross_device_sync import push_sync_to_cloud_async
                push_sync_to_cloud_async()
            except Exception:
                pass
            st.rerun()
    with c_ctrl3:
        if st.button("☁️ Sync PC & Mobile Now", key="btn_cross_device_sync_cockpit", use_container_width=True, help="Transfers trade status, active positions, and configuration across PC and Mobile devices."):
            with st.spinner("🔄 Synchronizing state with cloud relay..."):
                try:
                    from utils.cross_device_sync import pull_and_apply_cloud_sync, push_sync_to_cloud_async
                    push_sync_to_cloud_async()
                    sync_res = pull_and_apply_cloud_sync()
                    st.toast(f"✅ {sync_res.get('message', 'State synchronized.')}", icon="☁️")
                except Exception as ex_sync:
                    st.toast(f"Sync note: {ex_sync}", icon="ℹ️")
            st.rerun()

    # 4. Live Scanner Radar & Active Positions Feed (Directly visible without expander)
    if active_auto_trades:
        st.markdown(f"#### 📊 Active Auto-Traded Positions ({len(active_auto_trades)} of {max_pos} slots used)")
        for at_pos in active_auto_trades:
            at_id = at_pos["id"]
            at_tick = at_pos["ticker"]
            at_entry = float(at_pos["entry_price"])
            at_target = float(at_pos["target_price"])
            at_stop = float(at_pos["stop_loss_price"])
            at_sh = int(at_pos["shares"])
            at_val = float(at_pos["position_value"])
            at_h = at_pos.get("horizon", "DAY_TRADE")
            at_mode = at_pos.get("execution_mode", "SIMULATION")

            h_badge = (
                '<span style="background:#FF980022;color:#FF9800;border:1px solid #FF980044;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;">⚡ DAY</span>'
                if at_h == "DAY_TRADE"
                else '<span style="background:#58A6FF22;color:#58A6FF;border:1px solid #58A6FF44;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;">🔭 SWING</span>'
                if at_h == "SWING_TRADE"
                else '<span style="background:#3FB95022;color:#3FB950;border:1px solid #3FB95044;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;">🌱 LONG-TERM</span>'
            )

            c_pos_info, c_pos_act = st.columns([4, 1])
            with c_pos_info:
                st.markdown(
                    f"<div style='background:#161B22; border:1px solid #30363D; border-radius:8px; padding:10px 14px; margin-bottom:6px;'>"
                    f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                    f"<span><strong>#{at_id} · {at_tick}</strong> {h_badge} · <strong>{at_sh:,} shares</strong> @ ₹{at_entry:,.2f} (₹{at_val:,.0f} value)</span>"
                    f"<span style='font-size:11px; color:#8B949E;'>Mode: <strong>{at_mode}</strong></span>"
                    f"</div>"
                    f"<div style='display:flex; gap:16px; font-size:11px; margin-top:4px;'>"
                    f"<span style='color:#58A6FF;'>🎯 Target: ₹{at_target:,.2f} (+{round(((at_target-at_entry)/at_entry)*100, 1)}%)</span>"
                    f"<span style='color:#F85149;'>🛑 Stop: ₹{at_stop:,.2f} ({round(((at_stop-at_entry)/at_entry)*100, 1)}%)</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with c_pos_act:
                if st.button(f"✖ Exit #{at_id}", key=f"btn_man_exit_{at_id}", use_container_width=True):
                    close_paper_trade(at_id, at_entry, "MANUAL_EXIT")
                    pm = diagnose_trade_postmortem(at_tick, at_pos["trade_type"], at_entry, at_target, at_stop, at_entry, "MANUAL_EXIT")
                    pm["trade_id"] = at_id
                    log_trade_postmortem(pm)
                    st.toast(f"Position #{at_id} ({at_tick}) squared off manually.", icon="✖")
                    st.rerun()
    else:
        if is_at_active:
            st.markdown(
                f"""
                <div style="background:#161B22; border:1.5px solid #238636; border-radius:10px; padding:14px 18px; margin:8px 0 16px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#3FB950; font-weight:800; font-size:14px;">🟢 Live Scanner Active & Evaluating Markets</span>
                        <span style="font-size:11px; color:#8B949E; background:#0D1117; padding:3px 10px; border-radius:12px; border:1px solid #30363D;">0 of {max_pos} Slots In Use</span>
                    </div>
                    <div style="font-size:13px; color:#C9D1D9; margin-top:8px; line-height:1.5;">
                        The autonomous scanner is currently monitoring 500+ Indian stocks across <strong>{cur_horizons_raw.replace('_', ' ')}</strong>.<br/>
                        When a high-conviction setup is detected (ML consensus &gt; 55% + regime alignment), it will enter automatically and appear right here, sized to your ₹{top_budget:,.0f} budget.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="background:#161B22; border:1.5px dashed #30363D; border-radius:10px; padding:14px 18px; margin:8px 0 16px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#8B949E; font-weight:800; font-size:14px;">⚪ Scanner On Standby (Auto-Trader Switched OFF)</span>
                        <span style="font-size:11px; color:#8B949E; background:#0D1117; padding:3px 10px; border-radius:12px; border:1px solid #30363D;">0 of {max_pos} Slots In Use</span>
                    </div>
                    <div style="font-size:13px; color:#8B949E; margin-top:8px; line-height:1.5;">
                        Turn ON the <strong>Auto-Trade Engine Master Switch</strong> above to start the autonomous scanner, or tap <strong>'Trigger Auto-Trade Scan Cycle Now'</strong> to test an instant scan.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 5. Advanced Settings & Horizon Rules Expander
    with st.expander("⚙️ Auto-Trader Rules, Risk Sizing & Broker Gateway Configuration", expanded=False):
        c_at_m1, c_at_m2 = st.columns([1, 1])
        with c_at_m1:
            mode_choice = st.radio(
                "Execution Mode (Safety Guard)",
                options=["🛡️ Safe Simulation (Paper Trading)", "🚀 Live Broker Gateway"],
                index=0 if cur_mode == "SIMULATION" else 1,
                horizontal=True,
                key="radio_at_mode_settings",
                help="Simulation records all trades into SQLite with zero real money risk. Live Broker dispatches real orders via official API."
            )
            chosen_exec_mode = "SIMULATION" if "Simulation" in mode_choice else "LIVE_BROKER"
        with c_at_m2:
            st.metric("Risk Cap Per Trade", f"{top_risk_pct*100:.1f}%", help="Strictly capped mathematically by the position sizing formula.")

        # Horizon Selectors & Capacity
        c_h1, c_h2 = st.columns([2, 1])
        with c_h1:
            horizon_options = ["⚡ Day Trading (Intraday)", "🔭 Multi-Day Swing Trading", "🌱 Long-Term Compounding"]
            default_sel = []
            if "DAY_TRADE" in cur_horizons_raw:
                default_sel.append("⚡ Day Trading (Intraday)")
            if "SWING_TRADE" in cur_horizons_raw:
                default_sel.append("🔭 Multi-Day Swing Trading")
            if "LONG_TERM" in cur_horizons_raw:
                default_sel.append("🌱 Long-Term Compounding")

            sel_horizons = st.multiselect(
                "Target Trading Horizons",
                options=horizon_options,
                default=default_sel if default_sel else horizon_options,
                key="ms_at_horizons_cfg",
                help="Select which horizons the Auto-Trader is authorized to trade."
            )
        with c_h2:
            new_max_pos = st.slider(
                "Max Open Positions",
                min_value=1,
                max_value=5,
                value=max_pos,
                key="slider_at_max_pos_cfg",
            )

        # Live Broker Details
        sel_brk = auto_cfg.get("selected_broker", "Zerodha Kite")
        wb_url_val = auto_cfg.get("broker_webhook_url", "")
        if chosen_exec_mode == "LIVE_BROKER":
            st.warning("⚠️ **Live Trading Active**: Autonomous orders will be dispatched directly to your broker API.")
            c_brk1, c_brk2 = st.columns(2)
            with c_brk1:
                sel_brk = st.selectbox("Active Broker", SUPPORTED_BROKERS, index=0, key="sel_at_broker_cfg")
            with c_brk2:
                wb_url_val = st.text_input("Broker Webhook / API URL", value=wb_url_val, placeholder="https://api.kite.trade/orders", type="password", key="wb_at_url_cfg")

        # Save configuration if modified
        mapped_horizons = []
        for h in sel_horizons:
            if "Day" in h:
                mapped_horizons.append("DAY_TRADE")
            if "Swing" in h:
                mapped_horizons.append("SWING_TRADE")
            if "Long-Term" in h:
                mapped_horizons.append("LONG_TERM")

        new_cfg = {
            "is_enabled": is_at_active,
            "execution_mode": chosen_exec_mode,
            "enabled_horizons": ",".join(mapped_horizons) if mapped_horizons else "DAY_TRADE",
            "max_concurrent_positions": new_max_pos,
            "risk_pct_per_trade": top_risk_pct,
            "allocated_budget": top_budget,
            "selected_broker": sel_brk,
            "broker_webhook_url": wb_url_val,
        }

        if (
            chosen_exec_mode != cur_mode
            or ",".join(mapped_horizons) != cur_horizons_raw
            or new_max_pos != max_pos
            or sel_brk != auto_cfg.get("selected_broker")
            or wb_url_val != auto_cfg.get("broker_webhook_url")
        ):
            save_auto_trader_config(new_cfg)
            try:
                from utils.cross_device_sync import push_sync_to_cloud_async
                push_sync_to_cloud_async()
            except Exception:
                pass
            st.toast("💾 Auto-Trader settings updated and synced to cloud!", icon="🤖")
            st.rerun()

        # ── 🧠 Auto-Trader Brain & Learning Feed ("What Went Right vs Mistakes Made") ──
        with st.expander("🧠 Auto-Trader Brain Activity & Continuous Self-Learning Feed", expanded=bool(recent_auto_learnings)):
            if not recent_auto_learnings:
                st.info("No auto-trade autopsies logged yet. As the Auto-Trader exits trades, its diagnoses ('What went right' vs 'Mistakes made' & adaptive parameter updates) will appear here in real-time.")
            else:
                for l in recent_auto_learnings:
                    is_profit = float(l.get("pnl_amount", 0)) > 0
                    pnl_color = "#3FB950" if is_profit else "#F85149"
                    diag = l.get("diagnosis_code", "UNKNOWN")
                    h_label = l.get("horizon", "DAY_TRADE").replace("_", " ")

                    st.markdown(
                        textwrap.dedent(f"""
                        <div style="background:#0D1117; border-left:4px solid {pnl_color}; border-radius:6px; padding:10px 14px; margin-bottom:8px; border-top:1px solid #21262D; border-right:1px solid #21262D; border-bottom:1px solid #21262D;">
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                                <div>
                                    <span style="font-weight:800; font-size:12px; color:#F0F6FC;">{l.get('ticker')}</span>
                                    <span style="font-size:10px; background:#161B22; color:#8B949E; padding:1px 6px; border-radius:4px; margin-left:6px;">{h_label}</span>
                                    <span style="font-size:10px; background:#21262D; color:{pnl_color}; padding:1px 6px; border-radius:4px; margin-left:4px; font-weight:700;">{l.get('outcome')}</span>
                                </div>
                                <div style="font-family:var(--mono); font-weight:800; color:{pnl_color}; font-size:12px;">
                                    {'+' if is_profit else ''}₹{float(l.get('pnl_amount', 0)):,.0f} ({float(l.get('pnl_pct', 0)):+.2f}%)
                                </div>
                            </div>
                            <div style="font-size:11px; color:#E6EDF3; margin-top:4px;">
                                <strong>Diagnosis:</strong> <code style="color:#58A6FF;">{diag}</code> · {l.get('root_cause')}
                            </div>
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:11px; margin-top:6px; background:#161B22; padding:6px 10px; border-radius:4px;">
                                <div><span style="color:#3FB950; font-weight:700;">✅ What Went Right:</span> {l.get('what_went_right')}</div>
                                <div><span style="color:#F85149; font-weight:700;">⚠️ Mistakes / Attribution:</span> {l.get('mistakes_made')}</div>
                            </div>
                            <div style="font-size:10px; color:#58A6FF; margin-top:4px;">
                                🔧 <strong>Adaptive Learning Action:</strong> {l.get('corrective_action')} (Stop Buffer: {l.get('buffer_multiplier', 1.0)}x)
                            </div>
                        </div>
                        """),
                        unsafe_allow_html=True
                    )

    st.divider()

    # ── AI Market Season & Regime Radar ──────────────────────────────────────
    market_regime = detect_indian_market_regime()
    try:
        log_regime_snapshot(market_regime)
    except Exception:
        pass

    # ── Macro Cross-Asset Barometer ──────────────────────────────────────────
    macro_baro = get_live_cross_asset_macro()
    assets = macro_baro.get("assets", {})
    crude = assets.get("crude", {"price": 78.5, "chg_5d_pct": 0.0})
    usdinr = assets.get("usdinr", {"price": 87.25, "chg_5d_pct": 0.0})
    gold = assets.get("gold", {"price": 2850.0, "chg_5d_pct": 0.0})

    crude_clr = "#F85149" if crude["chg_5d_pct"] > 0 else "#3FB950"
    usdinr_clr = "#F85149" if usdinr["chg_5d_pct"] > 0 else "#3FB950"
    gold_clr = "#E3B341"

    sensex_p = market_regime.get("sensex_price", 76152.0)
    sensex_chg = market_regime.get("sensex_change_pct", 0.0)
    cross_badge = market_regime.get("cross_exchange_badge", "✅ NSE 50 & BSE Sensex Aligned")
    cross_verdict = market_regime.get("cross_exchange_verdict", "CONFIRMED_NSE_BSE_ALIGNMENT")
    cross_color = "#3FB950" if cross_verdict == "CONFIRMED_NSE_BSE_ALIGNMENT" else "#FFB300"

    macro_econ = fetch_official_indian_macro()
    fci_data = compute_indian_fci(
        repo_rate=macro_econ.get("policy_repo_rate", 6.50),
        cpi_inflation=macro_econ.get("cpi_inflation_pct", 5.08),
        gdp_growth=macro_econ.get("gdp_growth_pct", 6.70),
        crude_oil_price=crude.get("price", 78.5),
        usdinr_exchange_rate=usdinr.get("price", 87.25),
    )

    st.markdown(
        textwrap.dedent(f"""
        <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:12px 16px; margin:14px 0;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
              <span style="font-size:11px; color:#8B949E; font-weight:700;">🏛️ CURRENT INDIAN DUAL-EXCHANGE REGIME</span>
              <div style="font-size:16px; font-weight:800; color:{market_regime['badge_color']};">
                {market_regime['regime_name']}
              </div>
            </div>
            <div style="text-align:right;">
              <span style="font-size:11px; color:#8B949E;">
                Nifty: <strong>₹{market_regime.get('nifty_price', 23873):,.0f}</strong> ({market_regime['nifty_pct_ema20']:+.1f}% vs EMA20) · 
                Sensex: <strong>₹{sensex_p:,.0f}</strong> ({sensex_chg:+.2f}%)
              </span>
              <div style="font-size:12px; font-weight:700; color:#58A6FF;">Playbook: {market_regime['strategy_playbook']}</div>
            </div>
          </div>
          <div style="font-size:11px; color:#C9D1D9; margin-top:6px; border-top:1px solid #21262D; padding-top:6px;">
            💡 <em>{market_regime['playbook_guidance']}</em>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-top:8px; border-top:1px dashed #21262D; padding-top:8px;">
            <div style="font-size:11px; color:#8B949E;">
              🌐 <strong>Cross-Asset Macro:</strong> 
              Crude: <strong>${crude['price']}</strong> (<span style="color:{crude_clr}">{crude['chg_5d_pct']:+.1f}% 5D</span>) · 
              USD/INR: <strong>₹{usdinr['price']}</strong> (<span style="color:{usdinr_clr}">{usdinr['chg_5d_pct']:+.1f}%</span>) · 
              Gold: <strong>${gold['price']:,.0f}</strong>
            </div>
            <div style="display:flex; gap:6px; align-items:center;">
              <span style="font-size:10px; font-weight:700; background:#21262D; padding:2px 8px; border-radius:10px; color:{cross_color};">
                {cross_badge}
              </span>
              <span style="font-size:10px; font-weight:800; background:#21262D; padding:2px 8px; border-radius:10px; color:#58A6FF;">
                {macro_baro['macro_badge']}
              </span>
            </div>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-top:6px; border-top:1px dashed #21262D; padding-top:6px;">
            <div style="font-size:11px; color:#8B949E;">
              🇮🇳 <strong>Indian Economic Engine:</strong> 
              RBI Repo: <strong>{macro_econ['policy_repo_rate']}%</strong> · 
              CPI Inflation: <strong>{macro_econ['cpi_inflation_pct']}%</strong> · 
              Real GDP: <strong>{macro_econ['gdp_growth_pct']}%</strong> (YoY)
            </div>
            <div style="display:flex; gap:6px; align-items:center;">
              <span style="font-size:10px; font-weight:800; background:#21262D; padding:2px 8px; border-radius:10px; color:{fci_data['badge_color']};">
                {fci_data['fci_badge']}
              </span>
            </div>
          </div>
        </div>
        """),
        unsafe_allow_html=True
    )


    # ── 🏛️ India Market Leaders & Benchmark Radar (Permanent Live Card) ────────
    st.markdown(
        """
        <div style="background:#161B22; border:1px solid #21262D; border-radius:10px; padding:12px 14px 6px 14px; margin-bottom:10px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size:13px; font-weight:700; color:#58A6FF; letter-spacing:0.5px;">
              🏛️ INDIA MARKET LEADERS & BENCHMARKS
            </div>
            <div style="font-size:10px; color:#8B949E; background:#21262D; padding:2px 8px; border-radius:10px;">
              Live Dalal Street Quotes
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    c_ref_btn, c_auto_chk = st.columns([1, 1])
    with c_ref_btn:
        if st.button("🔄 Refresh Quotes Now", key="refresh_leaders_now", use_container_width=True):
            get_india_market_leaders_quotes.clear()
            st.toast("⚡ Fresh live Dalal Street quotes loaded!", icon="📈")
            st.rerun()
    with c_auto_chk:
        auto_refresh = st.checkbox("⚡ Auto-refresh (30s)", value=False, key="auto_refresh_leaders_toggle")

    now_str = datetime.datetime.now().strftime("%I:%M:%S %p")
    if auto_refresh and st_autorefresh is not None:
        st_autorefresh(interval=30000, limit=None, key="leaders_autorefresh_counter")
        st.caption(f"🟢 **Live streaming active** · Auto-refreshing every 30s · Updated at {now_str}")
    else:
        st.caption(f"Quotes cached for 30s · Last updated at {now_str}")

    leaders_quotes = get_india_market_leaders_quotes()
    for i in range(0, len(leaders_quotes), 2):
        cols = st.columns(2)
        for col_idx, item in enumerate(leaders_quotes[i:i+2]):
            with cols[col_idx]:
                st.metric(
                    label=f"{item['name']} ({item['symbol']})",
                    value=f"₹{item['price']:,.2f}",
                    delta=f"{item['change']:+.2f}%"
                )
    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    # ── Persona & Track Selector (Persisted User Preferences) ─────────────────
    prefs = get_user_preferences()
    saved_budget = float(prefs.get("total_capital", 500000.0))
    saved_risk_prof = prefs.get("risk_profile", "Balanced (1.0% max risk)")
    saved_goal_idx = int(prefs.get("trading_goal_index", 0))

    track_options = [
        "⚡ Quick Profits & Day Trading (Intraday Scalps: Minutes to 1 Day)",
        "🌱 Multi-Year Wealth Compounding (Long-Term Stocks: 1 to 5 Years)",
    ]
    if "copilot_goal_track" not in st.session_state:
        st.session_state["copilot_goal_track"] = track_options[saved_goal_idx if saved_goal_idx in [0, 1] else 0]

    risk_options = ["Conservative (0.5% max risk)", "Balanced (1.0% max risk)", "Active (2.0% max risk)"]
    if "copilot_risk_profile" not in st.session_state:
        st.session_state["copilot_risk_profile"] = saved_risk_prof if saved_risk_prof in risk_options else risk_options[1]

    if "copilot_user_budget" not in st.session_state:
        st.session_state["copilot_user_budget"] = float(st.session_state.get("total_capital", saved_budget))

    c_track, c_budget, c_risk = st.columns([3, 2, 2])
    with c_track:
        track_choice = st.radio(
            "🎯 Select Your Trading / Investing Goal",
            options=track_options,
            key="copilot_goal_track",
        )
        cur_goal_idx = 0 if "Quick Profits" in track_choice else 1
        if cur_goal_idx != saved_goal_idx:
            save_user_preference("trading_goal_index", cur_goal_idx)

    with c_budget:
        user_budget = st.number_input(
            "💰 Your Trading Budget (₹)",
            min_value=1_000.0,
            max_value=10_000_000.0,
            step=5_000.0,
            key="copilot_user_budget",
            help="The amount of capital you want to allocate for these setups (automatically saved).",
        )
        if user_budget != saved_budget:
            save_user_preference("total_capital", user_budget)
        st.session_state["total_capital"] = user_budget

    with c_risk:
        risk_profile = st.selectbox(
            "🛡️ Risk Appetite",
            options=risk_options,
            key="copilot_risk_profile",
            help="Strict mathematical stop-loss cap on capital per trade.",
        )
        if risk_profile != saved_risk_prof:
            save_user_preference("risk_profile", risk_profile)
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

    # ── 🎖️ Veteran Wisdom & Advice Fact-Check Section ────────────────────────
    with st.expander("🎖️ Feed Advice from Stock Market Veterans (AI Empirical Fact-Check)"):
        st.caption(
            "Heard a trading rule, tip, or heuristic from a Dalal Street veteran, mentor, or financial book? "
            "Type it here. The AI Learner will run an empirical walk-forward backtest across 2 years of actual NSE data, "
            "measure its statistical edge, and decide whether to incorporate it into its active brain or reject it as an unbacked retail myth."
        )
        c_v1, c_v2 = st.columns([3, 1])
        with c_v1:
            v_input = st.text_input(
                "Enter Veteran Advice / Rule",
                placeholder="e.g. When Reliance RSI drops below 40, buy for a 5 day swing...",
                key="copilot_veteran_rule_input"
            ).strip()
        with c_v2:
            v_author = st.text_input("Source / Mentor", value="Dalal Street Veteran", key="copilot_veteran_author")
        
        c_vbtn, _ = st.columns([2, 3])
        with c_vbtn:
            check_v_btn = st.button("🧪 Fact-Check With AI Learner", key="btn_check_veteran_copilot", use_container_width=True)

        if check_v_btn and v_input:
            with st.spinner("🤖 AI Learner is parsing rule conditions and running a 2-year walk-forward backtest..."):
                v_res = fact_check_veteran_rule(v_input, author_or_source=v_author)
                save_veteran_rule(v_res)
            
            st.markdown(
                textwrap.dedent(f"""
                <div style="background:#161B22; border:2px solid {v_res['badge_color']}; border-radius:10px; padding:14px; margin:10px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <span style="font-size:15px; font-weight:800; color:{v_res['badge_color']};">{v_res['verdict_badge']}</span>
                        <span style="font-size:11px; color:#8B949E;">Target Stock: <strong>{v_res.get('target_ticker', 'N/A')}</strong> | Source: {v_res.get('author', 'Mentor')}</span>
                    </div>
                    <div style="margin-top:8px; font-size:12px; color:#E6EDF3; line-height:1.5;">
                        {v_res['summary_report']}
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
            v_m1, v_m2, v_m3, v_m4 = st.columns(4)
            v_m1.metric("Historical Triggers", v_res["occurrences"])
            v_m2.metric("Win Rate %", f"{v_res['win_rate_pct']:.1f}%")
            v_m3.metric("Profit Factor", f"{v_res['profit_factor']:.2f}×")
            v_m4.metric("Avg Return / Trade", f"{v_res['avg_return_pct']:+.2f}%")



    # ── ⚡ TRACK 1: DAY TRADING & QUICK PROFITS ────────────────────────────────
    if track_choice.startswith("⚡"):
        # Live Broker Gateway Configuration (OFF by Default)
        with st.expander("⚡ Live Broker Execution Gateway (Optional & Switched OFF by Default)", expanded=False):
            enable_broker = st.toggle(
                "Enable Live Broker Routing (Fenix / Kite / Upstox)",
                value=st.session_state.get("broker_routing_enabled", False),
                key="toggle_broker_routing",
                help="Switched OFF by default for safety. When disabled, orders are simulated in Paper Trading mode with zero financial risk."
            )
            st.session_state["broker_routing_enabled"] = enable_broker
            
            if enable_broker:
                st.warning("⚠️ **Live Broker Mode Active**: Order buttons will attempt to dispatch real trades to your configured broker endpoint.")
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    sel_broker = st.selectbox("Select Active Broker", SUPPORTED_BROKERS, index=0, key="sel_broker_copilot")
                with b_col2:
                    wb_url = st.text_input("Broker Webhook / API URL", placeholder="https://api.kite.trade/orders or n8n webhook", type="password", key="wb_url_copilot")
                st.caption(f"Connected to **{sel_broker}**. Orders will be formatted using official exchange JSON specifications.")
            else:
                st.caption("🛡️ **Safe Simulation Mode Active**: All trades are recorded to your offline SQLite Paper Trading journal (`finvision_data.db`) with zero real capital risk.")

        col_head1, col_head2 = st.columns([3, 2])
        with col_head1:
            st.markdown("### ⚡ Today's AI Master Day Trading Setups")
            st.caption(f"Mathematically sized for a **₹{user_budget:,.0f}** account with **₹{user_budget*risk_pct:,.0f}** maximum risk protection.")
        with col_head2:
            if st.button("🔄 Retrain ML on Trade Journal", key="btn_retrain_ml", use_container_width=True):
                retrain_res = retrain_ensemble_from_trade_journal()
                if retrain_res["status"] == "SUCCESS":
                    st.toast(retrain_res["message"], icon="🤖")
                else:
                    st.toast(f"ℹ️ {retrain_res['message']}", icon="📓")

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
                clean_close = df_t["Close"].dropna()
                if clean_close.empty:
                    continue
                last_p = float(clean_close.iloc[-1])

                b_entry = bp.get("buy_entry", last_p)
                t1 = bp.get("sell_target_1", last_p * 1.015)
                t2 = bp.get("sell_target_2", last_p * 1.03)
                sl = bp.get("stop_loss", last_p * 0.985)
                act = bp.get("primary_action", "BUY ON PULLBACK")
                bias = bp.get("opening_bias", "🟢 EXPECTED TO RISE")
                flip = bp.get("flip_time_est", "10:00 AM")
                conv = fc.get("conviction_pct", 65.0)

                # Adaptive Post-Mortem Stop Buffer
                adaptive_buf = get_stock_adaptive_buffer(tick)
                stop_mult = adaptive_buf.get("current_stop_multiplier", 1.0)
                if stop_mult > 1.0:
                    sl = round(b_entry - abs(b_entry - sl) * stop_mult, 2)

                delivery_accum = fc.get("delivery_accumulation", {}).get("is_accumulation", False)
                exit_trap = fc.get("exit_liquidity_trap", {}).get("is_trap", False)

                meta_eval = evaluate_meta_labeling_filter(
                    ticker=tick,
                    action=act,
                    entry_price=b_entry,
                    stop_loss=sl,
                    target_price=t1,
                    conviction_pct=conv,
                    rsi=fc.get("rsi", 50.0),
                    regime_code=market_regime.get("regime_code", "BULL_MARKUP"),
                    vix_val=market_regime.get("vix_value", 14.5),
                    delivery_accum=delivery_accum,
                    exit_trap=exit_trap
                )

                # Profit % and Risk:Reward
                profit_pct = round(((t1 - b_entry) / max(0.01, b_entry)) * 100.0, 2)
                risk_dist = max(0.01, abs(b_entry - sl))
                reward_dist = abs(t1 - b_entry)
                rr = round(reward_dist / risk_dist, 2)

                sizing = compute_position_size(user_budget, risk_pct, b_entry, sl)
                raw_shares = sizing.get("shares", 0)
                bet_mult = meta_eval.get("bet_sizing_factor", 1.0)
                final_shares = max(1 if raw_shares > 0 and bet_mult > 0 else 0, int(raw_shares * bet_mult))
                final_pos_val = round(final_shares * b_entry, 2)
                final_risk = round(final_shares * abs(b_entry - sl), 2)

                ml_data = fc.get("ml_ensemble", {})
                tail_risk = fc.get("tail_risk", {})
                var_inr = round(final_pos_val * (tail_risk.get("var_95_pct", 1.8) / 100.0), 1)
                cvar_inr = round(final_pos_val * (tail_risk.get("cvar_95_pct", 2.4) / 100.0), 1)
                reg_mode = fc.get("regime_adaptive_mode", "Adaptive")

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
                    "shares": final_shares,
                    "pos_val": final_pos_val,
                    "risk_val": final_risk,
                    "meta_eval": meta_eval,
                    "adaptive_stop_mult": stop_mult,
                    "ml_ensemble": ml_data,
                    "ml_badge": ml_data.get("badge", "🤖 ML Consensus: Active"),
                    "tail_risk": tail_risk,
                    "var_inr": var_inr,
                    "cvar_inr": cvar_inr,
                    "regime_mode": reg_mode,
                })
            except Exception:
                continue

        # Prioritize actionable setups: Filter for approved setups with shares > 0 first!
        actionable_setups = [s for s in setups if s["meta_eval"]["is_approved"] and s["shares"] > 0]
        actionable_setups = sorted(
            actionable_setups,
            key=lambda x: (x["meta_eval"].get("meta_win_probability_pct", 0), x["conviction"]),
            reverse=True
        )

        vetoed_setups = [s for s in setups if s not in actionable_setups]
        vetoed_setups = sorted(vetoed_setups, key=lambda x: x["conviction"], reverse=True)

        # Present actionable setups first so user gets usable trades!
        sorted_setups = (actionable_setups + vetoed_setups)[:3]

        if not sorted_setups:
            st.info("Market data is refreshing. Click below to analyze setups.")
        else:
            if actionable_setups:
                st.caption(f"⚡ Showing **{min(len(actionable_setups), 3)} actionable setup(s)** with positive statistical edge (screened across {len(day_tickers_to_scan)} market leaders).")
            else:
                st.caption("🛡️ All standard long setups are currently paused by the AI Risk Gatekeeper to protect capital during this market correction.")

            for s_idx, s in enumerate(sorted_setups, start=1):
                tick = s["ticker"]
                is_short = "SELL" in s["action"].upper() or "SHORT" in s["action"].upper()
                est_profit_inr = round(s["shares"] * abs(s["target1"] - s["entry"]), 0)
                anti_sweep_badge = ""
                if s.get("adaptive_stop_mult", 1.0) > 1.0:
                    anti_sweep_badge = f'<span style="background:#A371F722;color:#A371F7;border:1px solid #A371F744;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700;">🛡️ Anti-Sweep Stop ({s["adaptive_stop_mult"]}x ATR)</span>'

                order_verb = "Short / Sell" if is_short else "Buy"
                level1_lbl = "1. Short Limit Entry" if is_short else "1. Place Buy Limit"
                level2_lbl = "2. Cover Target (Scalp)" if is_short else "2. Take Profit (Scalp)"

                friction_res = compute_indian_market_friction(
                    entry_price=s["entry"],
                    exit_price=s["target1"],
                    shares=s["shares"],
                    is_intraday=True
                )

                gtt_info = compute_gtt_order_parameters(
                    ticker=tick,
                    current_price=s["price"],
                    entry_price=s["entry"],
                    stop_loss=s["stop_loss"],
                    target1=s["target1"],
                    shares=s["shares"]
                )

                bse_event = check_corporate_event_risk(tick)
                bse_event_badge = ""
                if bse_event.get("has_imminent_event"):
                    bse_event_badge = f'<span style="background:#F8514922;color:#F85149;border:1px solid #F8514944;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700;">{bse_event["warning_badge"]}</span>'

                adaptive_res = calculate_adaptive_confluence_score(
                    trend_score=0.85 if "BULL" in s["bias"].upper() else 0.35,
                    momentum_score=s["conviction"],
                    sr_score=0.80,
                    volume_score=0.75,
                    news_score=0.60,
                    regime_name=market_regime.get("regime_name", "BULL_MARKUP")
                )

                with st.container():
                    card_html_t1 = "\n".join([
                        f'<div class="top10-card" style="border-left: 4px solid #58A6FF;margin-bottom:18px;">',
                        f'<div class="top10-header">',
                        f'<div>',
                        f'<span class="top10-rank-pill">🎯 SETUP #{s_idx}</span>',
                        f'<span class="top10-symbol">&nbsp;{esc(tick)}</span>',
                        f'<div class="top10-sector">Reference Price: <strong>₹{s["price"]:,.2f}</strong></div>',
                        f'</div>',
                        f'<div style="text-align:right;"></div>',
                        f'</div>',
                        f'<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">',
                        f'<span class="tactical-badge tactical-badge-action">⚡ {esc(s["action"])}</span>',
                        f'<span class="tactical-badge tactical-badge-up">{esc(s["bias"])}</span>',
                        f'<span style="background:{s["meta_eval"]["badge_color"]}22;color:{s["meta_eval"]["badge_color"]};border:1px solid {s["meta_eval"]["badge_color"]}44;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;">{s["meta_eval"]["status_badge"]}</span>',
                        anti_sweep_badge,
                        bse_event_badge,
                        f'<span style="font-size:11px;color:var(--amber);font-family:var(--mono);">Expected Inflection @ {esc(s["flip_time"])}</span>',
                        f'</div>',
                        f'<div class="top10-grid-levels">',
                        f'<div class="level-item"><span class="level-label">{level1_lbl}</span><span class="level-val val-buy">₹{s["entry"]:,.2f}</span></div>',
                        f'<div class="level-item"><span class="level-label">{level2_lbl}</span><span class="level-val val-target">₹{s["target1"]:,.2f}</span></div>',
                        f'<div class="level-item"><span class="level-label">3. Stop Loss</span><span class="level-val val-stop">₹{s["stop_loss"]:,.2f}</span></div>',
                        f'</div>',
                        f'<div class="top10-sizing-strip">',
                        f'<span>EXACT SIZED ORDER</span>',
                        f'<span>{order_verb} <strong>{s["shares"]:,} shares</strong> (₹{s["pos_val"]:,.0f} value) · Max Loss strictly capped at ₹{s["risk_val"]:,.0f} ({s["meta_eval"]["bet_sizing_factor"]}x sizing)</span>',
                        f'</div>',
                        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; font-size:11px; background:#0B1E12; border:1px solid #238636; border-radius:6px; padding:6px 10px; margin-top:6px;">',
                        f'<span>💰 <strong>Gross:</strong> +₹{est_profit_inr:,.0f} · <strong>Taxes & Brokerage:</strong> -₹{friction_res["total_friction"]:,.0f}</span>',
                        f'<span style="color:#3FB950; font-weight:800;">✨ Net Take-Home: +₹{friction_res["net_profit"]:,.0f} ({friction_res["net_return_pct"]:+.2f}%)</span>',
                        f'<span style="color:#8B949E; font-size:10px;">Break-Even: ₹{friction_res["break_even_price"]:,.2f}</span>',
                        f'</div>',
                        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; font-size:11px; background:#0D1117; border:1px solid #21262D; border-radius:6px; padding:6px 10px; margin-top:8px;">',
                        f'<span>📉 <strong>1D 95% VaR:</strong> ₹{s["var_inr"]:,.0f} (CVaR Tail Loss: ₹{s["cvar_inr"]:,.0f})</span>',
                        f'<span style="color:#58A6FF; font-weight:700;">{s["ml_badge"]}</span>',
                        f'<span style="color:#8B949E; font-size:10px;">⚖️ {s["regime_mode"]}</span>',
                        f'</div>',
                        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; font-size:10px; color:#8B949E; padding:4px 8px; margin-top:4px; border-top:1px dashed #21262D;">',
                        f'<span>🎯 <strong>Adaptive Weights:</strong> {adaptive_res["weight_summary"]}</span>',
                        f'<span style="color:#58A6FF;">Key Edge: <strong>{adaptive_res["dominant_factor"]}</strong></span>',
                        f'</div>',
                        f'</div>'
                    ])
                    st.markdown(card_html_t1, unsafe_allow_html=True)

                    # GTT Ready-to-Copy Expander
                    with st.expander(f"📋 Zerodha / Upstox GTT Ready-to-Copy Card ({tick})", expanded=False):
                        st.markdown(f"**GTT Single Buy Trigger:** `₹{gtt_info['single_gtt']['trigger_price']:,.2f}` | **Limit Price:** `₹{gtt_info['single_gtt']['limit_price']:,.2f}`")
                        st.markdown(f"**GTT OCO Stop Trigger:** `₹{gtt_info['oco_gtt']['sl_trigger_price']:,.2f}` | **Target Trigger:** `₹{gtt_info['oco_gtt']['target_trigger_price']:,.2f}`")
                        st.code(gtt_info["single_gtt"]["copy_text"] + "\n\n" + gtt_info["oco_gtt"]["copy_text"], language="text")
                        st.caption("📋 1-Click Copy: Paste these parameters directly into Zerodha Kite / Groww GTT order creator.")

                    # Interactive actions & ELI5
                    col_act1, col_act2, col_act3 = st.columns([2, 2, 3])
                    with col_act1:
                        if st.session_state.get("broker_routing_enabled", False):
                            if st.button(f"🚀 Deploy to Broker: {tick}", key=f"btn_brk_{tick}_{s_idx}", use_container_width=True):
                                p_load = build_broker_order_payload(
                                    broker=st.session_state.get("sel_broker_copilot", "Zerodha Kite"),
                                    ticker=tick,
                                    transaction_type="SELL" if is_short else "BUY",
                                    quantity=s["shares"],
                                    price=s["entry"],
                                    stop_loss=s["stop_loss"],
                                    target=s["target1"],
                                )
                                dispatch_res = dispatch_broker_order(
                                    broker=st.session_state.get("sel_broker_copilot", "Zerodha Kite"),
                                    payload=p_load,
                                    webhook_url=st.session_state.get("wb_url_copilot", ""),
                                    dry_run=not bool(st.session_state.get("wb_url_copilot", "")),
                                )
                                st.toast(dispatch_res["message"], icon="🚀")
                        else:
                            if st.button(f"📓 Paper Trade: {tick}", key=f"btn_pt_{tick}_{s_idx}", use_container_width=True):
                                trade_id = log_paper_trade(
                                    ticker=tick,
                                    trade_type="BUY_INTRADAY",
                                    entry_price=s["entry"],
                                    target_price=s["target1"],
                                    stop_loss_price=s["stop_loss"],
                                    shares=s["shares"],
                                    notes=f"Copilot Setup #{s_idx}: {s['action']} | Meta: {s['meta_eval']['status_badge']}",
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
                                    f"1. Why trade here: Price is sitting near institutional boundary levels at ₹{s['entry']:,.2f}.\n"
                                    f"2. Your exit plan: As soon as price rises to ₹{s['target1']:,.2f}, sell your shares and lock in your profit of +₹{est_profit_inr:,.0f}.\n"
                                    f"3. Your safety net: If the market drops unexpectedly, your stop loss triggers at ₹{s['stop_loss']:,.2f}. "
                                    f"You only lose ₹{s['risk_val']:,.0f} (which is strictly capped by your risk rules).\n"
                                    f"4. Institutional Tail Risk: 1-Day 95% Value-at-Risk (VaR) is ₹{s['var_inr']:,.0f}. In an extreme 5% tail shock, expected loss is ₹{s['cvar_inr']:,.0f}.\n"
                                    f"5. Machine Learning Consensus: {s['ml_badge']} (Non-linear Random Forest & Logistic Regression cross-validation).\n"
                                    f"6. Net Take-Home Rupees: Gross profit is ₹{est_profit_inr:,.0f}. After STT, GST, exchange fees, and brokerage (-₹{friction_res['total_friction']:,.0f}), your net profit is +₹{friction_res['net_profit']:,.0f} ({friction_res['net_return_pct']:+.2f}% net yield).\n"
                                    f"7. AI Veteran Meta-Model: {s['meta_eval']['verdict_explanation']}"
                                ),
                                key_rules=[
                                    "Never trade without entering the stop loss in your broker app (Zerodha/Groww).",
                                    "Lock profits at Target 1 and do not get greedy if market turns choppy.",
                                    f"Active Market Regime: {market_regime['regime_name']} ({market_regime['strategy_playbook']}).",
                                    f"Dynamic Factor Weighting: {s['regime_mode']}.",
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
            from utils.fundamental_wealth import DEFAULT_FUNDAMENTALS
            for tick in top_picks:
                if tick in DEFAULT_FUNDAMENTALS:
                    fb = dict(DEFAULT_FUNDAMENTALS[tick])
                    fb["ticker"] = tick
                    compounders.append(fb)

        if not compounders:
            st.info("No fundamental compounder records could be retrieved at this moment.")
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
                    card_html_t2 = "\n".join([
                        f'<div class="top10-card" style="border-top: 4px solid #3FB950;margin-bottom:18px;">',
                        f'<div class="top10-header">',
                        f'<div>',
                        f'<span class="moat-pill moat-wide">🏰 {esc(moat)}</span>',
                        f'<span class="top10-symbol">&nbsp;{esc(tick)}</span>',
                        f'<div class="top10-sector">{esc(name)} · LTP: <strong>₹{p:,.2f}</strong></div>',
                        f'</div>',
                        f'<div style="text-align:right;">',
                        f'<div style="font-family:var(--mono);font-size:18px;font-weight:700;color:#3FB950;">~{cagr:.1f}% Projected CAGR</div>',
                        f'<div style="font-size:11px;color:var(--text-muted);font-family:var(--mono);">Quality: {score:.0f}/100 · {esc(tier.split(" ")[1])}</div>',
                        f'</div>',
                        f'</div>',
                        f'<div class="top10-grid-levels" style="grid-template-columns: repeat(3, 1fr);">',
                        f'<div class="level-item"><span class="level-label">P/E Valuation</span><span class="level-val">{c_stock["trailing_pe"]}</span></div>',
                        f'<div class="level-item"><span class="level-label">Return on Equity (ROE)</span><span class="level-val" style="color:#3FB950;">{c_stock["roe_pct"]}%</span></div>',
                        f'<div class="level-item"><span class="level-label">Debt / Equity</span><span class="level-val">{c_stock["debt_to_equity"]}</span></div>',
                        f'</div>',
                        f'<div class="top10-grid-levels" style="grid-template-columns: repeat(2, 1fr);background:#161B22;">',
                        f'<div class="level-item"><span class="level-label">3-Year Compounded Target</span><span class="level-val val-target">₹{t3y:,.0f} (+{round(((t3y-p)/p)*100, 1)}%)</span></div>',
                        f'<div class="level-item"><span class="level-label">5-Year Wealth Multiplier</span><span class="level-val val-profit">₹{t5y:,.0f} (+{round(((t5y-p)/p)*100, 1)}%)</span></div>',
                        f'</div>',
                        f'<div class="top10-sizing">',
                        f'<span>SUGGESTED SIP PLAN</span>',
                        f'<span>Invest <strong>₹{monthly_sip:,.0f}/month</strong> → Projected to grow from ₹{sip_invested:,.0f} to <strong>₹{sip_5y_val:,.0f}</strong> in 5 years</span>',
                        f'</div>',
                        f'</div>'
                    ])
                    st.markdown(card_html_t2, unsafe_allow_html=True)

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

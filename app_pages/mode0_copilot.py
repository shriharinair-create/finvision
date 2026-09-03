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
from utils.market_store import log_paper_trade, log_regime_snapshot, get_stock_adaptive_buffer, save_veteran_rule, get_veteran_rules
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
import textwrap


RECOMMENDED_DAY_TICKERS = [
    "RELIANCE.NS", "MARUTI.NS", "INFY.NS", "TCS.NS",
    "HDFCBANK.NS", "ICICIBANK.NS", "BAJFINANCE.NS", "TITAN.NS",
    "BHARTIARTL.NS", "SUNPHARMA.NS", "ITC.NS", "LT.NS",
    "AXISBANK.NS", "MARUTI.NS", "TATASTEEL.NS", "POWERGRID.NS"
]


DEFAULT_LEADERS = [
    {"symbol": "^NSEI", "name": "NIFTY 50", "sector": "NSE Benchmark", "price": 23873.45, "change": -0.17},
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
    tickers = ["^NSEI", "^NSEBANK", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS"]
    names = {
        "^NSEI": ("NIFTY 50", "NSE Benchmark"),
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

    st.markdown(
        textwrap.dedent(f"""
        <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:12px 16px; margin:14px 0;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
              <span style="font-size:11px; color:#8B949E; font-weight:700;">🏛️ CURRENT INDIAN MARKET REGIME</span>
              <div style="font-size:16px; font-weight:800; color:{market_regime['badge_color']};">
                {market_regime['regime_name']}
              </div>
            </div>
            <div style="text-align:right;">
              <span style="font-size:11px; color:#8B949E;">India VIX: <strong>{market_regime['vix_value']}</strong> | Nifty vs EMA20: <strong>{market_regime['nifty_pct_ema20']:+.1f}%</strong></span>
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
            <div>
              <span style="font-size:10px; font-weight:800; background:#21262D; padding:2px 8px; border-radius:10px; color:#58A6FF;">
                {macro_baro['macro_badge']}
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

    st.divider()

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
                last_p = float(df_t["Close"].iloc[-1])

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

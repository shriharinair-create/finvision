"""
finvision/app_pages/mode3_intraday.py
=====================================
Live Intraday Monitoring Terminal with Real-Time Vector Catalyst & Sentiment Alerting.
"""

from __future__ import annotations

import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from utils.scanner_nlp import evaluate_ticker_sentiment_fast
from utils.historical_news import get_live_15m_ticker_news
from utils.forecasting import compute_quantitative_confluence_forecast, generate_intraday_5m_session_forecast
from utils.charts import plot_intraday_5m_session_forecast
from utils.market_store import (
    log_intraday_forecast_snapshot,
    get_intraday_forecast_snapshots,
    get_snapshot_adaptation_audit
)


def _calc_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculates intraday Volume Weighted Average Price (VWAP)."""
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    cum_tp_vol = (typical_price * df["Volume"]).cumsum()
    cum_vol = df["Volume"].cumsum()
    return cum_tp_vol / cum_vol.replace(0, np.nan)


def _render_live_telemetry_body(ticker: str, interval: str) -> None:
    """Core live telemetry body executed inside a background auto-refreshing fragment."""
    now_str = datetime.datetime.now().strftime("%I:%M:%S %p IST")

    # ── Live Status Pulse Bar ─────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:center;background:rgba(22,27,34,0.85);border:1px solid #30363D;border-radius:8px;padding:8px 16px;margin-bottom:14px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#00E676;box-shadow:0 0 8px #00E676;"></span>
                <span style="font-size:12px;font-weight:700;color:#E6EDF3;letter-spacing:0.5px;">LIVE MARKET STREAM ACTIVE</span>
                <span style="font-size:12px;color:#8B949E;">· Polling {interval} bars for <b>{ticker}</b></span>
            </div>
            <div style="font-size:12px;font-family:var(--mono);color:#8B949E;">
                Last Poll: <span style="color:#58A6FF;font-weight:600;">{now_str}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Vector DB Catalyst Lookup ─────────────────────────────────────────────
    nlp_data = evaluate_ticker_sentiment_fast(ticker, top_k=3)
    sent_score = nlp_data["sentiment_score"]
    label = nlp_data["label"]

    # ── Fetch Intraday Quotes ─────────────────────────────────────────────────
    with st.spinner(f"Streaming {interval} intraday bars for {ticker}..."):
        try:
            df_intra = yf.download(ticker, period="1d", interval=interval, progress=False)
        except Exception:
            df_intra = pd.DataFrame()

    if df_intra.empty:
        st.error(f"No intraday bars returned for {ticker}. Market may be closed or ticker is invalid.")
        return

    if isinstance(df_intra.columns, pd.MultiIndex):
        df_intra.columns = [c[0] for c in df_intra.columns]

    close = df_intra["Close"].dropna()
    last_price = float(close.iloc[-1])
    open_price = float(df_intra["Open"].iloc[0])
    high_price = float(df_intra["High"].max())
    low_price = float(df_intra["Low"].min())
    pct_move = ((last_price - open_price) / open_price) * 100.0

    # VWAP & 9 EMA
    df_intra["VWAP"] = _calc_vwap(df_intra)
    df_intra["EMA9"] = close.ewm(span=9, adjust=False).mean()
    last_vwap = float(df_intra["VWAP"].dropna().iloc[-1]) if not df_intra["VWAP"].dropna().empty else last_price

    # ── KPI & Catalyst Header ─────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Last Price", f"₹{last_price:,.2f}", f"{pct_move:+.2f}% vs Open")
    k2.metric("Intraday VWAP", f"₹{last_vwap:,.2f}", f"{last_price - last_vwap:+.2f} spread")
    k3.metric("Day Range", f"₹{low_price:,.1f} - ₹{high_price:,.1f}")
    k4.metric("Catalyst Tone", f"{sent_score:+.2f} ({label})")

    # ── Active News Catalyst Banner ───────────────────────────────────────────
    if nlp_data["headline"] not in ("No news indexed in DB", "No matching articles"):
        if sent_score > 0.15:
            st.success(f"🟢 **Catalyst Tailwind:** {nlp_data['headline']} (FinBERT: {nlp_data['confidence']}% Positive)", icon="📰")
        elif sent_score < -0.15:
            st.error(f"🔴 **Catalyst Warning:** {nlp_data['headline']} (FinBERT: {nlp_data['confidence']}% Negative)", icon="⚠️")
        else:
            st.info(f"⚪ **Recent News:** {nlp_data['headline']}", icon="ℹ️")

    st.divider()

    # ── Chart + Order Flow Panel ──────────────────────────────────────────────
    col_chart, col_side = st.columns([3, 1])

    with col_chart:
        st.markdown(f"### Intraday Action ({interval}) — {ticker}")

        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=df_intra.index,
                open=df_intra["Open"],
                high=df_intra["High"],
                low=df_intra["Low"],
                close=df_intra["Close"],
                name="Price",
            )
        )
        fig.add_trace(go.Scatter(x=df_intra.index, y=df_intra["VWAP"], mode="lines", name="VWAP", line=dict(color="#FF9800", width=1.5)))
        fig.add_trace(go.Scatter(x=df_intra.index, y=df_intra["EMA9"], mode="lines", name="EMA 9", line=dict(color="#2962FF", width=1.5)))

        fig.update_layout(
            height=560,
            hovermode="x unified",
            xaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.07)",
                rangeslider_visible=False,
                tickfont=dict(color="#8B949E", size=10),
                nticks=25,
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikethickness=1,
                spikecolor="rgba(255, 255, 255, 0.3)",
                spikedash="dot"
            ),
            yaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.10)",
                zerolinecolor="rgba(255, 255, 255, 0.15)",
                tickfont=dict(color="#F0F6FC", size=11, family="monospace"),
                tickformat=".2f",
                tickprefix="₹",
                nticks=22,
                minor=dict(
                    ticks="inside",
                    ticklen=4,
                    showgrid=True,
                    gridcolor="rgba(255, 255, 255, 0.04)"
                ),
                side="right",
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikethickness=1,
                spikecolor="rgba(255, 255, 255, 0.3)",
                spikedash="dot"
            ),
            margin=dict(l=10, r=65, t=30, b=25),
            legend=dict(orientation="h", y=1.02, xanchor="right", x=1, bgcolor="rgba(22, 27, 34, 0.8)", font=dict(color="#E6EDF3", size=11)),
            plot_bgcolor="rgba(13, 17, 23, 0.6)",
            paper_bgcolor="rgba(0, 0, 0, 0)"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Multi-Source Live News & 5-Minute Full Session Candlestick Forecast ---
    st.divider()
    col_n1, col_n2 = st.columns([3, 2])
    with col_n1:
        st.markdown("###  Full-Session 5-Min Projected Trajectory & Dynamic VWAP (09:15 - 15:30 IST)")
        st.caption("Real-time 75-bar session forecast continuously adjusted via 6-source Indian news aggregation & price action.")
    with col_n2:
        live_news_15m = get_live_15m_ticker_news(ticker)
        poll_time = live_news_15m.get("last_polled_at", "Just now")
        n_sent = live_news_15m.get("sentiment_score", 0.0)
        n_cat = live_news_15m.get("catalyst_score", 0.0)
        poll_mode = live_news_15m.get("polling_mode", "Adaptive Poller")
        st.info(f"**⚡ Multi-Source 60s Radar Active** | `{poll_time}`\nSent: `{n_sent:+.2f}` | Cat: `{n_cat:+.2f}` | Mode: `{poll_mode}`")

    # Fetch daily context for ATR and compute 5-min session forecast
    try:
        df_daily = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if isinstance(df_daily.columns, pd.MultiIndex):
            df_daily.columns = [c[0] for c in df_daily.columns]
        
        if not df_daily.empty:
            fc_res = compute_quantitative_confluence_forecast(
                df=df_daily,
                news_sentiment_score=n_sent,
                catalyst_score=n_cat
            )
            fused_s = fc_res.get("fused_score", 0.0)
            
            tf_choice = interval if interval in ["5m", "15m"] else "15m"
            intra_fc = generate_intraday_5m_session_forecast(
                daily_df=df_daily,
                last_price=last_price,
                fused_score=fused_s,
                news_sentiment_score=n_sent,
                catalyst_score=n_cat,
                intraday_actual_df=df_intra if interval == tf_choice else None,
                timeframe=tf_choice
            )
            
            if intra_fc:
                target_date = intra_fc.get("session_date", "Upcoming Session")
                is_upcoming = intra_fc.get("is_upcoming_session", False)
                noise_note = " · 🏛️ Low-Noise Institutional Standard" if tf_choice == "15m" else " · ⚠️ High-Noise Scalp"
                status_label = (
                    f"📅 Target Session: **{target_date}** (Next Upcoming Session){noise_note}"
                    if is_upcoming
                    else f"📅 Live Active Session: **{target_date}**{noise_note}"
                )
                st.markdown(status_label)

                fig_5m_intra = plot_intraday_5m_session_forecast(
                    intra_fc,
                    title=f"{ticker} — {intra_fc.get('total_bars', 25)}-Bar {tf_choice} Forecast for {target_date} (VWAP + 80% CI Envelope)"
                )
                st.plotly_chart(fig_5m_intra, use_container_width=True)
                
                # Intraday Summary Metrics
                im1, im2, im3, im4, im5 = st.columns(5)
                im1.metric("Exp Open", f"{intra_fc['expected_open']:.2f}")
                im2.metric("Exp High", f"{intra_fc['session_high']:.2f}")
                im3.metric("Exp Low", f"{intra_fc['session_low']:.2f}")
                im4.metric("Exp Close", f"{intra_fc['expected_close']:.2f}", f"{intra_fc['expected_return_pct']:+.2f}%")
                im5.metric("Final VWAP", f"{intra_fc['final_vwap']:.2f}")

                # ── Log snapshot to database ledger ──────────────────────────────
                try:
                    slot_now = datetime.datetime.now().strftime("%H:%M")
                    log_intraday_forecast_snapshot({
                        "ticker": ticker,
                        "session_date": target_date,
                        "time_slot": slot_now,
                        "spot_price": last_price,
                        "fused_score": fused_s,
                        "bias_label": fc_res.get("bias_label", "NEUTRAL"),
                        "prob_up": fc_res.get("prob_up", 0.5),
                        "expected_open": intra_fc.get("expected_open", last_price),
                        "expected_close": intra_fc.get("expected_close", last_price),
                        "expected_return_pct": intra_fc.get("expected_return_pct", 0.0),
                        "ci_80_low": intra_fc.get("ci_80_low", last_price * 0.98),
                        "ci_80_high": intra_fc.get("ci_80_high", last_price * 1.02),
                        "final_vwap": intra_fc.get("final_vwap", last_price),
                        "news_sentiment": n_sent,
                        "catalyst_score": n_cat,
                    })
                except Exception as ex_snap:
                    pass

                # ── Real-Time Forecast Adaptation & Audit Trail Expander ──────────
                with st.expander("🕒 Intraday Forecast Evolution & Audit Trail", expanded=False):
                    audit_data = get_snapshot_adaptation_audit(ticker, session_date=target_date)
                    if audit_data.get("available"):
                        snaps_list = audit_data.get("snapshots", [])
                        st.markdown(f"**Recorded Snapshots for {target_date}:** `{len(snaps_list)} time slots`")
                        
                        # Show summary comparison
                        sa1, sa2, sa3 = st.columns(3)
                        sa1.metric("First Forecast Close", f"{audit_data['initial_expected_close']:.2f}", audit_data.get("initial_bias", ""))
                        sa2.metric("Latest Forecast Close", f"{audit_data['latest_expected_close']:.2f}", audit_data.get("latest_bias", ""))
                        if audit_data.get("has_actual_reconciliation"):
                            sa3.metric("Actual Close / MAE", f"{audit_data['actual_close']:.2f}", f"MAE: {audit_data['mean_absolute_error_pct']}%")
                        else:
                            sa3.metric("Latest Spot", f"{last_price:,.2f}", f"Gap to Close: {(intra_fc['expected_close'] - last_price):+.2f}")
                        
                        # Snapshot table
                        df_snaps = pd.DataFrame(snaps_list)
                        display_cols = ["time_slot", "spot_price", "expected_close", "expected_return_pct", "final_vwap", "bias_label", "news_sentiment"]
                        avail_cols = [c for c in display_cols if c in df_snaps.columns]
                        st.dataframe(
                            df_snaps[avail_cols].rename(columns={
                                "time_slot": "Time",
                                "spot_price": "Spot Price",
                                "expected_close": "Exp Close",
                                "expected_return_pct": "Exp Ret %",
                                "final_vwap": "Proj VWAP",
                                "bias_label": "Bias",
                                "news_sentiment": "News Sent"
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.caption("Snapshot recorded. As the session progresses, intraday prediction adjustments will populate here.")
    except Exception as e:
        st.warning(f"Unable to generate 5m session trajectory: {e}")

    with col_side:
        st.markdown("### Execution Checklist & Risk Gate")

        above_vwap = last_price > last_vwap
        above_ema = last_price > float(df_intra["EMA9"].iloc[-1])
        news_aligned = (sent_score > 0 and pct_move > 0) or (sent_score < 0 and pct_move < 0) or abs(sent_score) < 0.1

        # Institutional telemetry from confluence forecast
        exit_trap = fc_res.get("exit_liquidity_trap", {}) if "fc_res" in locals() and fc_res else {}
        is_trap = exit_trap.get("is_trap", False)
        delivery_res = fc_res.get("delivery_accumulation", {}) if "fc_res" in locals() and fc_res else {}
        is_accum = delivery_res.get("is_accumulation", False)
        rr_val = fc_res.get("risk_reward_ratio", 1.5) if "fc_res" in locals() and fc_res else 1.5
        stop_p = fc_res.get("stop_loss", last_price * 0.985) if "fc_res" in locals() and fc_res else last_price * 0.985

        checklist_items = [
            {"Condition": "Price > VWAP", "Status": "✅ Bullish" if above_vwap else "❌ Bearish"},
            {"Condition": "Price > EMA 9", "Status": "✅ Momentum" if above_ema else "❌ Drag"},
            {"Condition": "News Alignment", "Status": "✅ Aligned" if news_aligned else "⚠️ Divergent"},
            {"Condition": "Trap Guard", "Status": "🚨 Distribution Trap" if is_trap else "✅ Clear"},
            {"Condition": "Order Flow", "Status": "🟢 Stealth Accumulation" if is_accum else "⚪ Balanced"},
        ]
        st.dataframe(pd.DataFrame(checklist_items), use_container_width=True, hide_index=True)

        if is_trap:
            st.error(f"🚨 **INSTITUTIONAL EXIT TRAP ALERT:** {exit_trap.get('warning_message', 'High-risk exit distribution zone.')}")

        st.divider()

        # Risk-to-Reward & Trade Bias Synthesis
        st.caption(f"**Anti-Hunt Stop Loss:** ₹{stop_p:,.2f} | **Risk:Reward:** 1 : {rr_val:.2f}")

        if is_trap:
            st.error(f"🛑 **Distribution Warning:** Smart money offloading into retail buying ({exit_trap.get('trap_type', 'TRAP')}). Do not chase longs.")
        elif not above_vwap and sent_score > 0.15:
            st.error(f"🚨 **BULL TRAP / VWAP LOST:** Price (₹{last_price:,.2f}) has broken below VWAP (₹{last_vwap:,.2f}) despite positive news (+{sent_score:.2f}). Smart money is rejecting the catalyst — Longs INVALIDATED.")
        elif above_vwap and above_ema and news_aligned and sent_score > 0.10:
            st.success("🎯 **High-Conviction Long Bias:** Price above VWAP & EMA 9 with confirmed technical and catalyst alignment.")
        elif above_vwap and above_ema and not news_aligned:
            st.warning("⚠️ **Cautious Long:** Price is holding VWAP, but news alignment is divergent. Keep a tight stop loss.")
        elif not above_vwap and not above_ema:
            st.error("🔻 **Short / Capital Preservation Bias:** Price trading below both VWAP and EMA 9. High distribution pressure.")
        else:
            st.warning("⚖️ **Mixed Setup:** Price testing dynamic VWAP boundary. Wait for clear directional confirmation.")


# ── Periodic Auto-Refreshing Fragment Wrappers ────────────────────────────────
@st.fragment(run_every=10)
def _render_live_telemetry_10s(ticker: str, interval: str) -> None:
    _render_live_telemetry_body(ticker, interval)


@st.fragment(run_every=15)
def _render_live_telemetry_15s(ticker: str, interval: str) -> None:
    _render_live_telemetry_body(ticker, interval)


@st.fragment(run_every=30)
def _render_live_telemetry_30s(ticker: str, interval: str) -> None:
    _render_live_telemetry_body(ticker, interval)


@st.fragment(run_every=60)
def _render_live_telemetry_60s(ticker: str, interval: str) -> None:
    _render_live_telemetry_body(ticker, interval)


@st.fragment(run_every=None)
def _render_live_telemetry_manual(ticker: str, interval: str) -> None:
    _render_live_telemetry_body(ticker, interval)


def render_mode3():
    st.markdown("## ⚡ Live Intraday Monitor & Catalyst Radar")
    st.caption("Live minute-level telemetry coupled with real-time Vector DB news catalysts.")

    # ── Ticker & Auto-Refresh Configuration Bar ───────────────────────────────
    c_sym, c_int, c_auto, c_sec, c_btn = st.columns([3, 2, 2, 2, 2])
    with c_sym:
        default_ticker = st.session_state.get("bridged_monitor_ticker") or "^NSEI"
        ticker = st.text_input("Active Monitor Ticker", value=default_ticker, help="e.g. ^NSEI, RELIANCE.NS, APOLLOHOSP.NS")
    with c_int:
        interval_raw = st.selectbox(
            "Candlestick Interval",
            options=["15m (Institutional - Recommended)", "5m (Scalp - High Noise)", "1m"],
            index=0,
            help="15m reduces random microstructure noise by ~42%, matching institutional TWAP/VWAP execution blocks."
        )
        interval = "15m" if "15m" in interval_raw else "5m" if "5m" in interval_raw else "1m"
    with c_auto:
        st.write("")
        auto_refresh = st.toggle("⚡ Auto-Refresh", value=True, help="Continuously poll live market quotes in the background")
    with c_sec:
        refresh_sec = st.selectbox("Interval", options=[10, 15, 30, 60], index=1, format_func=lambda x: f"{x}s")
    with c_btn:
        st.write("")
        st.write("")
        refresh_now = st.button("🔄 Refresh Now", use_container_width=True)

    # Dispatch to the appropriate polling fragment
    if auto_refresh:
        if refresh_sec == 10:
            _render_live_telemetry_10s(ticker, interval)
        elif refresh_sec == 15:
            _render_live_telemetry_15s(ticker, interval)
        elif refresh_sec == 30:
            _render_live_telemetry_30s(ticker, interval)
        else:
            _render_live_telemetry_60s(ticker, interval)
    else:
        _render_live_telemetry_manual(ticker, interval)
"""
Mode 1 — Manual Ticker Analysis
Analyse one or multiple tickers entered by the user, one-by-one.
"""

from __future__ import annotations

import streamlit as st

from utils.data import analyse_ticker
from utils.components import render_ticker_card, esc


def render_mode1() -> None:
    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="page-header">
            <h1>🔍 Manual Ticker Analysis</h1>
            <p>Enter one or more tickers to get full day-trade and swing investment analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Sidebar controls ──────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Ticker Input")

        # Pre-populate from scanner bridge
        default_val = ""
        if st.session_state.get("bridged_tickers"):
            default_val = ", ".join(st.session_state["bridged_tickers"])

        raw_input = st.text_area(
            "Ticker(s)",
            value=default_val,
            placeholder="e.g. RELIANCE.NS, TCS.NS, AAPL, TSLA",
            help=(
                "Enter NSE tickers with .NS suffix (e.g. RELIANCE.NS), "
                "BSE with .BO suffix, or global symbols (e.g. AAPL)."
            ),
            height=90,
        )

        if st.session_state.get("bridged_tickers"):
            if st.button("🔗 Clear bridged tickers", use_container_width=True):
                st.session_state.bridged_tickers = []
                st.rerun()

        show_chart = st.checkbox("Show price charts", value=True)
        run = st.button("▶ Analyse", use_container_width=True, type="primary")

    if not run and not raw_input.strip():
        _render_landing()
        return

    if not raw_input.strip():
        st.warning("Please enter at least one ticker symbol.")
        return

    # ── Parse tickers ─────────────────────────────────────────────────────────
    tickers = [
        t.strip().upper()
        for t in raw_input.replace(",", " ").split()
        if t.strip()
    ]
    tickers = list(dict.fromkeys(tickers))  # deduplicate, preserve order

    if not tickers:
        st.warning("No valid ticker symbols found.")
        return

    # ── Analysis loop ─────────────────────────────────────────────────────────
    for ticker in tickers:
        st.divider()
        with st.expander(
            f"**{ticker}**  —  click to expand full analysis",
            expanded=len(tickers) == 1,
        ):
            with st.spinner(f"Fetching data for {ticker}…"):
                data = analyse_ticker(ticker)

            if data is None:
                st.error(
                    f"❌ Could not fetch data for **{ticker}**. "
                    "Check the symbol and your internet connection."
                )
                continue

            # Ticker name + price header
            import math
            chg    = data["day_change_pct"]
            price  = data["current_price"]
            price_valid = isinstance(price, (int, float)) and not (math.isnan(price) or math.isinf(price))
            chg_valid = isinstance(chg, (int, float)) and not (math.isnan(chg) or math.isinf(chg))

            price_display = f"₹{price:,.2f}" if price_valid else "₹—"
            chg_icon = ("▲" if chg >= 0 else "▼") if chg_valid else "—"
            chg_color = ("#3FB950" if chg >= 0 else "#F85149") if chg_valid else "#8B949E"
            chg_display = f"{abs(chg):.2f}%" if chg_valid else "no data"

            if data.get("is_stale_price"):
                st.warning(
                    "⚠️ Most recent session's close was missing — showing the "
                    "last known good price. Figures may be slightly stale.",
                    icon="⚠️",
                )

            st.markdown(
                f"""
                <div class="ticker-header">
                    <span class="ticker-symbol">{esc(ticker)}</span>
                    <span class="ticker-name">{esc(data['name'])}</span>
                    <span class="ticker-price"
                          style="color:{chg_color if price_valid else '#8B949E'}">
                        {price_display}
                    </span>
                    <span style="color:{chg_color};font-size:13px">
                        {chg_icon} {chg_display}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            render_ticker_card(data, show_chart=show_chart)

    st.divider()
    st.caption(
        "⚠️ FinVision is for research only. All trading decisions are your own responsibility."
    )


def _render_landing() -> None:
    """Landing state when no analysis has been run yet."""
    st.markdown(
        """
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:64px;margin-bottom:16px;">📊</div>
            <h2 style="color:#E6EDF3;font-size:22px;margin-bottom:8px;">
                Enter a ticker to begin analysis
            </h2>
            <p style="color:#8B949E;font-size:14px;max-width:480px;margin:0 auto;">
                Type any ticker symbol in the sidebar — NSE stocks use the <code>.NS</code>
                suffix (e.g. <code>RELIANCE.NS</code>), or enter global symbols like
                <code>AAPL</code>, <code>TSLA</code>.
                <br><br>
                You'll get candlestick charts, SMA levels, a Day-Trade Matrix,
                a Swing Matrix with delusion protection, news sentiment, and a
                composite conviction score.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick-start examples
    st.markdown("---")
    st.markdown("#### Quick-start examples")
    cols = st.columns(4)
    examples = [
        ("🇮🇳 Nifty Blue-chip", "RELIANCE.NS, TCS.NS, HDFCBANK.NS"),
        ("⚡ High-momentum",    "ZOMATO.NS, JIOFIN.NS, SUZLON.NS"),
        ("🌍 US Tech",          "AAPL, MSFT, NVDA"),
        ("📦 Mid-cap Mix",      "APOLLOHOSP.NS, TATAMOTORS.NS, WIPRO.NS"),
    ]
    for col, (label, tickers) in zip(cols, examples):
        with col:
            if st.button(label, use_container_width=True, key=f"ex_{label}"):
                st.session_state["_example_tickers"] = tickers
                st.rerun()

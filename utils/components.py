"""
Reusable HTML/Streamlit UI components for FinVision.
All render to st.markdown with unsafe_allow_html=True.
"""

from __future__ import annotations

import html as html_lib

import streamlit as st

from utils.data import analyse_ticker
from utils.charts import (
    make_candlestick_chart,
    make_conviction_chart,
    make_sentiment_donut,
    make_range_bar,
    make_rsi_macd_chart,
)


def esc(value) -> str:
    """
    HTML-escapes any dynamic value before it's interpolated into a
    markdown(unsafe_allow_html=True) block.

    This matters because several fields rendered here come straight from
    yfinance's free-text `.info` dict (sector, industry, company name) or
    from news headlines/publishers — none of that text is guaranteed to be
    free of '<', '>', or unbalanced quotes. Without escaping, a sector
    string like 'Health Care</div><script>' will silently close the
    surrounding <div> early and corrupt every card rendered after it,
    which is exactly the failure mode that produced raw HTML appearing as
    visible text on the page.
    """
    if value is None:
        return ""
    return html_lib.escape(str(value), quote=True)


# ── Metric grid ───────────────────────────────────────────────────────────────

def metric_card(label: str, value: str, sub: str = "", color_class: str = "") -> str:
    sub_html = f"<div class='metric-sub'>{esc(sub)}</div>" if sub else ""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{esc(label)}</div>
        <div class="metric-value {esc(color_class)}">{esc(value)}</div>
        {sub_html}
    </div>"""


def render_metric_grid(cards: list[tuple]) -> None:
    """cards = list of (label, value, sub, color_class)"""
    html = '<div class="metric-grid">'
    for item in cards:
        label = item[0]
        value = item[1]
        sub   = item[2] if len(item) > 2 else ""
        cls   = item[3] if len(item) > 3 else ""
        html += metric_card(label, value, sub, cls)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Plan A / Plan B boxes ─────────────────────────────────────────────────────

def _render_position_sizing(entry: float, stop: float, currency: str = "₹") -> None:
    """Renders a compact position-sizing readout using sidebar-set capital/risk%."""
    from utils.risk import compute_position_size

    total_capital = st.session_state.get("total_capital", 0)
    risk_pct = st.session_state.get("risk_pct", 0.0)

    if total_capital <= 0 or risk_pct <= 0:
        return

    sizing = compute_position_size(total_capital, risk_pct, entry, stop)
    if sizing["shares"] == 0 and not sizing.get("warning"):
        return

    c = currency
    st.markdown(
        f"""
        <div style="margin-top:8px;padding:8px 12px;background:#0D1117;
                    border:1px dashed #30363D;border-radius:8px;font-size:12px;">
            <span style="color:#8B949E;font-family:monospace;">SUGGESTED SIZE</span>
            &nbsp;&nbsp;
            <span style="color:#58A6FF;font-weight:700;font-family:monospace;">
                {sizing['shares']:,} shares
            </span>
            <span style="color:#8B949E;">
                · {c}{sizing['position_value']:,.0f} position
                ({sizing['position_pct_of_capital']:.1f}% of capital)
                · {c}{sizing['cash_at_risk']:,.0f} at risk
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if sizing.get("warning"):
        st.caption(f"⚠️ {sizing['warning']}")


def render_plan_a(plan: dict, currency: str = "₹") -> None:
    if not plan:
        st.info("Insufficient 15-min data for Plan A.")
        return
    c = currency
    st.markdown(
        f"""
        <div class="plan-box plan-a">
            <div class="plan-title">⚡ Plan A — Day Trade Matrix</div>
            <div class="plan-row">
                <span class="plan-key">Current Rate</span>
                <span class="plan-val rate">{c}{plan['current']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">ATR (15m)</span>
                <span class="plan-val">{c}{plan['atr_15m']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">Limit Buy Entry</span>
                <span class="plan-val buy">{c}{plan['entry']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">Tight Stop-Loss</span>
                <span class="plan-val stop">{c}{plan['stop']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">Day-Trade Target</span>
                <span class="plan-val sell">{c}{plan['target']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">Risk / Reward</span>
                <span class="plan-val">{plan['rr_ratio']}×</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_position_sizing(plan["entry"], plan["stop"], currency)


def render_plan_b(plan: dict, currency: str = "₹") -> None:
    if not plan:
        st.info("Need 60+ days of daily data for Plan B.")
        return
    c = currency
    if plan.get("low_confidence"):
        st.info(
            "ℹ️ Less than 200 trading days of history available — SMA200 "
            "approximated from SMA50. Treat swing levels as lower-confidence."
        )
    if plan.get("delusional"):
        st.error(
            f"⚠️  Target Delusion Alert: Mathematical target "
            f"{c}{plan['raw_target']:,.2f} overshoots the 52-week ceiling "
            f"({c}{plan['week52_high']:,.2f}). Displayed target clamped to "
            f"{c}{plan['target']:,.2f} (3% below resistance)."
        )

    clamped_note = (
        ' <span style="color:#484F58;font-size:11px">(clamped)</span>'
        if plan.get("delusional") else ""
    )
    swing_target_html = f"{c}{plan['target']:,.2f}{clamped_note}"

    st.markdown(
        f"""
        <div class="plan-box plan-b">
            <div class="plan-title">🔭 Plan B — Swing / Long-Term Matrix</div>
            <div class="plan-row">
                <span class="plan-key">Current Rate</span>
                <span class="plan-val rate">{c}{plan['current']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">SMA 50</span>
                <span class="plan-val">{c}{plan['sma50']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">SMA 200</span>
                <span class="plan-val">{c}{plan['sma200']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">Swing Entry</span>
                <span class="plan-val buy">{c}{plan['entry']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">Macro Stop-Loss</span>
                <span class="plan-val stop">{c}{plan['stop']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">Swing Sell Target</span>
                <span class="plan-val sell">{swing_target_html}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">52-Week High</span>
                <span class="plan-val">{c}{plan['week52_high']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">52-Week Low</span>
                <span class="plan-val">{c}{plan['week52_low']:,.2f}</span>
            </div>
            <div class="plan-row">
                <span class="plan-key">Risk / Reward</span>
                <span class="plan-val">{plan['rr_ratio']}×</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_position_sizing(plan["entry"], plan["stop"], currency)


# ── News feed ─────────────────────────────────────────────────────────────────

def render_news_feed(news: list[dict], sentiments: list[str]) -> None:
    if not news:
        st.caption("No recent news found.")
        return

    for item, sentiment in zip(news, sentiments):
        title     = esc(item.get("title", "No title"))
        publisher = esc(item.get("publisher", "Unknown"))
        link      = esc(item.get("link", "#"))

        badge_cls = {
            "positive": "badge-positive",
            "negative": "badge-negative",
        }.get(sentiment, "badge-neutral")

        label = sentiment.capitalize()

        st.markdown(
            f"""
            <div class="news-card sentiment-{sentiment}">
                <div class="news-headline">
                    <a href="{link}" target="_blank"
                       style="color:inherit;text-decoration:none;">{title}</a>
                </div>
                <div class="news-meta">
                    {publisher}
                    &nbsp;·&nbsp;
                    <span class="news-badge {badge_cls}">{label}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Conviction score display ──────────────────────────────────────────────────

def render_conviction(conviction: dict, key_suffix: str = "") -> None:
    score = conviction.get("total", 0)
    grade = conviction.get("grade", "N/A")

    ring_cls = "score-high" if score >= 65 else ("score-medium" if score >= 40 else "score-low")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(
            f'<div class="score-ring {ring_cls}">{score}</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Grade: **{grade}**")
    with col2:
        st.plotly_chart(
            make_conviction_chart(conviction),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"conviction_chart_{key_suffix}",
        )


# ── Candle pattern pills ──────────────────────────────────────────────────────

_PATTERN_META = {
    "shooting_star":  ("🌠 Shooting Star", "bearish", "Bearish reversal / fakeout signal"),
    "hammer":         ("🔨 Hammer",         "bullish", "Bullish support / reversal signal"),
    "strong_bullish": ("🚀 Strong Bullish", "bullish", "Body >60% range — momentum candle"),
    "strong_bearish": ("🔻 Strong Bearish", "bearish", "Body >60% range — heavy selling"),
    "":               ("—", "neutral", "No notable pattern"),
}

def render_pattern_pills(patterns: list[str]) -> None:
    html = ""
    seen: set[str] = set()
    for p in patterns:
        if p and p not in seen:
            seen.add(p)
            meta = _PATTERN_META.get(p, ("Unknown", "neutral", ""))
            label, cls, tooltip = meta
            html += (
                f'<span class="pattern-pill pill-{cls}" title="{tooltip}">'
                f'{label}</span>'
            )
    if html:
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.caption("No candlestick patterns detected in recent 5 bars.")


# ── Trend classification banner ───────────────────────────────────────────────

_TREND_META = {
    "Strong Uptrend":    ("🚀", "#3FB950", "green"),
    "Uptrend":           ("📈", "#3FB950", "green"),
    "Range-bound":       ("↔️", "#D29922", "amber"),
    "Downtrend":         ("📉", "#F85149", "red"),
    "Strong Downtrend":  ("🔻", "#F85149", "red"),
    "Insufficient Data": ("❓", "#8B949E", "grey"),
}

def render_trend_banner(trend: dict) -> None:
    label = trend.get("label", "Insufficient Data")
    confidence = trend.get("confidence", 0)
    icon, color, _ = _TREND_META.get(label, _TREND_META["Insufficient Data"])

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;
                    background:#161B22;border:1px solid #21262D;border-left:3px solid {color};
                    border-radius:8px;margin-bottom:10px;">
            <span style="font-size:20px">{icon}</span>
            <div>
                <span style="font-weight:700;color:{color};font-size:14px">{label}</span>
                <span style="color:#8B949E;font-size:12px;margin-left:8px">
                    {confidence:.0f}% confidence · ADX {trend.get('adx', 0):.1f} · RSI {trend.get('rsi', 0):.0f}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Why this classification?", expanded=False):
        for detail in trend.get("details", []):
            st.markdown(f"- {detail}")


def render_warnings(warnings_list: list[str]) -> None:
    """Render conviction-score risk warnings as compact alert lines."""
    if not warnings_list:
        return
    for w in warnings_list:
        st.warning(w, icon="⚠️")


# ── Full ticker card (used in scanner expanders) ──────────────────────────────

def _is_valid_number(value) -> bool:
    """True only for a real, finite number — False for None, NaN, inf, or non-numeric."""
    import math
    if value is None or isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return not (math.isnan(value) or math.isinf(value))


def _fmt_or_dash(value, fmt: str) -> str:
    """Formats a numeric value, or returns '—' for None/NaN/inf/non-numeric."""
    if not _is_valid_number(value):
        return "—"
    try:
        return format(value, fmt)
    except (ValueError, TypeError):
        return "—"


def render_ticker_card(data: dict, show_chart: bool = True) -> None:
    """Renders full analysis output for a single ticker dict."""
    price    = data["current_price"]
    chg      = data["day_change_pct"]
    chg_valid = _is_valid_number(chg)
    chg_cls  = ("metric-up" if chg >= 0 else "metric-down") if chg_valid else "metric-flat"
    chg_icon = ("▲" if chg >= 0 else "▼") if chg_valid else "—"
    vol      = data["avg_vol_10d"]
    mktcap   = data.get("market_cap")
    pe_ratio = data.get("pe_ratio")
    beta     = data.get("beta")

    if data.get("is_stale_price"):
        st.warning(
            "⚠️ The most recent trading session's close was missing/invalid "
            "for this ticker — showing the last known good price instead. "
            "Figures below may be slightly behind the latest session.",
            icon="⚠️",
        )

    price_valid = _is_valid_number(price)
    price_str = _fmt_or_dash(price, ",.2f")
    chg_str = f"{chg_icon} {_fmt_or_dash(abs(chg), '.2f')}% today" if price_valid and chg_valid else "No change data"
    mktcap_str = f"₹{_fmt_or_dash(mktcap / 1e7, ',.1f')} Cr" if _is_valid_number(mktcap) else "—"
    pe_str = f"{_fmt_or_dash(pe_ratio, '.1f')}x" if _is_valid_number(pe_ratio) else "—"

    render_metric_grid([
        ("Current Price",    f"₹{price_str}",               chg_str, chg_cls),
        ("10d Avg Volume",   _fmt_or_dash(vol, ",.0f"),      "shares/day"),
        ("Sector",           data.get("sector", "—"),       data.get("industry", "")),
        ("Market Cap",       mktcap_str, ""),
        ("P/E Ratio",        pe_str, ""),
        ("Beta",             _fmt_or_dash(beta, ".2f"),      "volatility"),
    ])

    # ── Trend classification ─────────────────────────────────────────────────
    trend = data.get("trend")
    if trend:
        st.markdown('<div class="section-label">Trend Classification</div>', unsafe_allow_html=True)
        render_trend_banner(trend)

    # ── Risk warnings from conviction engine ─────────────────────────────────
    warnings_list = data.get("conviction", {}).get("warnings", [])
    if warnings_list:
        st.markdown('<div class="section-label">Risk Signals</div>', unsafe_allow_html=True)
        render_warnings(warnings_list)

    st.markdown('<div class="section-label">Candlestick Patterns (last 5 bars)</div>', unsafe_allow_html=True)
    render_pattern_pills(data["recent_patterns"])

    if show_chart and not data["daily_df"].empty:
        st.markdown('<div class="section-label">Price Chart</div>', unsafe_allow_html=True)
        fig = make_candlestick_chart(data["daily_df"], data["ticker"])
        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False},
            key=f"candlestick_{data['ticker']}",
        )

        st.markdown('<div class="section-label">Momentum Oscillators</div>', unsafe_allow_html=True)
        st.plotly_chart(
            make_rsi_macd_chart(data["daily_df"]),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"rsi_macd_{data['ticker']}",
        )

        plan_b = data["plan_b"]
        if plan_b:
            st.plotly_chart(
                make_range_bar(price, plan_b["week52_low"], plan_b["week52_high"]),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"range_bar_{data['ticker']}",
            )

    col1, col2 = st.columns(2)
    with col1:
        render_plan_a(data["plan_a"])
    with col2:
        render_plan_b(data["plan_b"])

    st.markdown('<div class="section-label">Conviction Score</div>', unsafe_allow_html=True)
    render_conviction(data["conviction"], key_suffix=data["ticker"])

    # Volume confirmation note
    vol_conf = data.get("volume_confirmation")
    if vol_conf:
        if vol_conf.get("divergence"):
            st.caption("📊 Volume signal: **price/volume divergence** — move lacks OBV confirmation.")
        elif vol_conf.get("confirmed"):
            st.caption("📊 Volume signal: **confirmed** — OBV trend agrees with price trend.")

    # News
    st.markdown('<div class="section-label">Latest News</div>', unsafe_allow_html=True)
    news = data.get("news", [])
    from utils.data import score_headline_sentiment
    sentiments = [score_headline_sentiment(n.get("title", "")) for n in news]

    col_news, col_donut = st.columns([3, 1])
    with col_news:
        render_news_feed(news, sentiments)
    with col_donut:
        bd = data["news_sentiment"]["breakdown"]
        fig = make_sentiment_donut(bd)
        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False},
            key=f"sentiment_donut_{data['ticker']}",
        )
        label = data["news_sentiment"]["label"]
        score = data["news_sentiment"]["score"]
        sentiment_color = {
            "Bullish": "#3FB950", "Bearish": "#F85149",
            "Neutral": "#D29922", "Mixed": "#58A6FF",
        }.get(label, "#8B949E")
        st.markdown(
            f'<div style="text-align:center;font-family:monospace;font-size:12px;'
            f'color:{sentiment_color};font-weight:700">{label} ({score:+.2f})</div>',
            unsafe_allow_html=True,
        )


# ── Tactical Blueprint & Executive Cards Components ───────────────────────────

def render_tactical_executive_cards(
    last_price: float,
    ib: dict[str, Any],
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
    currency: str = "₹",
) -> None:
    """
    Renders responsive, beautifully styled executive cards for the Intraday Tactical Blueprint:
      1. Current Price
      2. Opening Direction (with colored status badge + scrollable impulse explanation)
      3. Trend Duration Before Flip (bars / mins + inflection time)
      4. Tactical Recommended Action (with action badge + scrollable execution posture)
    """
    c = currency
    opening_bias = ib.get("opening_bias", "⚪ FLAT / CONSOLIDATING")
    primary_action = ib.get("primary_action", "WAIT FOR ORB")
    trend_bars = ib.get("trend_duration_bars", 6)
    trend_mins = ib.get("trend_duration_mins", 30)
    flip_time = ib.get("flip_time_est", "10:00 AM")

    # Determine status badges and colors
    if "RISE" in opening_bias.upper() or "BULLISH" in opening_bias.upper():
        open_cls = "card-bullish"
        open_badge_cls = "tactical-badge-up"
        open_badge_txt = "🟢 RISE / BULLISH OPEN"
    elif "FALL" in opening_bias.upper() or "BEARISH" in opening_bias.upper():
        open_cls = "card-bearish"
        open_badge_cls = "tactical-badge-down"
        open_badge_txt = "🔴 FALL / BEARISH DRAG"
    else:
        open_cls = "card-neutral"
        open_badge_cls = "tactical-badge-flat"
        open_badge_txt = "⚪ FLAT / RANGE-BOUND"

    if "BUY" in primary_action.upper():
        action_cls = "card-bullish"
        action_badge_cls = "tactical-badge-up"
        action_badge_txt = "🟢 BUY SETUP"
    elif "SELL" in primary_action.upper() or "SHORT" in primary_action.upper():
        action_cls = "card-bearish"
        action_badge_cls = "tactical-badge-down"
        action_badge_txt = "🔴 SHORT / EXIT"
    else:
        action_cls = "card-action"
        action_badge_cls = "tactical-badge-action"
        action_badge_txt = "🔵 ORB BREAKOUT"

    html = f"""
    <div class="tactical-blueprint-grid">
        <div class="tactical-card">
            <div class="tactical-card-label">Current Reference Price</div>
            <div style="font-size:22px;font-weight:700;font-family:var(--mono);color:var(--text-primary);">
                {c}{last_price:,.2f}
            </div>
            <div class="tactical-card-sub">Last Traded Price (LTP)</div>
        </div>
        <div class="tactical-card {open_cls}">
            <div class="tactical-card-label">Opening Direction</div>
            <div>
                <span class="tactical-badge {open_badge_cls}">{open_badge_txt}</span>
                <div class="tactical-scroll-text" title="{esc(opening_bias)}">{esc(opening_bias)}</div>
            </div>
            <div class="tactical-card-sub">Session Opening Impulse</div>
        </div>
        <div class="tactical-card card-action">
            <div class="tactical-card-label">Trend Duration Before Flip</div>
            <div style="font-size:16px;font-weight:600;font-family:var(--mono);color:var(--blue);">
                {trend_bars} bars ({trend_mins} mins)
            </div>
            <div class="tactical-card-sub" style="color:var(--amber);">⚡ Inflection @ {esc(flip_time)}</div>
        </div>
        <div class="tactical-card {action_cls}">
            <div class="tactical-card-label">Tactical Recommended Action</div>
            <div>
                <span class="tactical-badge {action_badge_cls}">{action_badge_txt}</span>
                <div class="tactical-scroll-text" title="{esc(primary_action)}">{esc(primary_action)}</div>
            </div>
            <div class="tactical-card-sub">Primary Execution Posture</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_actionable_levels_bar(
    last_price: float,
    ib: dict[str, Any],
    stop_loss: float = 0.0,
    take_profit: float = 0.0,
    currency: str = "₹",
) -> None:
    """Renders the 5 actionable execution price levels in a structured grid."""
    c = currency
    buy_entry = ib.get("buy_entry", last_price)
    buy_breakout = ib.get("buy_breakout", last_price)
    target1 = ib.get("sell_target_1", take_profit or last_price)
    target2 = ib.get("sell_target_2", take_profit or last_price)
    stop = ib.get("stop_loss", stop_loss or last_price)
    day_high = ib.get("expected_day_high", last_price)
    day_low = ib.get("expected_day_low", last_price)

    t1_pct = round(((target1 - last_price) / last_price) * 100.0, 2) if last_price > 0 else 0.0
    t2_pct = round(((target2 - last_price) / last_price) * 100.0, 2) if last_price > 0 else 0.0
    stop_pct = round(((last_price - stop) / last_price) * 100.0, 2) if last_price > 0 else 0.0

    l_col1, l_col2, l_col3, l_col4, l_col5 = st.columns(5)
    l_col1.metric("Optimal Entry", f"{c}{buy_entry:,.2f}", f"Breakout: {c}{buy_breakout:,.2f}", help="Price level to enter on pullback dip or on momentum breakout")
    l_col2.metric("Target 1 (Scalp)", f"{c}{target1:,.2f}", f"{'+' if t1_pct >= 0 else ''}{t1_pct}%", help="First profit taking target (Conservative/Scalp)")
    l_col3.metric("Target 2 (Runner)", f"{c}{target2:,.2f}", f"{'+' if t2_pct >= 0 else ''}{t2_pct}%", help="Extended profit target for remaining runner position")
    l_col4.metric("Protective Stop Loss", f"{c}{stop:,.2f}", f"-{stop_pct}%", help="Strict exit price level to invalidate setup")
    l_col5.metric("Expected Session Range", f"H: {c}{day_high:,.1f}", f"L: {c}{day_low:,.1f}", help="Statistical expected Day High (+%) and Day Low (-%) range")


# ── ELI5 (Explain Like I'm 5) & Mentorship Components ─────────────────────────

def render_eli5_box(title: str, explanation: str, key_rules: list[str] | None = None) -> None:
    """Renders a friendly, jargon-free beginner explanation box."""
    rules_html = ""
    if key_rules:
        rules_html = "<div style='margin-top:8px;font-size:12px;color:var(--text-secondary);'><strong>🎓 Pro Rules for Success:</strong><ul style='margin:4px 0 0 16px;padding:0;'>"
        for r in key_rules:
            rules_html += f"<li>{esc(r)}</li>"
        rules_html += "</ul></div>"

    html = f"""
    <div class="eli5-box">
        <div class="eli5-header">
            <span>🧠 Explain Like I'm 5:</span>
            <span>{esc(title)}</span>
        </div>
        <div class="eli5-body">
            {esc(explanation)}
        </div>
        {rules_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_wealth_compounder_card(fund_data: dict[str, Any], currency: str = "₹") -> None:
    """Renders a long-term wealth compounder card with fundamental quality metrics and Moat badge."""
    c = currency
    tick = fund_data.get("ticker", "")
    name = fund_data.get("company_name", tick)
    sec = fund_data.get("sector", "Diversified")
    price = fund_data.get("current_price", 0.0)
    score = fund_data.get("fundamental_quality_score", 50.0)
    moat_badge = fund_data.get("moat_badge", "MODERATE")
    tier = fund_data.get("compounder_tier", "AA Quality")
    cagr = fund_data.get("expected_cagr_pct", 15.0)
    t1y = fund_data.get("target_1y", price)
    t3y = fund_data.get("target_3y", price)
    t5y = fund_data.get("target_5y", price)
    pe = fund_data.get("trailing_pe", "N/A")
    roe = fund_data.get("roe_pct", "N/A")
    de = fund_data.get("debt_to_equity", "N/A")

    moat_cls = "moat-wide" if moat_badge == "WIDE MOAT" else "moat-narrow" if moat_badge == "NARROW MOAT" else "moat-none"

    html = f"""
    <div class="top10-card" style="border-top: 3px solid #3FB950;">
        <div class="top10-header">
            <div>
                <span class="moat-pill {moat_cls}">🏰 {esc(moat_badge)}</span>
                <span class="top10-symbol">&nbsp;{esc(tick)}</span>
                <div class="top10-sector">{esc(name)} · {esc(sec)}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-family:var(--mono);font-size:18px;font-weight:700;color:#3FB950;">
                    ~{cagr:.1f}% CAGR
                </div>
                <div style="font-size:11px;color:var(--text-muted);font-family:var(--mono);">
                    Quality Score: {score:.0f}/100
                </div>
            </div>
        </div>
        <div style="font-size:12px;color:var(--blue);font-weight:600;margin-bottom:8px;font-family:var(--mono);">
            {esc(tier)}
        </div>
        <div class="top10-grid-levels" style="grid-template-columns: repeat(3, 1fr);">
            <div class="level-item">
                <span class="level-label">P/E Ratio</span>
                <span class="level-val">{pe}</span>
            </div>
            <div class="level-item">
                <span class="level-label">Return on Equity</span>
                <span class="level-val" style="color:#3FB950;">{roe}%</span>
            </div>
            <div class="level-item">
                <span class="level-label">Debt / Equity</span>
                <span class="level-val">{de}</span>
            </div>
        </div>
        <div class="top10-grid-levels" style="grid-template-columns: repeat(3, 1fr);background:#161B22;">
            <div class="level-item">
                <span class="level-label">1-Year Target</span>
                <span class="level-val val-target">{c}{t1y:,.0f}</span>
            </div>
            <div class="level-item">
                <span class="level-label">3-Year Target</span>
                <span class="level-val val-profit">{c}{t3y:,.0f}</span>
            </div>
            <div class="level-item">
                <span class="level-label">5-Year Target</span>
                <span class="level-val" style="color:#BC8CFF;font-weight:700;">{c}{t5y:,.0f}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)



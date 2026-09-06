"""
Plotly chart builders for FinVision.
All charts use a dark theme consistent with the CSS palette.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils import indicators as ti

# ── Colour constants (match CSS vars) ────────────────────────────────────────
BG      = "#161B22"
BG_PLOT = "#0D1117"
GRID    = "#21262D"
TEXT    = "#E6EDF3"
TEXT2   = "#8B949E"
GREEN   = "#3FB950"
RED     = "#F85149"
AMBER   = "#D29922"
BLUE    = "#58A6FF"
PURPLE  = "#BC8CFF"
WHITE   = "#E6EDF3"

_LAYOUT_BASE = dict(
    paper_bgcolor=BG_PLOT,
    plot_bgcolor=BG_PLOT,
    font=dict(family="IBM Plex Mono, monospace", color=TEXT2, size=11),
    margin=dict(l=12, r=12, t=32, b=12),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor=GRID,
        font=dict(size=10),
    ),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, showgrid=True),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, showgrid=True),
)


def _apply_base(fig: go.Figure) -> go.Figure:
    fig.update_layout(**_LAYOUT_BASE)
    return fig


# ── Candlestick + SMA + volume chart ─────────────────────────────────────────

def make_candlestick_chart(
    df: pd.DataFrame,
    ticker: str,
    sma_periods: list[int] | None = None,
) -> go.Figure:
    """
    Full OHLCV chart with optional SMA overlays and volume bars.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=TEXT2))
        return _apply_base(fig)

    sma_periods = sma_periods or [20, 50, 200]
    sma_colors  = [AMBER, BLUE, PURPLE]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.02,
    )

    # Candles
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker,
            increasing=dict(line=dict(color=GREEN), fillcolor=GREEN),
            decreasing=dict(line=dict(color=RED),   fillcolor=RED),
        ),
        row=1, col=1,
    )

    # SMAs
    close = df["Close"].astype(float)
    for period, colour in zip(sma_periods, sma_colors):
        if len(df) >= period:
            s = close.rolling(period).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=s,
                    name=f"SMA{period}",
                    line=dict(color=colour, width=1.2, dash="dot" if period == 200 else "solid"),
                    opacity=0.8,
                ),
                row=1, col=1,
            )

    # Volume
    if "Volume" in df.columns:
        vol_colors = [
            GREEN if c >= o else RED
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume",
                marker_color=vol_colors,
                opacity=0.6,
            ),
            row=2, col=1,
        )
        # Volume MA
        vol = df["Volume"].astype(float)
        vol_ma = vol.rolling(20).mean()
        fig.add_trace(
            go.Scatter(
                x=df.index, y=vol_ma,
                name="Vol MA20",
                line=dict(color=AMBER, width=1),
                opacity=0.8,
            ),
            row=2, col=1,
        )

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=f"<b>{ticker}</b> — Price History", font=dict(color=TEXT, size=13)),
        xaxis_rangeslider_visible=False,
        height=420,
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Vol",   row=2, col=1)
    return fig


# ── 5-minute intraday chart with EMA ─────────────────────────────────────────

def make_intraday_chart(
    df: pd.DataFrame,
    ticker: str,
    entry_price: float | None = None,
    target_price: float | None = None,
    vwap_series: pd.Series | None = None,
    orb: dict | None = None,
) -> go.Figure:
    """5-min candles with EMA20, optional VWAP overlay, opening-range shading, + volume."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No intraday data", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=TEXT2))
        return _apply_base(fig)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.02,
    )

    # Opening range shaded zone (drawn first so it sits behind the candles)
    if orb and orb.get("available"):
        fig.add_hrect(
            y0=orb["low"], y1=orb["high"],
            fillcolor="rgba(210,153,34,0.08)",
            line_width=0,
            row=1, col=1,
        )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"],   close=df["Close"],
            name=ticker,
            increasing=dict(line=dict(color=GREEN), fillcolor=GREEN),
            decreasing=dict(line=dict(color=RED),   fillcolor=RED),
        ),
        row=1, col=1,
    )

    # EMA 20
    close = df["Close"].astype(float)
    ema20 = close.ewm(span=20, adjust=False).mean()
    fig.add_trace(
        go.Scatter(
            x=df.index, y=ema20,
            name="EMA20",
            line=dict(color=PURPLE, width=1.5),
        ),
        row=1, col=1,
    )

    # VWAP overlay
    if vwap_series is not None and not vwap_series.empty:
        fig.add_trace(
            go.Scatter(
                x=vwap_series.index, y=vwap_series,
                name="VWAP",
                line=dict(color=AMBER, width=1.5, dash="dot"),
            ),
            row=1, col=1,
        )

    # Horizontal reference lines
    if entry_price:
        fig.add_hline(
            y=entry_price, line_color=BLUE, line_width=1.2,
            line_dash="dash", annotation_text="Entry",
            annotation_font_color=BLUE, row=1, col=1,
        )
    if target_price:
        fig.add_hline(
            y=target_price, line_color=GREEN, line_width=1.2,
            line_dash="dash", annotation_text="Target",
            annotation_font_color=GREEN, row=1, col=1,
        )

    # Volume
    if "Volume" in df.columns:
        vol = df["Volume"].astype(float)
        vol_ma = vol.rolling(20).mean()
        vol_colors = [
            GREEN if c >= o else RED
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(
            go.Bar(x=df.index, y=vol, name="Volume",
                   marker_color=vol_colors, opacity=0.55),
            row=2, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=vol_ma, name="Vol MA20",
                       line=dict(color=AMBER, width=1)),
            row=2, col=1,
        )

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=f"<b>{ticker}</b> — 5-min Intraday", font=dict(color=TEXT, size=13)),
        xaxis_rangeslider_visible=False,
        height=400,
    )
    return fig


# ── Conviction score breakdown bar chart ─────────────────────────────────────

def make_conviction_chart(conviction: dict) -> go.Figure:
    """Horizontal stacked bar showing conviction score breakdown."""
    breakdown = conviction.get("breakdown", {})
    if not breakdown:
        return go.Figure()

    labels = list(breakdown.keys())
    values = list(breakdown.values())
    colours = [GREEN, BLUE, AMBER, PURPLE, RED]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker=dict(
                color=colours[:len(labels)],
                line=dict(width=0),
            ),
            text=[f"{v}" for v in values],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color=TEXT, size=10, family="IBM Plex Mono"),
        )
    )
    layout = {**_LAYOUT_BASE}
    layout["margin"] = dict(l=8, r=8, t=8, b=8)
    layout["xaxis"] = dict(range=[0, 30], gridcolor=GRID)
    layout["yaxis"] = dict(gridcolor="rgba(0,0,0,0)")
    fig.update_layout(
        **layout,
        height=160,
        showlegend=False,
    )
    return fig


# ── News sentiment mini chart ─────────────────────────────────────────────────

def make_sentiment_donut(breakdown: dict) -> go.Figure:
    """Donut chart showing news sentiment distribution."""
    labels = ["Positive", "Negative", "Neutral"]
    values = [
        breakdown.get("positive", 0),
        breakdown.get("negative", 0),
        breakdown.get("neutral", 0),
    ]
    colours = [GREEN, RED, AMBER]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker=dict(colors=colours, line=dict(color=BG_PLOT, width=2)),
            textinfo="percent",
            textfont=dict(size=10, family="IBM Plex Mono"),
        )
    )
    layout = {**_LAYOUT_BASE}
    layout["legend"] = dict(orientation="h", x=0, y=-0.15, font=dict(size=9))
    layout["margin"] = dict(l=0, r=0, t=0, b=0)
    fig.update_layout(
        **layout,
        height=140,
        showlegend=True,
    )
    return fig


# ── 52-week range bar ─────────────────────────────────────────────────────────

def make_range_bar(current: float, low52: float, high52: float) -> go.Figure:
    """Simple gauge-style bar showing where current price sits in 52w range."""
    pct = (current - low52) / max(high52 - low52, 1e-9) * 100

    fig = go.Figure(
        go.Bar(
            x=[pct],
            y=["52w Range"],
            orientation="h",
            marker_color=BLUE,
            width=0.4,
        )
    )
    fig.add_vline(x=pct, line_color=WHITE, line_width=2)
    layout = {**_LAYOUT_BASE}
    layout["margin"] = dict(l=8, r=8, t=4, b=4)
    layout["xaxis"] = dict(range=[0, 100], gridcolor=GRID, ticksuffix="%", tickfont=dict(size=9))
    layout["yaxis"] = dict(gridcolor="rgba(0,0,0,0)")
    fig.update_layout(
        **layout,
        height=80,
        showlegend=False,
        annotations=[
            dict(x=2,    y=0, text=f"₹{low52:,.0f}",  showarrow=False,
                 font=dict(color=TEXT2, size=9), xanchor="left"),
            dict(x=98,   y=0, text=f"₹{high52:,.0f}", showarrow=False,
                 font=dict(color=TEXT2, size=9), xanchor="right"),
            dict(x=pct,  y=0.55, text=f"<b>₹{current:,.1f}</b>",
                 showarrow=False, font=dict(color=WHITE, size=10), xanchor="center"),
        ],
    )
    return fig


# ── RSI + MACD combo chart ────────────────────────────────────────────────────

def make_rsi_macd_chart(df: pd.DataFrame) -> go.Figure:
    """
    Two-panel oscillator chart: RSI (top) with overbought/oversold bands,
    MACD histogram + signal lines (bottom). Used to visually back up the
    conviction score's momentum components.
    """
    if df.empty or len(df) < 30:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data for RSI/MACD", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=TEXT2))
        return _apply_base(fig)

    close = df["Close"].astype(float)
    rsi_s = ti.rsi(close)
    macd_d = ti.macd(close)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.45, 0.55],
        vertical_spacing=0.04,
        subplot_titles=("RSI (14)", "MACD (12, 26, 9)"),
    )

    # RSI
    fig.add_trace(
        go.Scatter(x=df.index, y=rsi_s, name="RSI", line=dict(color=BLUE, width=1.5)),
        row=1, col=1,
    )
    fig.add_hline(y=70, line_color=RED, line_width=1, line_dash="dot", row=1, col=1)
    fig.add_hline(y=30, line_color=GREEN, line_width=1, line_dash="dot", row=1, col=1)
    fig.add_hline(y=50, line_color=GRID, line_width=1, row=1, col=1)

    # MACD
    hist_colors = [GREEN if v >= 0 else RED for v in macd_d["hist"].fillna(0)]
    fig.add_trace(
        go.Bar(x=df.index, y=macd_d["hist"], name="Histogram",
               marker_color=hist_colors, opacity=0.6),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=macd_d["macd"], name="MACD",
                   line=dict(color=BLUE, width=1.3)),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=macd_d["signal"], name="Signal",
                   line=dict(color=AMBER, width=1.3)),
        row=2, col=1,
    )

    layout = {**_LAYOUT_BASE}
    layout["legend"] = dict(orientation="h", x=0, y=1.12, font=dict(size=9))
    fig.update_layout(
        **layout,
        height=320,
        showlegend=True,
    )
    fig.update_yaxes(range=[0, 100], row=1, col=1)
    for ann in fig.layout.annotations:
        ann.font = dict(color=TEXT2, size=11)
    return fig


# ── Intraday probability cone chart ───────────────────────────────────────────

def make_probability_cone_chart(cone: dict, ticker: str) -> go.Figure:
    """
    Renders the intraday probability cone as a banded area chart: a median
    line with 25-75 and 10-90 percentile shading. This is intentionally
    NOT a single confident line — the width of the bands is the point,
    since it visually communicates how uncertain the "typical path" really
    is, especially when built from a small number of days.
    """
    if not cone.get("available"):
        fig = go.Figure()
        fig.add_annotation(
            text=cone.get("reason", "Insufficient data"), x=0.5, y=0.5,
            showarrow=False, font=dict(color=TEXT2, size=12),
        )
        return _apply_base(fig)

    minutes = cone["minutes"]

    fig = go.Figure()

    # Outer band (10-90 percentile) — lightest shading
    fig.add_trace(go.Scatter(
        x=minutes + minutes[::-1],
        y=cone["p90"] + cone["p10"][::-1],
        fill="toself", fillcolor="rgba(88,166,255,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="10th–90th percentile", showlegend=True,
        hoverinfo="skip",
    ))

    # Inner band (25-75 percentile) — denser shading
    fig.add_trace(go.Scatter(
        x=minutes + minutes[::-1],
        y=cone["p75"] + cone["p25"][::-1],
        fill="toself", fillcolor="rgba(88,166,255,0.22)",
        line=dict(color="rgba(0,0,0,0)"),
        name="25th–75th percentile", showlegend=True,
        hoverinfo="skip",
    ))

    # Median line
    fig.add_trace(go.Scatter(
        x=minutes, y=cone["median_pct_from_open"],
        line=dict(color=BLUE, width=2.5),
        name="Median path", mode="lines",
    ))

    fig.add_hline(y=0, line_color=GRID, line_width=1, line_dash="dot")

    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(
            text=f"<b>{ticker}</b> — Typical Intraday Path ({cone['n_days']} days, % from open)",
            font=dict(color=TEXT, size=13),
        ),
        height=340,
        xaxis_title="Minutes since market open",
        yaxis_title="% change from session open",
    )
    return fig


# ── Lead-lag correlation chart ────────────────────────────────────────────────

def make_lead_lag_chart(lead_lag: dict) -> go.Figure:
    """Bar chart of correlation coefficient by lag, with significance markers."""
    if not lead_lag.get("available"):
        fig = go.Figure()
        fig.add_annotation(
            text=lead_lag.get("reason", "Insufficient data"), x=0.5, y=0.5,
            showarrow=False, font=dict(color=TEXT2, size=12),
        )
        return _apply_base(fig)

    results = lead_lag["results"]
    lags = [r["lag"] for r in results]
    corrs = [r["correlation"] for r in results]
    colors = [GREEN if r["significant"] else GRID for r in results]
    text_labels = [
        f"p={r['p_value']:.3f}{'  ✓ sig.' if r['significant'] else ''}"
        for r in results
    ]

    fig = go.Figure(go.Bar(
        x=lags, y=corrs,
        marker_color=colors,
        text=text_labels,
        textposition="outside",
        textfont=dict(size=9, color=TEXT2),
    ))
    fig.add_hline(y=0, line_color=GRID, line_width=1)

    fig.update_layout(
        **_LAYOUT_BASE,
        height=240,
        xaxis_title="Lag (periods leader leads target by)",
        yaxis_title="Correlation",
        showlegend=False,
    )
    return fig


# ── Correlation matrix heatmap ────────────────────────────────────────────────

def make_correlation_heatmap(corr_data: dict) -> go.Figure:
    """Heatmap of same-day return correlation across multiple tickers."""
    if not corr_data.get("available"):
        fig = go.Figure()
        fig.add_annotation(
            text=corr_data.get("reason", "Insufficient data"), x=0.5, y=0.5,
            showarrow=False, font=dict(color=TEXT2, size=12),
        )
        return _apply_base(fig)

    tickers = corr_data["tickers"]
    matrix = corr_data["matrix"]

    fig = go.Figure(go.Heatmap(
        x=tickers, y=tickers, z=matrix,
        colorscale=[[0, RED], [0.5, BG_PLOT], [1, GREEN]],
        zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont=dict(size=10),
        colorbar=dict(thickness=12, len=0.8),
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        height=max(280, 50 * len(tickers)),
        title=dict(
            text=f"Same-day return correlation (n={corr_data['n_observations']} days)",
            font=dict(color=TEXT, size=12),
        ),
    )
    return fig



def plot_intraday_5m_session_forecast(session_fc: dict[str, Any], title: Optional[str] = None) -> go.Figure:
    """
    Renders an expansive candlestick trajectory chart for either:
      - 15-Minute Institutional Standard (25 bars, low-noise signal)
      - 5-Minute Granular Scalp (75 bars)
    """
    tf = session_fc.get("timeframe", "15m")
    if not title:
        if tf == "15m":
            title = "15-Minute Institutional Candlestick Forecast (09:15 - 15:30 IST) — Low-Noise"
        else:
            title = "5-Minute Session Candlestick Forecast (09:15 - 15:30 IST)"

    df = session_fc.get("trajectory_df", pd.DataFrame())
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**_LAYOUT_BASE, title="No Intraday Forecast Data")
        return fig

    # Sanitize any rogue 0 or <=0 values in price/envelope columns
    for col in ["open", "high", "low", "close", "vwap", "upper_80", "lower_80"]:
        if col in df.columns:
            df[col] = df[col].replace(0, np.nan).bfill().ffill()

    if "ema9" not in df.columns:
        df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()

    # Calculate clean Y-axis range with healthy padding around the price action
    all_lows = []
    all_highs = []
    for col in ["low", "lower_80", "vwap", "ema9"]:
        if col in df.columns:
            s = df[col].dropna()
            s_valid = s[s > 0]
            if not s_valid.empty:
                all_lows.append(float(s_valid.min()))
    for col in ["high", "upper_80", "vwap", "ema9"]:
        if col in df.columns:
            s = df[col].dropna()
            s_valid = s[s > 0]
            if not s_valid.empty:
                all_highs.append(float(s_valid.max()))

    y_axis_range = None
    if all_lows and all_highs:
        y_min = min(all_lows)
        y_max = max(all_highs)
        pad = max(0.5, (y_max - y_min) * 0.08)
        y_axis_range = [round(y_min - pad, 2), round(y_max + pad, 2)]

    fig = go.Figure()

    # 1. Subtle 80% Confidence Interval Corridor
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["upper_80"],
        mode="lines",
        line=dict(color="rgba(88, 166, 255, 0.35)", width=1, dash="dot"),
        name="80% CI Upper",
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["lower_80"],
        mode="lines",
        fill="tonexty",
        fillcolor="rgba(41, 98, 255, 0.06)",
        line=dict(color="rgba(88, 166, 255, 0.35)", width=1, dash="dot"),
        name="80% CI Envelope",
        hoverinfo="skip"
    ))

    # 2. Unified Full-Width 5-Minute Candlesticks (centered, sharp, identical to live market chart)
    fig.add_trace(go.Candlestick(
        x=df["time"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="5m Candles",
        increasing_line_color="#00E676",
        decreasing_line_color="#FF5252",
        increasing_fillcolor="#00E676",
        decreasing_fillcolor="#FF5252",
        line=dict(width=1.2)
    ))

    # 3. Dynamic Orange VWAP Line
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["vwap"],
        mode="lines",
        name="VWAP",
        line=dict(color="#FF9800", width=2.0)
    ))

    # 4. Dynamic Blue EMA 9 Line
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["ema9"],
        mode="lines",
        name="EMA 9",
        line=dict(color="#2962FF", width=1.75)
    ))

    # 5. Opening Range Breakout (ORB 30m) boundaries
    orb_high = session_fc.get("orb_30m_high")
    orb_low = session_fc.get("orb_30m_low")
    if orb_high and orb_low:
        fig.add_hline(
            y=orb_high,
            line_dash="dot",
            line_color="rgba(0, 230, 118, 0.55)",
            annotation_text=f"ORB High: ₹{orb_high:.2f}",
            annotation_position="top left",
            annotation_font=dict(color="#00E676", size=10)
        )
        fig.add_hline(
            y=orb_low,
            line_dash="dot",
            line_color="rgba(255, 82, 82, 0.55)",
            annotation_text=f"ORB Low: ₹{orb_low:.2f}",
            annotation_position="bottom left",
            annotation_font=dict(color="#FF5252", size=10)
        )

    # Clean, High-Legibility Layout matching the live intraday chart
    yaxis_config = dict(
        gridcolor="rgba(255, 255, 255, 0.08)",
        zerolinecolor="rgba(255, 255, 255, 0.15)",
        tickfont=dict(color="#F0F6FC", size=11, family="monospace"),
        tickformat=".2f",
        tickprefix="₹",
        nticks=18,
        side="right",
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikethickness=1,
        spikecolor="rgba(255, 255, 255, 0.3)",
        spikedash="dot"
    )
    if y_axis_range:
        yaxis_config["range"] = y_axis_range

    fig.update_layout(
        title=dict(text=title, font=dict(color="#E6EDF3", size=14, family="sans-serif")),
        height=620,
        hovermode="x unified",
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.07)",
            rangeslider=dict(visible=False),
            tickfont=dict(color="#8B949E", size=10),
            nticks=16,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikecolor="rgba(255, 255, 255, 0.3)",
            spikedash="dot"
        ),
        yaxis=yaxis_config,
        margin=dict(l=10, r=65, t=35, b=25),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(22, 27, 34, 0.8)",
            font=dict(color="#E6EDF3", size=11)
        ),
        plot_bgcolor="rgba(13, 17, 23, 0.6)",
        paper_bgcolor="rgba(0, 0, 0, 0)"
    )
    return fig


# ── Advanced Interactive Manual Trading Chart (Kite / Groww Grade) ───────────

def make_advanced_manual_trading_chart(
    df: pd.DataFrame,
    ticker: str,
    timeframe: str = "1D",
    show_ema9: bool = True,
    show_ema21: bool = True,
    show_ema50: bool = False,
    show_ema200: bool = False,
    show_vwap: bool = True,
    show_supertrend: bool = False,
    show_bollinger: bool = False,
    show_pivots: bool = False,
    pivots_dict: dict | None = None,
    show_rsi: bool = True,
    show_macd: bool = False,
    entry_level: float | None = None,
    target_level: float | None = None,
    stop_loss_level: float | None = None,
) -> go.Figure:
    """
    Institutional multi-indicator chart designed for manual trading.
    Replicates TradingView/Kite/Groww ergonomics with customizable overlays.
    """
    if df.empty or len(df) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No candlestick data available for {ticker} ({timeframe})",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=TEXT2, size=14)
        )
        return _apply_base(fig)

    # Determine subplot rows
    has_rsi = show_rsi and len(df) > 14
    has_macd = show_macd and len(df) > 26

    rows = 1
    row_heights = [1.0]
    if has_rsi and has_macd:
        rows = 3
        row_heights = [0.64, 0.18, 0.18]
    elif has_rsi or has_macd:
        rows = 2
        row_heights = [0.76, 0.24]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        specs=[[{"secondary_y": True}]] + [[{"secondary_y": False}]] * (rows - 1)
    )

    # 1. Main Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=f"{ticker} ({timeframe})",
            increasing=dict(line=dict(color=GREEN, width=1), fillcolor=GREEN),
            decreasing=dict(line=dict(color=RED, width=1), fillcolor=RED),
        ),
        row=1, col=1, secondary_y=False
    )

    close = df["Close"].astype(float)

    # 2. Volume Overlay (TradingView style on secondary Y)
    if "Volume" in df.columns:
        vol_colors = [
            "rgba(63, 185, 80, 0.22)" if c >= o else "rgba(248, 81, 73, 0.22)"
            for c, o in zip(df["Close"], df["Open"])
        ]
        max_vol = float(df["Volume"].max()) if not df["Volume"].empty else 1.0
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume",
                marker_color=vol_colors,
                showlegend=False,
            ),
            row=1, col=1, secondary_y=True
        )
        fig.update_yaxes(
            range=[0, max_vol * 4.0],  # Keeps volume bars confined to lower 25% of chart
            showgrid=False,
            showticklabels=False,
            secondary_y=True,
            row=1, col=1
        )

    # 3. Moving Averages
    if show_ema9 and len(df) >= 9:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=ti.ema(close, 9),
                name="EMA 9",
                line=dict(color="#38BDF8", width=1.2),
            ),
            row=1, col=1, secondary_y=False
        )

    if show_ema21 and len(df) >= 21:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=ti.ema(close, 21),
                name="EMA 21",
                line=dict(color="#FBBF24", width=1.3),
            ),
            row=1, col=1, secondary_y=False
        )

    if show_ema50 and len(df) >= 50:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=ti.ema(close, 50),
                name="EMA 50",
                line=dict(color="#A855F7", width=1.4),
            ),
            row=1, col=1, secondary_y=False
        )

    if show_ema200 and len(df) >= 150:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=ti.ema(close, min(200, len(df))),
                name=f"EMA {min(200, len(df))}",
                line=dict(color="#F43F5E", width=1.6, dash="dash"),
            ),
            row=1, col=1, secondary_y=False
        )

    # 4. VWAP Overlay
    if show_vwap and "Volume" in df.columns:
        vwap_vals = ti.vwap(df)
        if not vwap_vals.dropna().empty:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=vwap_vals,
                    name="VWAP",
                    line=dict(color="#FB923C", width=1.8),
                ),
                row=1, col=1, secondary_y=False
            )

    # 5. Supertrend Overlay
    if show_supertrend and len(df) > 10:
        st_data = ti.supertrend(df, period=10, multiplier=3.0)
        st_line = st_data["supertrend"]
        if not st_line.dropna().empty:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=st_line,
                    name="Supertrend (10,3)",
                    line=dict(color="#10B981", width=1.5, dash="dot"),
                ),
                row=1, col=1, secondary_y=False
            )

    # 6. Bollinger Bands
    if show_bollinger and len(df) >= 20:
        bb = ti.bollinger_bands(close, period=20, std_dev=2.0)
        fig.add_trace(
            go.Scatter(
                x=df.index, y=bb["upper"],
                name="BB Upper",
                line=dict(color="rgba(148, 163, 184, 0.4)", width=1),
                showlegend=False
            ),
            row=1, col=1, secondary_y=False
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=bb["lower"],
                name="BB Lower",
                line=dict(color="rgba(148, 163, 184, 0.4)", width=1),
                fill="tonexty",
                fillcolor="rgba(148, 163, 184, 0.06)",
                showlegend=False
            ),
            row=1, col=1, secondary_y=False
        )

    # 7. Pivot Points (Horizontal Reference Lines)
    if show_pivots and pivots_dict:
        if "pivot" in pivots_dict:
            fig.add_hline(
                y=pivots_dict["pivot"], line_dash="dash", line_color="#F59E0B",
                annotation_text=f"P: ₹{pivots_dict['pivot']:.2f}",
                annotation_position="top right", row=1, col=1
            )
        if "r1" in pivots_dict:
            fig.add_hline(
                y=pivots_dict["r1"], line_dash="dot", line_color="#EF4444",
                annotation_text=f"R1: ₹{pivots_dict['r1']:.2f}",
                annotation_position="top right", row=1, col=1
            )
        if "s1" in pivots_dict:
            fig.add_hline(
                y=pivots_dict["s1"], line_dash="dot", line_color="#10B981",
                annotation_text=f"S1: ₹{pivots_dict['s1']:.2f}",
                annotation_position="bottom right", row=1, col=1
            )

    # 8. Order Levels (Entry, Target, Stop Loss)
    if entry_level and entry_level > 0:
        fig.add_hline(
            y=entry_level, line_dash="dash", line_color="#38BDF8", line_width=1.5,
            annotation_text=f"Entry: ₹{entry_level:.2f}",
            annotation_position="top left", row=1, col=1
        )
    if target_level and target_level > 0:
        fig.add_hline(
            y=target_level, line_dash="dash", line_color="#22C55E", line_width=1.5,
            annotation_text=f"Target: ₹{target_level:.2f}",
            annotation_position="top left", row=1, col=1
        )
    if stop_loss_level and stop_loss_level > 0:
        fig.add_hline(
            y=stop_loss_level, line_dash="dash", line_color="#EF4444", line_width=1.5,
            annotation_text=f"Stop: ₹{stop_loss_level:.2f}",
            annotation_position="bottom left", row=1, col=1
        )

    # 9. Subplots: RSI and MACD
    current_sub_row = 2
    if has_rsi:
        rsi_vals = ti.rsi(close, 14)
        fig.add_trace(
            go.Scatter(
                x=df.index, y=rsi_vals,
                name="RSI (14)",
                line=dict(color="#A855F7", width=1.5),
            ),
            row=current_sub_row, col=1
        )
        fig.add_hline(y=70, line_dash="dot", line_color="rgba(239, 68, 68, 0.6)", row=current_sub_row, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="rgba(34, 197, 94, 0.6)", row=current_sub_row, col=1)
        fig.update_yaxes(
            title_text="RSI", range=[10, 90],
            gridcolor=GRID, zerolinecolor=GRID,
            row=current_sub_row, col=1
        )
        current_sub_row += 1

    if has_macd:
        macd_dict = ti.macd(close)
        m_line = macd_dict["macd"]
        s_line = macd_dict["signal"]
        hist = macd_dict["hist"]
        hist_colors = [
            GREEN if val >= 0 else RED
            for val in hist
        ]
        fig.add_trace(
            go.Bar(
                x=df.index, y=hist,
                name="MACD Hist",
                marker_color=hist_colors,
                opacity=0.6,
            ),
            row=current_sub_row, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=m_line,
                name="MACD",
                line=dict(color=BLUE, width=1.2),
            ),
            row=current_sub_row, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=s_line,
                name="Signal",
                line=dict(color=AMBER, width=1.2),
            ),
            row=current_sub_row, col=1
        )
        fig.update_yaxes(
            title_text="MACD",
            gridcolor=GRID, zerolinecolor=GRID,
            row=current_sub_row, col=1
        )

    # Master Layout Configuration
    fig.update_layout(
        paper_bgcolor=BG_PLOT,
        plot_bgcolor=BG_PLOT,
        font=dict(family="IBM Plex Mono, monospace", color=TEXT2, size=11),
        margin=dict(l=10, r=60, t=35, b=20),
        height=680 if rows > 1 else 520,
        hovermode="x unified",
        xaxis=dict(
            gridcolor=GRID,
            rangeslider=dict(visible=False),
            showspikes=True,
            spikemode="across",
            spikethickness=1,
            spikecolor="rgba(255, 255, 255, 0.2)",
            spikedash="dot"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1,
            bgcolor="rgba(22, 27, 34, 0.7)",
            font=dict(size=10, color=TEXT)
        )
    )
    fig.update_yaxes(
        side="right",
        gridcolor=GRID,
        showspikes=True,
        spikemode="across",
        spikethickness=1,
        spikecolor="rgba(255, 255, 255, 0.2)",
        spikedash="dot",
        tickprefix="₹",
        tickformat=".2f",
        row=1, col=1, secondary_y=False
    )

    return fig
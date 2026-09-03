"""Global CSS injection for FinVision dashboard."""

import streamlit as st


def inject_css():
    st.markdown(
        """
        <style>
        /* ── Fonts ────────────────────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@300;400;500;600;700&display=swap');

        /* ── Root palette ─────────────────────────────────────────────────── */
        :root {
            --bg-base:        #0D1117;
            --bg-card:        #161B22;
            --bg-card-hover:  #1C2330;
            --border:         #21262D;
            --border-accent:  #30363D;
            --text-primary:   #E6EDF3;
            --text-secondary: #8B949E;
            --text-muted:     #484F58;
            --green:          #3FB950;
            --green-dim:      #1A4D2A;
            --red:            #F85149;
            --red-dim:        #4D1A1A;
            --amber:          #D29922;
            --amber-dim:      #3D2C0A;
            --blue:           #58A6FF;
            --blue-dim:       #0D2044;
            --purple:         #BC8CFF;
            --mono:           'IBM Plex Mono', monospace;
            --sans:           'Inter', sans-serif;
        }

        /* ── Global reset ─────────────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: var(--sans);
            background-color: var(--bg-base);
            color: var(--text-primary);
        }

        /* ── Streamlit chrome overrides ──────────────────────────────────── */
        .stApp { background-color: var(--bg-base); }
        .stSidebar { background-color: var(--bg-card) !important; border-right: 1px solid var(--border); }
        .stSidebar [data-testid="stSidebarContent"] { padding-top: 1rem; }

        /* Sidebar radio */
        div[data-testid="stRadio"] > label { display: none; }
        div[data-testid="stRadio"] div[role="radiogroup"] {
            gap: 4px;
            display: flex;
            flex-direction: column;
        }
        div[data-testid="stRadio"] label[data-baseweb="radio"] {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 10px 14px;
            cursor: pointer;
            transition: all 0.15s ease;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
        }
        div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-accent);
            color: var(--text-primary);
        }
        div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] {
            background: var(--blue-dim);
            border-color: var(--blue);
            color: var(--blue);
        }

        /* ── Sidebar logo ─────────────────────────────────────────────────── */
        .sidebar-logo {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 4px 4px;
        }
        .logo-icon { font-size: 28px; }
        .logo-text {
            font-family: var(--mono);
            font-size: 20px;
            font-weight: 600;
            color: var(--blue);
            letter-spacing: -0.5px;
        }
        .logo-tagline {
            font-size: 11px;
            color: var(--text-muted);
            font-family: var(--mono);
            padding: 0 4px;
            margin-top: -4px;
        }

        /* ── Page header ──────────────────────────────────────────────────── */
        .page-header {
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }
        .page-header h1 {
            font-size: 22px;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0 0 4px;
            letter-spacing: -0.3px;
        }
        .page-header p {
            font-size: 13px;
            color: var(--text-secondary);
            margin: 0;
        }

        /* ── Metric cards ─────────────────────────────────────────────────── */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin: 12px 0;
        }
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
            transition: border-color 0.15s;
        }
        .metric-card:hover { border-color: var(--border-accent); }
        .metric-label {
            font-size: 11px;
            color: var(--text-muted);
            font-family: var(--mono);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 20px;
            font-weight: 600;
            font-family: var(--mono);
            color: var(--text-primary);
            line-height: 1;
        }
        .metric-sub {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 4px;
        }
        .metric-up   { color: var(--green); }
        .metric-down { color: var(--red); }
        .metric-flat { color: var(--amber); }

        /* ── Plan boxes ───────────────────────────────────────────────────── */
        .plan-box {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px 20px;
            height: 100%;
        }
        .plan-box.plan-a { border-top: 3px solid var(--amber); }
        .plan-box.plan-b { border-top: 3px solid var(--purple); }
        .plan-title {
            font-family: var(--mono);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 12px;
        }
        .plan-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid var(--border);
        }
        .plan-row:last-child { border-bottom: none; }
        .plan-key { font-size: 12px; color: var(--text-secondary); }
        .plan-val { font-family: var(--mono); font-size: 14px; font-weight: 600; }
        .plan-val.buy  { color: var(--green); }
        .plan-val.sell { color: var(--purple); }
        .plan-val.stop { color: var(--red); }
        .plan-val.rate { color: var(--blue); }

        /* ── News cards ───────────────────────────────────────────────────── */
        .news-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-left: 3px solid var(--blue);
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 8px;
        }
        .news-card.sentiment-positive { border-left-color: var(--green); }
        .news-card.sentiment-negative { border-left-color: var(--red); }
        .news-card.sentiment-neutral  { border-left-color: var(--amber); }
        .news-headline {
            font-size: 13px;
            color: var(--text-primary);
            font-weight: 500;
            margin-bottom: 4px;
            line-height: 1.4;
        }
        .news-meta {
            font-size: 11px;
            color: var(--text-muted);
            font-family: var(--mono);
        }
        .news-badge {
            display: inline-block;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            font-family: var(--mono);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-positive { background: var(--green-dim);  color: var(--green); }
        .badge-negative { background: var(--red-dim);    color: var(--red);   }
        .badge-neutral  { background: var(--amber-dim);  color: var(--amber); }

        /* ── Candle pattern pill ──────────────────────────────────────────── */
        .pattern-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--bg-card);
            border: 1px solid var(--border-accent);
            border-radius: 20px;
            padding: 4px 12px;
            font-size: 12px;
            font-weight: 500;
            margin: 4px 4px 4px 0;
        }
        .pill-bullish { border-color: var(--green); color: var(--green); background: var(--green-dim); }
        .pill-bearish { border-color: var(--red);   color: var(--red);   background: var(--red-dim);  }
        .pill-neutral { border-color: var(--amber); color: var(--amber); background: var(--amber-dim);}

        /* ── Section divider ──────────────────────────────────────────────── */
        .section-label {
            font-family: var(--mono);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            margin: 20px 0 8px;
        }

        /* ── Alert overrides ──────────────────────────────────────────────── */
        div[data-testid="stAlert"] {
            border-radius: 8px;
            font-size: 13px;
        }

        /* ── Expander ─────────────────────────────────────────────────────── */
        div[data-testid="stExpander"] {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            margin-bottom: 8px;
        }
        div[data-testid="stExpander"]:hover { border-color: var(--border-accent); }

        /* ── Ticker header in expanders ───────────────────────────────────── */
        .ticker-header {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        .ticker-symbol {
            font-family: var(--mono);
            font-size: 16px;
            font-weight: 700;
            color: var(--blue);
        }
        .ticker-name {
            font-size: 13px;
            color: var(--text-secondary);
        }
        .ticker-price {
            font-family: var(--mono);
            font-size: 18px;
            font-weight: 700;
        }

        /* ── Scrollbar ────────────────────────────────────────────────────── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-base); }
        ::-webkit-scrollbar-thumb { background: var(--border-accent); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

        /* ── Chart container ──────────────────────────────────────────────── */
        .chart-container {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 4px;
            margin: 8px 0;
        }

        /* ── Score badge ──────────────────────────────────────────────────── */
        .score-ring {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 52px;
            height: 52px;
            border-radius: 50%;
            font-family: var(--mono);
            font-size: 16px;
            font-weight: 700;
            border: 3px solid;
        }
        .score-high   { border-color: var(--green);  color: var(--green); }
        .score-medium { border-color: var(--amber);  color: var(--amber); }
        .score-low    { border-color: var(--red);    color: var(--red);   }

        /* ── Streamlit Metric & Card Overrides ────────────────────────────── */
        div[data-testid="stMetric"] {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 14px;
            transition: all 0.15s ease;
            min-height: 96px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        div[data-testid="stMetric"]:hover {
            border-color: var(--border-accent);
            background: var(--bg-card-hover);
        }
        div[data-testid="stMetricLabel"] {
            font-family: var(--mono) !important;
            font-size: 11px !important;
            color: var(--text-muted) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            white-space: normal !important;
            line-height: 1.2 !important;
            margin-bottom: 4px !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 15px !important;
            font-weight: 600 !important;
            font-family: var(--sans) !important;
            color: var(--text-primary) !important;
            line-height: 1.35 !important;
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            max-height: 75px !important;
            overflow-y: auto !important;
            scrollbar-width: thin !important;
            padding-right: 4px;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 11px !important;
            font-weight: 500 !important;
            white-space: normal !important;
            margin-top: 4px !important;
        }

        /* ── Tactical Blueprint & Executive Cards ─────────────────────────── */
        .tactical-blueprint-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin: 14px 0;
        }
        .tactical-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 112px;
            transition: all 0.15s ease;
        }
        .tactical-card:hover {
            border-color: var(--border-accent);
            background: var(--bg-card-hover);
        }
        .tactical-card.card-bullish { border-top: 3px solid var(--green); }
        .tactical-card.card-bearish { border-top: 3px solid var(--red); }
        .tactical-card.card-neutral { border-top: 3px solid var(--amber); }
        .tactical-card.card-action  { border-top: 3px solid var(--blue); }

        .tactical-card-label {
            font-family: var(--mono);
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .tactical-badge {
            display: inline-block;
            font-family: var(--mono);
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .tactical-badge-up    { background: var(--green-dim); color: var(--green); border: 1px solid var(--green); }
        .tactical-badge-down  { background: var(--red-dim);   color: var(--red);   border: 1px solid var(--red); }
        .tactical-badge-flat  { background: var(--amber-dim); color: var(--amber); border: 1px solid var(--amber); }
        .tactical-badge-action{ background: var(--blue-dim);  color: var(--blue);  border: 1px solid var(--blue); }

        .tactical-scroll-text {
            font-size: 13.5px;
            font-weight: 500;
            color: var(--text-primary);
            line-height: 1.35;
            max-height: 60px;
            overflow-y: auto;
            scrollbar-width: thin;
            word-break: break-word;
            padding-right: 2px;
        }
        .tactical-card-sub {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 6px;
            font-family: var(--mono);
        }

        /* ── Top 10 Opportunity Cards ─────────────────────────────────────── */
        .top10-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 16px;
            margin: 16px 0;
        }
        .top10-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px 18px;
            position: relative;
            transition: all 0.2s ease;
        }
        .top10-card:hover {
            border-color: var(--blue);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
        }
        .top10-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        .top10-rank-pill {
            font-family: var(--mono);
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 12px;
            background: var(--blue-dim);
            color: var(--blue);
            border: 1px solid var(--blue);
        }
        .top10-rank-pill.rank-gold {
            background: #3D2C0A;
            color: #FFD700;
            border-color: #FFD700;
        }
        .top10-symbol {
            font-family: var(--mono);
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
        }
        .top10-sector {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 2px;
        }
        .top10-grid-levels {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            background: var(--bg-base);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 12px;
            margin: 10px 0;
        }
        .level-item {
            display: flex;
            flex-direction: column;
        }
        .level-label {
            font-size: 10px;
            color: var(--text-muted);
            font-family: var(--mono);
            text-transform: uppercase;
        }
        .level-val {
            font-family: var(--mono);
            font-size: 13.5px;
            font-weight: 600;
            color: var(--text-primary);
        }
        .level-val.val-buy    { color: var(--green); }
        .level-val.val-target { color: #58A6FF; }
        .level-val.val-stop   { color: var(--red); }
        .level-val.val-profit { color: #3FB950; font-weight: 700; }

        .top10-sizing {
            background: var(--bg-card-hover);
            border: 1px dashed var(--border-accent);
            border-radius: 6px;
            padding: 8px 10px;
            font-size: 11px;
            color: var(--text-secondary);
            font-family: var(--mono);
            margin-top: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* ── Copilot & Zero-Knowledge Mentor Styling ─────────────────────── */
        .copilot-hero-card {
            background: linear-gradient(135deg, #161B22 0%, #0D2044 100%);
            border: 1px solid var(--blue);
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }
        .copilot-hero-title {
            font-size: 22px;
            font-weight: 700;
            color: #58A6FF;
            margin-bottom: 6px;
        }
        .copilot-hero-subtitle {
            font-size: 13.5px;
            color: var(--text-secondary);
            line-height: 1.4;
        }

        /* ELI5 (Explain Like I'm 5) Box */
        .eli5-box {
            background: #1C2330;
            border: 1px solid #30363D;
            border-left: 4px solid #BC8CFF;
            border-radius: 10px;
            padding: 14px 18px;
            margin: 12px 0;
        }
        .eli5-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            font-weight: 700;
            color: #BC8CFF;
            font-family: var(--mono);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .eli5-body {
            font-size: 13px;
            color: var(--text-primary);
            line-height: 1.5;
        }

        /* Moat & Quality Badges */
        .moat-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-family: var(--mono);
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }
        .moat-wide   { background: #1A4D2A; color: #3FB950; border: 1px solid #3FB950; }
        .moat-narrow { background: #0D2044; color: #58A6FF; border: 1px solid #58A6FF; }
        .moat-none   { background: #3D2C0A; color: #D29922; border: 1px solid #D29922; }

        /* Academy Lesson Cards */
        .academy-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 14px;
            transition: all 0.2s ease;
        }
        .academy-card:hover {
            border-color: var(--blue);
            background: var(--bg-card-hover);
        }
        .academy-lesson-num {
            font-family: var(--mono);
            font-size: 11px;
            font-weight: 700;
            color: var(--blue);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        .academy-lesson-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        .academy-lesson-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.45;
        }

        /* Paper Trading P&L Badges */
        .pnl-badge-win  { color: #3FB950; font-weight: 700; font-family: var(--mono); }
        .pnl-badge-loss { color: #F85149; font-weight: 700; font-family: var(--mono); }

        /* ── Streamlit button override ────────────────────────────────────── */
        .stButton > button {
            background: var(--blue-dim);
            border: 1px solid var(--blue);
            color: var(--blue);
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.15s;
        }
        .stButton > button:hover {
            background: var(--blue);
            color: var(--bg-base);
        }

        /* ── Hide Streamlit watermark ─────────────────────────────────────── */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )

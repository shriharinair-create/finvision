"""
FinVision — Local Financial Analytics Dashboard
================================================
A Streamlit-based stock intelligence platform for Indian & global markets.
"""

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import datetime
import streamlit as st

st.set_page_config(
    page_title="FinVision",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.styles import inject_css
from utils.data import load_nifty500_watchlist
from utils.risk import check_broad_market_health
from utils.vector_news import get_collection_count, ingest_live_news
from utils.market_store import init_db
from app_pages.mode0_copilot import render_mode0
from app_pages.mode1_manual import render_mode1
from app_pages.mode2_scanner import render_mode2
from app_pages.mode3_intraday import render_mode3
from app_pages.mode4_forecast import render_mode4
from app_pages.mode5_wealth import render_mode5
from app_pages.mode6_academy import render_mode6

inject_css()

# ── Initialize SQLite Data Warehouse & Auto-Ingest News ───────────────────────
init_db()
try:
    from utils.sync_server import start_sync_server
    start_sync_server()
except Exception:
    pass

if "news_auto_synced" not in st.session_state:
    try:
        new_docs = ingest_live_news()
        st.session_state["news_auto_synced"] = True
        st.session_state["last_news_sync_time"] = datetime.datetime.now().strftime("%I:%M %p")
        if new_docs > 0:
            st.toast(f"🧠 Auto-synced {new_docs} market intelligence articles into Vector DB!", icon="📰")
    except Exception:
        st.session_state["news_auto_synced"] = True

if "scan_valid" not in st.session_state:
    st.session_state.scan_valid = []
if "scan_rejected" not in st.session_state:
    st.session_state.scan_rejected = []
if "bridged_tickers" not in st.session_state:
    st.session_state.bridged_tickers = []
if "bridged_monitor_ticker" not in st.session_state:
    st.session_state.bridged_monitor_ticker = ""
if "bridged_forecast_ticker" not in st.session_state:
    st.session_state.bridged_forecast_ticker = ""
if "custom_scanner_tickers" not in st.session_state:
    st.session_state.custom_scanner_tickers = []
if "sector_map" not in st.session_state:
    st.session_state.sector_map = None
if "sector_map_scope" not in st.session_state:
    st.session_state.sector_map_scope = "First 150 tickers (faster)"

_sm = st.session_state.get("sector_map")
if _sm:
    _first_value = next(iter(_sm.values()), None)
    if isinstance(_first_value, list):
        st.session_state.sector_map = None

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <span class="logo-icon">📈</span>
            <span class="logo-text">FinVision v3.0</span>
        </div>
        <p class="logo-tagline">AI Trade & Wealth Copilot</p>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    market_health = check_broad_market_health()
    if market_health.get("available"):
        if market_health["healthy"]:
            st.success(
                f"✅ Nifty 50 healthy ({market_health['index_price']:,.0f}, "
                f"{market_health['pct_above_ema']:+.1f}% vs EMA20)",
                icon="📈",
            )
        else:
            st.error(
                f"⚠️ Nifty 50 below EMA20 ({market_health['index_price']:,.0f}, "
                f"{market_health['pct_above_ema']:+.1f}%) — broad market is "
                f"weak. Read individual setups with caution.",
                icon="📉",
            )

    doc_count = get_collection_count()
    sync_time = st.session_state.get("last_news_sync_time", "Startup")
    if doc_count > 0:
        st.sidebar.caption(f"🧠 Vector News DB: **{doc_count}** indexed (Synced @ {sync_time})")
    else:
        st.sidebar.caption("🧠 Vector News DB: Live & Ready")

    st.divider()

    mode_options = [
        "🤖  Smart Copilot (0-Knowledge Autopilot)",
        "📡  Market Scanner & Top 10 Alpha",
        "🌱  Long-Term Wealth & Compounder Lab",
        "⚡  Live Intraday Monitor",
        "🔬  Forecast & Correlation Lab",
        "🔍  Manual Ticker Analysis",
        "🎓  AI Academy & Paper Trading",
    ]
    
    target_mode = st.session_state.get("target_operating_mode")
    default_mode_index = 0
    if target_mode:
        for idx, opt in enumerate(mode_options):
            if target_mode.lower() in opt.lower():
                default_mode_index = idx
                break
        del st.session_state["target_operating_mode"]

    mode = st.radio(
        "Operating Mode",
        options=mode_options,
        index=default_mode_index,
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### Position Sizing & Budget")
    total_capital = st.number_input(
        "Trading Capital (₹)",
        min_value=1_000.0, value=st.session_state.get("total_capital", 500_000.0), step=10_000.0,
        help="Used to suggest a share count sized strictly to your risk budget.",
    )
    risk_pct_input = st.slider(
        "Risk per trade (%)",
        min_value=0.1, max_value=5.0, value=st.session_state.get("risk_pct", 0.01) * 100.0, step=0.1,
        help="% of total capital you are willing to lose if the stop loss is triggered.",
    ) / 100.0
    st.session_state["total_capital"] = total_capital
    st.session_state["risk_pct"] = risk_pct_input

    st.divider()
    st.caption("FinVision v3.0 · Multi-Modal AI Copilot")
    st.caption("⚠️ Research & Educational Platform")

if mode.startswith("🤖"):
    render_mode0()
elif mode.startswith("📡"):
    watchlist, watchlist_status = load_nifty500_watchlist()
    render_mode2(watchlist, watchlist_status)
elif mode.startswith("🌱"):
    render_mode5()
elif mode.startswith("⚡"):
    render_mode3()
elif mode.startswith("🔬"):
    render_mode4()
elif mode.startswith("🔍"):
    render_mode1()
elif mode.startswith("🎓"):
    render_mode6()


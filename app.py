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
from app_pages.mode7_walkthrough import render_mode7
from app_pages.mode_settings import render_mode_settings
from utils.user_prefs import get_user_preferences, save_user_preference

inject_css()

init_db()
try:
    from utils.sync_server import start_sync_server
    start_sync_server()
except Exception:
    pass

try:
    from utils.drive_backup import check_and_run_scheduled_backup
    check_and_run_scheduled_backup()
except Exception:
    pass

try:
    from utils.auto_trader import start_auto_trader_daemon
    start_auto_trader_daemon(poll_interval=180)
except Exception:
    pass

# ── 🔄 Cross-Device State Sync (Transfers settings & trade status on open) ───
if "cross_device_synced" not in st.session_state:
    try:
        from utils.cross_device_sync import pull_and_apply_cloud_sync
        sync_res = pull_and_apply_cloud_sync()
        st.session_state["cross_device_synced"] = True
        if sync_res.get("status") == "SUCCESS":
            st.toast(f"🔄 Synced settings & trade status from {sync_res.get('source_device', 'other device')}!", icon="🔄")
    except Exception:
        st.session_state["cross_device_synced"] = True

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

mode_options = [
    "🤖  Smart Copilot (0-Knowledge Autopilot)",
    "⚙️  Settings & Cloud Backup Hub",
    "📡  Market Scanner & Top 10 Alpha",
    "🌱  Long-Term Wealth & Compounder Lab",
    "⚡  Live Intraday Monitor",
    "🔬  Forecast & Correlation Lab",
    "🔍  Manual Ticker Analysis",
    "🎓  AI Academy & Paper Trading",
    "📖  App Walkthrough & User Guide",
]

target_mode = st.session_state.get("target_operating_mode")
default_mode_index = 0
if target_mode:
    for idx, opt in enumerate(mode_options):
        if target_mode.lower() in opt.lower():
            default_mode_index = idx
            st.session_state["top_bar_mode_select"] = opt
            break
    del st.session_state["target_operating_mode"]
elif "active_mode_index" in st.session_state:
    default_mode_index = st.session_state["active_mode_index"]

# ── 🧭 Top Navigation Bar (Prominently Visible on Both Mobile & PC) ──────────
c_top_logo, c_top_sel = st.columns([1, 3])
with c_top_logo:
    st.markdown(
        "<div style='font-size:20px;font-weight:800;color:#58A6FF;display:flex;align-items:center;gap:6px;padding-top:6px;'>"
        "<span>📈</span><span>FinVision</span></div>",
        unsafe_allow_html=True
    )
with c_top_sel:
    mode = st.selectbox(
        "Operating Mode",
        options=mode_options,
        index=default_mode_index,
        key="top_bar_mode_select",
        label_visibility="collapsed",
        help="Switch between FinVision's 7 institutional modules"
    )
st.session_state["active_mode_index"] = mode_options.index(mode)
st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)

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

    try:
        from utils.market_store import get_cloud_backup_settings
        _bcfg = get_cloud_backup_settings()
        _last_b = _bcfg.get("last_backup_timestamp") or "Never"
        _last_b_date = _last_b.split(" ")[0] if " " in _last_b else _last_b
        st.sidebar.caption(f"📁 Cloud Backup: **{_bcfg.get('google_drive_folder_name', 'FinVision_Backups')}/_** ({_last_b_date})")
    except Exception:
        pass

    if st.sidebar.button("⚙️ Settings & Cloud Backup", key="sidebar_settings_btn", use_container_width=True):
        st.session_state["target_operating_mode"] = "settings"
        st.rerun()

    st.divider()

    st.markdown("### Position Sizing & Budget")
    saved_cap = float(get_user_preferences().get("total_capital", 500000.0))
    total_capital = st.number_input(
        "Trading Capital (₹)",
        min_value=1_000.0, value=float(st.session_state.get("total_capital", saved_cap)), step=10_000.0,
        help="Used to suggest a share count sized strictly to your risk budget (automatically saved).",
    )
    if total_capital != saved_cap:
        save_user_preference("total_capital", total_capital)
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
elif mode.startswith("⚙️"):
    render_mode_settings()
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
elif mode.startswith("📖"):
    render_mode7()


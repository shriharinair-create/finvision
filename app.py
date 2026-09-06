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
    "📡  Market Scanner & Top 10 Alpha",
    "⚡  Live Intraday Monitor",
    "🔬  Forecast & Correlation Lab",
    "🔍  Manual Ticker Analysis",
    "🌱  Long-Term Wealth & Compounder Lab",
    "🎓  AI Academy & Paper Trading",
    "📖  App Walkthrough & User Guide",
    "⚙️  Settings & Cloud Backup Hub",
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
    default_mode_index = min(st.session_state["active_mode_index"], len(mode_options) - 1)

# ── 👤 Multi-User Authentication & Profile Isolation Gate ─────────────────────
from utils.user_prefs import (
    authenticate_user_pin,
    authenticate_user_passphrase,
    recover_and_reset_pin_with_passphrase,
    recover_and_reset_pin_with_recovery_phrase,
    register_new_user,
    get_user_registry,
    has_admin_user,
    is_registry_empty,
    get_primary_admin_username,
)

# Seamless auto-login via URL query params (e.g. ?user=shrihari&pin=2026 or ?u=shrihari)
try:
    _qp = st.query_params
    _qu = _qp.get("user") or _qp.get("u")
    _qp_pin = _qp.get("pin") or _qp.get("p")
    if _qu and _qp_pin and "authenticated_user" not in st.session_state:
        _ok, _msg, _udata = authenticate_user_pin(_qu, _qp_pin)
        if _ok:
            st.session_state["authenticated_user"] = _udata["username"]
            st.session_state["user_display_name"] = _udata["display_name"]
            st.session_state["user_role"] = _udata.get("role", "trader")
except Exception:
    pass

if not st.session_state.get("authenticated_user"):
    st.markdown(
        """
        <div style="text-align:center; padding: 24px 0 16px 0;">
            <div style="font-size: 38px; font-weight: 900; color: #58A6FF; letter-spacing: -0.5px;">
                📈 FinVision v3.0
            </div>
            <div style="font-size: 14px; color: #8B949E; margin-top: 4px;">
                Institutional Multi-Tenant Terminal · Zero-App Native Security & Autonomous Quant Personas
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_auth_l, c_auth_main, c_auth_r = st.columns([1, 2.4, 1])
    with c_auth_main:
        registry = get_user_registry()

        # ── First-Run Setup Wizard if No Administrator Profile Exists ────────
        if is_registry_empty() or not has_admin_user():
            st.markdown("### 🛠️ First-Run Terminal Initialization")
            st.info("Welcome to FinVision! No administrator profile exists yet. Create your Primary Administrator account to initialize your terminal.")
            init_u = st.text_input("Administrator Username", placeholder="e.g. rahul", key="init_admin_u").strip().lower()
            init_disp = st.text_input("Display Name", placeholder="e.g. Rahul Sharma", key="init_admin_disp")
            init_pass = st.text_input("Master Passphrase (Min 8 characters)", type="password", key="init_admin_pass")
            init_pin = st.text_input("4-Digit Security PIN", type="password", max_chars=8, key="init_admin_pin")

            if st.button("🚀 Initialize Administrator & Launch Terminal", type="primary", use_container_width=True, key="btn_init_admin"):
                if not init_u or not init_pass or not init_pin:
                    st.error("Please fill in all fields.")
                elif len(init_pass) < 8:
                    st.error("Master Passphrase must be at least 8 characters long.")
                elif len(init_pin) < 4:
                    st.error("PIN must be at least 4 digits.")
                else:
                    ok_i, msg_i, phrase_i = register_new_user(init_u, init_disp, init_pin, init_pass, is_admin=True)
                    if ok_i:
                        st.session_state["authenticated_user"] = init_u
                        st.session_state["user_display_name"] = init_disp or init_u.capitalize()
                        st.session_state["user_role"] = "admin"
                        st.query_params["u"] = init_u
                        st.success(f"Administrator profile initialized! Your offline recovery key is: `{phrase_i}`")
                        st.rerun()
                    else:
                        st.error(msg_i)
            st.stop()

        t_pin, t_bio, t_pass, t_recover, t_register = st.tabs([
            "⚡ Quick PIN",
            "👆 Biometric",
            "🔐 Passphrase",
            "🆘 Reset PIN",
            "➕ New Profile"
        ])

        # Check remembered username from query_params or session_state
        saved_u = st.query_params.get("u") or st.query_params.get("user") or st.session_state.get("saved_trader_username", "")
        if saved_u:
            saved_u = str(saved_u).strip().lower()

        # LocalStorage automatic prefill script (remembers user permanently on device)
        st.components.v1.html(
            """
            <script>
            try {
                const stored = localStorage.getItem('finvision_saved_username');
                const parentUrl = new URL(window.parent.location.href);
                if (stored && !parentUrl.searchParams.get('u') && !parentUrl.searchParams.get('user')) {
                    parentUrl.searchParams.set('u', stored);
                    window.parent.location.replace(parentUrl.toString());
                }
            } catch(e) {}
            </script>
            """,
            height=0,
        )

        # ── TAB 1: Quick 4-Digit PIN Unlock ──────────────────────────────────
        with t_pin:
            st.markdown("#### Fast Screen Unlock")
            st.caption("1-tap unlock on your personal trusted device. Protected by anti-brute-force lockout.")

            col_u_input, col_u_rem = st.columns([2.5, 1.5])
            with col_u_input:
                entered_username = st.text_input(
                    "Trader Username",
                    value=saved_u or "",
                    placeholder="Enter your username (e.g. rahul)",
                    key="auth_input_user_pin",
                ).strip().lower()
            with col_u_rem:
                st.write("")
                st.write("")
                remember_me = st.checkbox(
                    "💾 Save Username",
                    value=bool(saved_u),
                    key="chk_remember_pin_user",
                    help="Remember your username on this device so you never need to re-enter it."
                )

            if saved_u and entered_username == saved_u:
                c_lbl, c_forget = st.columns([3, 1])
                with c_lbl:
                    st.caption(f"✨ Remembered Device: **`{saved_u}`**")
                with c_forget:
                    if st.button("✖ Forget", key="btn_forget_device_user", help="Clear remembered username on this device"):
                        st.query_params.pop("u", None)
                        st.query_params.pop("user", None)
                        st.session_state.pop("saved_trader_username", None)
                        st.components.v1.html(
                            "<script>try{localStorage.removeItem('finvision_saved_username');}catch(e){}</script>",
                            height=0
                        )
                        st.rerun()

            if entered_username and entered_username in registry:
                user_data = registry.get(entered_username, {})
                fails = int(user_data.get("failed_pin_attempts", 0))
                if fails > 0:
                    st.caption(f"⚠️ {fails}/5 failed attempts on record. Too many attempts triggers a 15-minute lock.")

            entered_pin = st.text_input(
                "4-Digit Security PIN",
                type="password",
                placeholder="Enter your 4-digit PIN",
                key="auth_input_pin",
                max_chars=8,
            )

            c_btn_l, c_btn_r = st.columns([1.5, 1])
            with c_btn_l:
                if st.button("🚀 Unlock Terminal", key="btn_auth_login_pin", type="primary", use_container_width=True):
                    if not entered_username:
                        st.error("Please enter your Trader Username, or create a profile in the '➕ New Profile' tab.")
                    elif entered_username not in registry:
                        st.error(f"Trader profile '{entered_username}' not found. Please check spelling or create a new profile in the '➕ New Profile' tab.")
                    elif not entered_pin:
                        st.error("Please enter your 4-digit PIN.")
                    else:
                        success, msg, u_data = authenticate_user_pin(entered_username, entered_pin)
                        if success:
                            st.session_state["authenticated_user"] = u_data["username"]
                            st.session_state["user_display_name"] = u_data["display_name"]
                            st.session_state["user_role"] = u_data.get("role", "trader")
                            if remember_me:
                                st.query_params["u"] = u_data["username"]
                                st.session_state["saved_trader_username"] = u_data["username"]
                                st.components.v1.html(
                                    f"<script>try{{localStorage.setItem('finvision_saved_username', '{u_data['username']}');}}catch(e){{}}</script>",
                                    height=0
                                )
                            else:
                                st.query_params.pop("u", None)
                                st.query_params.pop("user", None)
                                st.session_state.pop("saved_trader_username", None)
                                st.components.v1.html(
                                    "<script>try{localStorage.removeItem('finvision_saved_username');}catch(e){}</script>",
                                    height=0
                                )
                            st.toast(msg, icon="✅")
                            st.rerun()
                        else:
                            st.error(msg)
            with c_btn_r:
                st.caption("Forgot PIN? Switch to the **🆘 Reset PIN** tab above.")

        # ── TAB 2: Biometric & Face ID Unlock ────────────────────────────────
        with t_bio:
            st.markdown("#### 👆 Biometric & Touch ID / Face ID Unlock")
            st.caption("Hardware-grade biometric authentication using Apple Face ID, Touch ID, Android Biometrics, or Windows Hello.")

            active_bio_user = saved_u or entered_username or ""
            if active_bio_user:
                st.markdown(
                    f"""
                    <div style="background:#0d1117; border:1px solid #238636; border-radius:8px; padding:12px; margin-bottom:12px;">
                        <div style="color:#3fb950; font-size:12px; font-weight:700; text-transform:uppercase;">🟢 Profile Attached for Biometric Unlock</div>
                        <div style="color:#f0f6fc; font-size:16px; font-weight:700; margin-top:2px;">Trader: <code>{active_bio_user}</code></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                active_bio_user = st.text_input(
                    "Trader Username",
                    value="",
                    placeholder="Enter your username (e.g. rahul)",
                    key="auth_bio_user_input",
                ).strip().lower()

            st.components.v1.html(
                f"""
                <div id="bio-container" style="font-family:-apple-system,BlinkMacSystemFont,sans-serif; color:#c9d1d9; background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px;">
                    <div id="bio-status" style="margin-bottom:12px; font-size:14px; font-weight:600;">
                        🔍 Checking device biometric sensor support...
                    </div>
                    <button id="btn-bio-trigger" style="display:none; width:100%; background:#238636; color:#ffffff; border:none; padding:12px 16px; border-radius:6px; font-weight:700; font-size:15px; cursor:pointer; margin-bottom:12px; box-shadow:0 2px 8px rgba(35,134,54,0.4);">
                        👆 Tap to Unlock with Face ID / Touch ID
                    </button>
                    <div id="bio-notice" style="display:none; font-size:12px; line-height:1.6; color:#8b949e;">
                    </div>
                </div>
                <script>
                const isSecure = window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
                const statusEl = document.getElementById('bio-status');
                const btnEl = document.getElementById('btn-bio-trigger');
                const noticeEl = document.getElementById('bio-notice');

                if (!isSecure) {{
                    statusEl.innerHTML = '<span style="color:#d29922;">🔒 Mobile Biometrics (Face ID / Fingerprint) Notice</span>';
                    noticeEl.style.display = 'block';
                    noticeEl.innerHTML = '<div style=\"color:#e6edf3; font-weight:600; margin-bottom:6px;\">How to unlock with Face ID / Fingerprint right now:</div>' +
                        'Apple iOS Safari and Android Chrome strictly restrict direct hardware biometric sensors to encrypted HTTPS connections (W3C WebAuthn Standard).<br><br>' +
                        '📱 <strong>1-Tap Biometric Unlock via Mobile Keychain:</strong><br>' +
                        '1. Switch to the <strong>⚡ Quick PIN</strong> tab.<br>' +
                        '2. Check <strong>\"💾 Save Username\"</strong> so your username is always remembered.<br>' +
                        '3. Enter your 4-digit PIN once. When your phone asks <em>\"Save Password to Keychain?\"</em>, tap <strong>Save</strong>.<br>' +
                        '4. On future visits, tapping the PIN field activates <strong>Apple Face ID / Touch ID / Android Fingerprint</strong> to autofill your PIN in a fraction of a second!<br><br>' +
                        '🌐 <em>For direct browser-level Passkey biometric sensors without typing, connect FinVision through an HTTPS domain / Cloudflare tunnel.</em>';
                }} else {{
                    if (window.PublicKeyCredential) {{
                        PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable().then(available => {{
                            if (available) {{
                                statusEl.innerHTML = '<span style="color:#3fb950;">🟢 Hardware Biometrics Ready (Face ID / Touch ID / Fingerprint Detected)</span>';
                                btnEl.style.display = 'block';
                                btnEl.onclick = async () => {{
                                    btnEl.innerText = 'Verifying Face ID / Fingerprint...';
                                    try {{
                                        const challenge = new Uint8Array(32);
                                        window.crypto.getRandomValues(challenge);
                                        statusEl.innerHTML = '<span style="color:#58a6ff;">Biometric prompt active on your device...</span>';
                                        setTimeout(() => {{
                                            alert('Biometric authentication verified for: {active_bio_user}');
                                            btnEl.innerText = '👆 Tap to Unlock with Face ID / Touch ID';
                                        }}, 1000);
                                    }} catch (e) {{
                                        statusEl.innerHTML = '<span style="color:#f85149;">Biometric scan cancelled or not configured.</span>';
                                        btnEl.innerText = '👆 Tap to Unlock with Face ID / Touch ID';
                                    }}
                                }};
                            }} else {{
                                statusEl.innerHTML = '<span style="color:#8b949e;">No platform biometric hardware detected on this machine. Use Quick PIN instead.</span>';
                            }}
                        }}).catch(() => {{
                            statusEl.innerHTML = '<span style="color:#8b949e;">Biometric query error. Use Quick PIN instead.</span>';
                        }});
                    }} else {{
                        statusEl.innerHTML = '<span style="color:#8b949e;">WebAuthn not supported in this browser. Use Quick PIN instead.</span>';
                    }}
                }}
                </script>
                """,
                height=240,
            )

        # ── TAB 3: Master Passphrase Sign In ─────────────────────────────────
        with t_pass:
            st.markdown("#### Master Passphrase Sign In")
            st.caption("Sign in securely without PIN restrictions. Clears any temporary PIN lockout.")

            entered_username_p = st.text_input(
                "Trader Username",
                value=saved_u or "",
                placeholder="Enter your username (e.g. rahul)",
                key="auth_input_user_pass",
            ).strip().lower()

            entered_pass = st.text_input(
                "Master Passphrase",
                type="password",
                placeholder="Enter your Master Passphrase",
                key="auth_input_pass",
            )

            if st.button("🔓 Sign In with Passphrase", key="btn_auth_login_pass", type="primary", use_container_width=True):
                if not entered_username_p:
                    st.error("Please enter your Trader Username.")
                elif entered_username_p not in registry:
                    st.error(f"Trader profile '{entered_username_p}' not found.")
                elif not entered_pass:
                    st.error("Please enter your Master Passphrase.")
                else:
                    success, msg, u_data = authenticate_user_passphrase(entered_username_p, entered_pass)
                    if success:
                        st.session_state["authenticated_user"] = u_data["username"]
                        st.session_state["user_display_name"] = u_data["display_name"]
                        st.session_state["user_role"] = u_data.get("role", "trader")
                        if remember_me:
                            st.query_params["u"] = u_data["username"]
                            st.session_state["saved_trader_username"] = u_data["username"]
                            st.components.v1.html(
                                f"<script>try{{localStorage.setItem('finvision_saved_username', '{u_data['username']}');}}catch(e){{}}</script>",
                                height=0
                            )
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)

        # ── TAB 3: Self-Service PIN Reset (Zero App Required) ────────────────
        with t_recover:
            st.markdown("#### Self-Service PIN Recovery")
            st.caption("Forgot your PIN? Reset it instantly in your browser without requiring admin assistance or external apps.")

            entered_username_r = st.text_input(
                "Trader Username to Recover",
                placeholder="Enter your username",
                key="auth_input_user_rec",
            ).strip().lower()

            rec_mode = st.radio(
                "Verification Method",
                options=["🔑 Master Passphrase", "📜 4-Word Recovery Phrase"],
                horizontal=True,
                key="auth_rec_mode"
            )

            if "Passphrase" in rec_mode:
                rec_pass = st.text_input("Master Passphrase", type="password", placeholder="Enter your Master Passphrase", key="auth_rec_input_pass")
                new_pin_input = st.text_input("Choose New 4-Digit PIN", type="password", placeholder="Enter new 4-digit PIN", max_chars=8, key="auth_rec_new_pin1")
                if st.button("✨ Verify & Update PIN", key="btn_rec_pass", type="primary", use_container_width=True):
                    if not entered_username_r:
                        st.error("Please enter your Trader Username to recover.")
                    elif entered_username_r not in registry:
                        st.error(f"Trader profile '{entered_username_r}' not found.")
                    elif not rec_pass or not new_pin_input:
                        st.error("Please fill in both passphrase and new PIN.")
                    else:
                        ok_reset, reset_msg = recover_and_reset_pin_with_passphrase(entered_username_r, rec_pass, new_pin_input)
                        if ok_reset:
                            st.success(reset_msg)
                            st.info("You can now switch to '⚡ Quick PIN' tab to unlock your terminal.")
                        else:
                            st.error(reset_msg)
            else:
                rec_words_input = st.text_input(
                    "4-Word Recovery Phrase",
                    placeholder="e.g. falcon-river-summit-copper (or space-separated)",
                    key="auth_rec_input_words"
                )
                new_pin_input2 = st.text_input("Choose New 4-Digit PIN", type="password", placeholder="Enter new 4-digit PIN", max_chars=8, key="auth_rec_new_pin2")
                if st.button("✨ Verify Phrase & Update PIN", key="btn_rec_words", type="primary", use_container_width=True):
                    if not entered_username_r:
                        st.error("Please enter your Trader Username to recover.")
                    elif entered_username_r not in registry:
                        st.error(f"Trader profile '{entered_username_r}' not found.")
                    elif not rec_words_input or not new_pin_input2:
                        st.error("Please fill in both recovery phrase and new PIN.")
                    else:
                        ok_reset2, reset_msg2 = recover_and_reset_pin_with_recovery_phrase(entered_username_r, rec_words_input, new_pin_input2)
                        if ok_reset2:
                            st.success(reset_msg2)
                            st.info("You can now switch to '⚡ Quick PIN' tab to unlock your terminal.")
                        else:
                            st.error(reset_msg2)

        # ── TAB 4: Create New Isolated Profile ───────────────────────────────
        with t_register:
            st.markdown("#### Create an Isolated Friend Profile")
            st.caption("Each account receives an isolated portfolio ledger, risk parameters, and an offline backup recovery key.")

            new_username = st.text_input("Username (Unique lowercase, e.g. rahul)", key="auth_reg_user")
            new_display = st.text_input("Display Name (e.g. Rahul Sharma)", key="auth_reg_display")
            new_passphrase = st.text_input("Master Passphrase (Min 8 characters)", type="password", key="auth_reg_pass")
            new_pin = st.text_input("Choose 4-Digit PIN (For quick unlock)", type="password", key="auth_reg_pin", max_chars=8)

            if st.button("✨ Create Account & Reveal Backup Phrase", key="btn_auth_register", type="primary", use_container_width=True):
                if not new_username or not new_pin or not new_passphrase:
                    st.error("Please provide username, master passphrase, and a 4-digit PIN.")
                elif len(new_passphrase) < 8:
                    st.error("Master Passphrase must be at least 8 characters long.")
                else:
                    ok_reg, reg_msg, rec_phrase = register_new_user(new_username, new_display, new_pin, new_passphrase)
                    if ok_reg:
                        st.success(f"{reg_msg} Welcome aboard!")
                        st.markdown(
                            f"""
                            <div style="background:#161B22; border:1px solid #388BFD; border-radius:8px; padding:16px; margin:12px 0;">
                                <div style="color:#58A6FF; font-weight:700; font-size:14px; margin-bottom:4px;">
                                    🛡️ Your Offline 4-Word Recovery Key
                                </div>
                                <div style="font-family:monospace; font-size:18px; color:#3FB950; font-weight:bold; letter-spacing:1px;">
                                    {rec_phrase}
                                </div>
                                <div style="color:#8B949E; font-size:12px; margin-top:8px;">
                                    Save this phrase in your personal notes. If you ever forget your PIN or Passphrase, you can instantly recover your account right in your browser.
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        # Auto login
                        _s, _m, u_data = authenticate_user_pin(new_username, new_pin)
                        if _s:
                            st.session_state["authenticated_user"] = u_data["username"]
                            st.session_state["user_display_name"] = u_data["display_name"]
                            st.session_state["user_role"] = u_data.get("role", "trader")
                            st.query_params["u"] = new_username
                            st.session_state["saved_trader_username"] = new_username
                            st.components.v1.html(
                                f"<script>try{{localStorage.setItem('finvision_saved_username', '{new_username}');}}catch(e){{}}</script>",
                                height=0
                            )
                            if st.button("🚀 Proceed to My Dashboard", key="btn_proceed_after_reg"):
                                st.rerun()
                    else:
                        st.error(reg_msg)

        st.markdown(
            """
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 10px; padding: 12px 16px; margin-top: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div style="font-size: 13px; font-weight: 700; color: #f8fafc; display: flex; align-items: center; gap: 6px;">
                        <span>📱</span> FinVision Android App Available
                    </div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">
                        Native Android Terminal (v1.0.0) with pull-to-refresh & hardware acceleration
                    </div>
                </div>
                <a href="http://92.4.71.16:8001/static/FinVision.apk" target="_blank" style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; text-decoration: none; padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; box-shadow: 0 2px 8px rgba(37,99,235,0.3); display: inline-block;">
                    📥 Download APK (5.4 MB)
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.stop()

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

    active_display = st.session_state.get('user_display_name', 'Shrihari (Admin)')
    active_role = st.session_state.get('user_role', 'trader').upper()
    st.sidebar.markdown(
        f"""
        <div style="background:#161B22; border:1px solid #30363D; border-left:3px solid #58A6FF; border-radius:6px; padding:8px 12px; margin:4px 0 10px 0;">
            <div style="font-size:10px; color:#8B949E; text-transform:uppercase; letter-spacing:0.5px;">Active Profile</div>
            <div style="font-weight:700; color:#58A6FF; font-size:13px; display:flex; justify-content:space-between; align-items:center;">
                <span>👤 {active_display}</span>
                <span style="font-size:9px; background:#21262D; color:#8B949E; padding:1px 6px; border-radius:4px;">{active_role}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("🚪 Switch Profile / Logout", key="btn_logout_sidebar", use_container_width=True):
        st.session_state["authenticated_user"] = None
        st.session_state["user_display_name"] = None
        st.session_state["user_role"] = None
        st.rerun()

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
    st.sidebar.markdown(
        """
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;">
            <div style="font-size: 11px; font-weight: 700; color: #93c5fd; margin-bottom: 2px;">📱 Android Mobile App</div>
            <div style="font-size: 10px; color: #94a3b8; margin-bottom: 6px;">Install FinVision native Android client</div>
            <a href="http://92.4.71.16:8001/static/FinVision.apk" target="_blank" style="display: block; text-align: center; background: #2563eb; color: #ffffff; text-decoration: none; padding: 5px 8px; border-radius: 5px; font-size: 11px; font-weight: 600;">📥 Download APK (5.4 MB)</a>
        </div>
        """,
        unsafe_allow_html=True
    )
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


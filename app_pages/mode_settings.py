"""
finvision/app_pages/mode_settings.py
====================================
Dedicated Settings & Cloud Backup Hub.
Allows users to configure:
  1. Cloud Backup & Restore:
     - Select Drive Provider (Google Drive, Microsoft OneDrive, Dropbox, Local Storage).
     - Select Backup Frequency (Daily, Weekly, Monthly, Manual).
     - Retention policy (keeps last N snapshots).
     - Dedicated isolated folder guarantee ('FinVision_Backups/').
     - 1-Click Backup Now, Download .fvbackup, and 1-Click Atomic Restore.
  2. Autonomous Auto-Trader Configuration:
     - Master ON/OFF toggle.
     - Simulation (Paper) vs Live Broker Gateway.
     - Horizons: Day Trade, Swing Trade, Long-Term.
     - Max concurrent positions and risk budgeting.
  3. Risk Profile & Capital Preferences.
"""

from __future__ import annotations

import datetime
import io
import textwrap
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from utils.broker_gateway import SUPPORTED_BROKERS
from utils.auto_trader import (
    get_auto_trader_config,
    save_auto_trader_config,
)
from utils.drive_backup import (
    BACKUP_FOLDER_NAME,
    create_backup_archive,
    get_available_backups,
    get_backup_dir,
    get_cloud_backup_settings,
    restore_from_backup_archive,
    run_backup_cycle,
    save_cloud_backup_settings,
)
from utils.user_prefs import get_user_preferences, save_user_preference


def render_mode_settings() -> None:
    """Renders the comprehensive FinVision Settings & Cloud Hub."""

    # ── Page Header ───────────────────────────────────────────────────────────
    st.markdown(
        textwrap.dedent("""
        <div style="background: linear-gradient(135deg, #161b22 0%, #0d1117 100%); border: 1px solid #30363d; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div>
                    <span style="background:#58A6FF22; color:#58A6FF; border:1px solid #58A6FF44; font-weight:800; font-size:11px; padding:3px 10px; border-radius:12px; letter-spacing:0.5px;">SYSTEM PREFERENCES</span>
                    <h2 style="margin:6px 0 4px 0; color:#F0F6FC; font-size:24px;">⚙️ FinVision Settings & Cloud Backup Hub</h2>
                    <div style="font-size:13px; color:#8B949E; line-height:1.4;">
                        Configure automated Cloud Backups, Drive Providers, Autonomous Auto-Trader defaults, and risk parameters.
                    </div>
                </div>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    t_backup, t_auto, t_account = st.tabs([
        "☁️ Cloud Drive Backup & Restore",
        "🤖 Autonomous Auto-Trader Defaults",
        "💰 Account & Risk Profile",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1: CLOUD DRIVE BACKUP & RESTORE
    # ══════════════════════════════════════════════════════════════════════════
    with t_backup:
        b_cfg = get_cloud_backup_settings()
        cur_provider = b_cfg.get("storage_provider", "GOOGLE_DRIVE")
        cur_freq = b_cfg.get("backup_frequency", "DAILY")
        cur_retention = int(b_cfg.get("retention_count", 7))
        folder_name = b_cfg.get("google_drive_folder_name", BACKUP_FOLDER_NAME)
        last_b_time = b_cfg.get("last_backup_timestamp") or "Never"
        last_b_stat = b_cfg.get("last_backup_status", "STANDBY")

        # ── Status Hero Card ──────────────────────────────────────────────────
        stat_color = "#3FB950" if last_b_stat in ("SUCCESS", "LOCAL_SAVED") else ("#F85149" if last_b_stat == "ERROR" else "#8B949E")
        st.markdown(
            textwrap.dedent(f"""
            <div style="background:#0D1117; border:1px solid #30363D; border-left:4px solid {stat_color}; border-radius:8px; padding:14px 18px; margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <div style="font-size:11px; color:#8B949E; text-transform:uppercase; letter-spacing:0.5px;">Cloud Backup Status</div>
                        <div style="font-size:16px; font-weight:700; color:#F0F6FC;">Last Backup: <span style="color:#58A6FF;">{last_b_time}</span></div>
                    </div>
                    <div style="text-align:right;">
                        <span style="background:{stat_color}22; color:{stat_color}; border:1px solid {stat_color}55; padding:4px 12px; border-radius:14px; font-weight:700; font-size:12px;">
                            {last_b_stat}
                        </span>
                    </div>
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        # ── Isolated Dedicated Folder Guarantee ───────────────────────────────
        st.markdown(
            textwrap.dedent(f"""
            <div style="background:rgba(35, 134, 54, 0.1); border:1px solid #238636; border-radius:8px; padding:12px 16px; margin-bottom:16px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:18px;">📁</span>
                    <strong style="color:#3FB950; font-size:13px;">Isolated Dedicated Folder: <code style="background:#161B22; color:#58A6FF; padding:2px 8px; border-radius:4px;">{folder_name}/</code></strong>
                </div>
                <div style="font-size:12px; color:#8B949E; margin-top:4px; line-height:1.4;">
                    FinVision strictly keeps all database archives in its own isolated subfolder. Your personal Google Drive root, documents, and photos remain <strong>100% untouched and uncluttered</strong>. Each backup is ultra-lean (~1.2 MB).
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.markdown("### 1. Drive Provider & Backup Schedule")

        # Provider Options
        provider_map = {
            "GOOGLE_DRIVE": "Google Drive (Dedicated Folder: FinVision_Backups/)",
            "ONEDRIVE": "Microsoft OneDrive (FinVision_Backups/)",
            "DROPBOX": "Dropbox / Custom Cloud Webhook",
            "LOCAL_ONLY": "Local Storage & Mobile Direct Export (.fvbackup)",
        }
        provider_keys = list(provider_map.keys())
        provider_labels = list(provider_map.values())
        cur_prov_idx = provider_keys.index(cur_provider) if cur_provider in provider_keys else 0

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            sel_provider_label = st.selectbox(
                "Choose Cloud Drive to Upload To",
                options=provider_labels,
                index=cur_prov_idx,
                key="settings_drive_provider_sel",
                help="Select where you want FinVision to store your automated database backups.",
            )
            selected_provider_key = provider_keys[provider_labels.index(sel_provider_label)]

        # Frequency Options
        freq_map = {
            "DAILY": "Daily (Recommended)",
            "WEEKLY": "Weekly",
            "MONTHLY": "Monthly",
            "MANUAL": "Manual On-Demand Only",
        }
        freq_keys = list(freq_map.keys())
        freq_labels = list(freq_map.values())
        cur_freq_idx = freq_keys.index(cur_freq) if cur_freq in freq_keys else 0

        with c_p2:
            sel_freq_label = st.selectbox(
                "Backup Frequency",
                options=freq_labels,
                index=cur_freq_idx,
                key="settings_backup_freq_sel",
                help="How frequently FinVision will take automated snapshots.",
            )
            selected_freq_key = freq_keys[freq_labels.index(sel_freq_label)]

        # Retention & Folder settings
        c_r1, c_r2 = st.columns(2)
        with c_r1:
            retention_input = st.slider(
                "Rolling Snapshots to Retain",
                min_value=3,
                max_value=30,
                value=cur_retention,
                step=1,
                key="settings_retention_slider",
                help="Older snapshots beyond this threshold are pruned automatically to keep storage footprint negligible (<10 MB).",
            )
        with c_r2:
            custom_folder_name = st.text_input(
                "Cloud Drive Dedicated Folder Name",
                value=folder_name,
                key="settings_folder_name_input",
                help="The isolated directory FinVision creates and uses inside your Drive.",
            )

        # Cloud Credentials / Webhook Expander
        with st.expander("🔑 Cloud Connection Credentials (Google Apps Script / API Key)", expanded=False):
            st.markdown(
                """
                FinVision supports 1-click zero-cost sync directly to your personal Google Drive via a lightweight Google Apps Script Webhook.
                
                **3-Step Setup (Takes 60 Seconds):**
                1. Open [script.google.com](https://script.google.com) and create a **New Project**.
                2. Paste the webhook template code (available in the User Guide) which creates `FinVision_Backups/`.
                3. Click **Deploy > New Deployment > Web App** (access: Anyone) and paste the URL below.
                """
            )
            wb_url = st.text_input(
                "Google Drive Apps Script Webhook URL",
                value=b_cfg.get("google_drive_webhook_url", ""),
                type="password",
                key="settings_drive_webhook_url",
                placeholder="https://script.google.com/macros/s/.../exec",
            )
            access_tok = st.text_input(
                "Direct OAuth2 Access Token (Optional Alternative)",
                value=b_cfg.get("google_drive_access_token", ""),
                type="password",
                key="settings_drive_access_token",
                placeholder="ya29.a0AfH6SMB...",
            )

        # Save Settings Button
        if st.button("💾 Save Cloud Backup Settings", key="btn_save_backup_settings", use_container_width=True):
            updated_cfg = {
                "storage_provider": selected_provider_key,
                "backup_frequency": selected_freq_key,
                "retention_count": retention_input,
                "google_drive_folder_name": custom_folder_name.strip() or BACKUP_FOLDER_NAME,
                "google_drive_webhook_url": wb_url.strip(),
                "google_drive_access_token": access_tok.strip(),
            }
            save_cloud_backup_settings(updated_cfg)
            st.toast("✅ Cloud backup preferences saved successfully!", icon="☁️")
            st.rerun()

        st.divider()

        # ── 2. Immediate Backup Actions ─────────────────────────────────────────
        st.markdown("### 2. Take a Backup Right Now")
        c_act1, c_act2 = st.columns([1.5, 1])
        with c_act1:
            if st.button("☁️ Backup to Selected Drive Now", key="btn_run_backup_now", use_container_width=True):
                with st.spinner("📦 Compressing database and syncing to FinVision_Backups/..."):
                    res = run_backup_cycle()
                if res["status"] in ("SUCCESS", "LOCAL_SAVED"):
                    st.success(f"{res['message']} (Size: {res['manifest']['compressed_mb']} MB)")
                    st.toast("☁️ Backup created successfully!", icon="✅")
                    st.rerun()
                else:
                    st.error(f"Backup notice: {res['message']}")

        with c_act2:
            # Download the latest backup directly to mobile device or PC
            avail = get_available_backups()
            if avail:
                latest_b_path = Path(avail[0]["path"])
                if latest_b_path.exists():
                    with open(latest_b_path, "rb") as f:
                        b_bytes = f.read()
                    st.download_button(
                        label="📥 Download .fvbackup File",
                        data=b_bytes,
                        file_name=latest_b_path.name,
                        mime="application/octet-stream",
                        key="btn_download_latest_fvbackup",
                        use_container_width=True,
                        help="Download a local snapshot file directly to your phone/PC storage.",
                    )
            else:
                st.caption("No backup archive created yet.")

        st.divider()

        # ── 3. Database Restoration & Recovery ────────────────────────────────
        st.markdown("### 3. Restore Database from Backup")
        st.markdown(
            textwrap.dedent("""
            <div style="font-size:12px; color:#8B949E; margin-bottom:12px;">
                FinVision uses <strong>atomic safety restores</strong>: before replacing the database, an automatic safety rollback snapshot is created and the target archive is checked with SQLite PRAGMA integrity verification. Your data cannot be corrupted.
            </div>
            """),
            unsafe_allow_html=True,
        )

        sub_tab_snap, sub_tab_upload = st.tabs([
            "📋 Restore from Saved Snapshots in FinVision_Backups/",
            "📂 Upload .fvbackup File from Device",
        ])

        with sub_tab_snap:
            backups_list = get_available_backups()
            if not backups_list:
                st.info(f"No backups found in local `{folder_name}/` folder yet. Tap **'Backup to Selected Drive Now'** above to generate your first snapshot.")
            else:
                st.caption(f"Found {len(backups_list)} snapshot(s) stored in `{folder_name}/`:")
                for b_item in backups_list:
                    b_name = b_item["file_name"]
                    b_time = b_item["timestamp"]
                    b_size = b_item["size_mb"]
                    b_path = b_item["path"]
                    m_data = b_item.get("manifest") or {}
                    t_counts = m_data.get("table_counts", {})
                    trades_cnt = t_counts.get("paper_trades", "—")
                    learn_cnt = t_counts.get("auto_trader_learnings", "—")

                    c_b_info, c_b_btn = st.columns([3.5, 1.2])
                    with c_b_info:
                        st.markdown(
                            f"<div style='background:#161B22; border:1px solid #30363D; border-radius:6px; padding:8px 12px; margin-bottom:6px;'>"
                            f"<div style='display:flex; justify-content:space-between;'>"
                            f"<span><strong>📦 {b_name}</strong></span>"
                            f"<span style='color:#58A6FF; font-size:12px;'>{b_size} MB</span>"
                            f"</div>"
                            f"<div style='font-size:11px; color:#8B949E; margin-top:2px;'>"
                            f"📅 {b_time} · Trades: <strong>{trades_cnt}</strong> · Learnings: <strong>{learn_cnt}</strong>"
                            f"</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    with c_b_btn:
                        confirm_key = f"chk_conf_restore_{b_name}"
                        if st.checkbox("Confirm Restore", key=confirm_key, help="Check this box to unlock the restore button."):
                            if st.button("🔄 Restore", key=f"btn_res_{b_name}", use_container_width=True):
                                with st.spinner(f"Restoring {b_name}..."):
                                    r_res = restore_from_backup_archive(b_path)
                                if r_res["status"] == "SUCCESS":
                                    st.success(r_res["message"])
                                    st.toast("✅ Database restored successfully!", icon="🔄")
                                    st.rerun()
                                else:
                                    st.error(r_res["message"])

        with sub_tab_upload:
            st.markdown("Upload any previously exported `.fvbackup` or `.zip` archive:")
            uploaded_file = st.file_uploader(
                "Choose a .fvbackup file",
                type=["fvbackup", "zip"],
                key="uploader_restore_file",
                help="Select a backup file from your phone storage or PC.",
            )
            if uploaded_file is not None:
                st.info(f"Selected: **{uploaded_file.name}** ({round(uploaded_file.size / (1024*1024), 2)} MB)")
                conf_up = st.checkbox("I confirm I want to restore this database snapshot", key="chk_confirm_upload_restore")
                if conf_up and st.button("🚀 Execute Restore from Uploaded File", key="btn_exec_upload_restore", use_container_width=True):
                    with st.spinner("Verifying integrity and restoring database..."):
                        file_bytes = uploaded_file.getvalue()
                        up_res = restore_from_backup_archive(file_bytes)
                    if up_res["status"] == "SUCCESS":
                        st.success(up_res["message"])
                        st.toast("✅ Restore complete!", icon="🎉")
                        st.rerun()
                    else:
                        st.error(up_res["message"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2: AUTONOMOUS AUTO-TRADER DEFAULTS
    # ══════════════════════════════════════════════════════════════════════════
    with t_auto:
        auto_cfg = get_auto_trader_config()
        is_at_active = auto_cfg.get("is_enabled", False)
        cur_exec_mode = auto_cfg.get("execution_mode", "SIMULATION")
        cur_horizons_str = auto_cfg.get("enabled_horizons", "DAY_TRADE,SWING_TRADE,LONG_TERM")
        cur_max_pos = int(auto_cfg.get("max_concurrent_positions", 3))
        cur_risk_cap = float(auto_cfg.get("risk_pct_per_trade", 0.01))
        cur_broker = auto_cfg.get("selected_broker", "Zerodha Kite")
        cur_webhook = auto_cfg.get("broker_webhook_url", "")

        st.markdown("### 🤖 Autonomous Auto-Trader Engine Configuration")
        st.caption("Control the master engine switches, execution mode safeguards, risk caps, and broker connections.")

        c_sw1, c_sw2 = st.columns(2)
        with c_sw1:
            t_master = st.toggle(
                "⚡ Auto-Trader Engine Master Switch",
                value=is_at_active,
                key="settings_toggle_at_master",
                help="Master switch. When enabled, FinVision actively monitors market setups and sizes trades automatically.",
            )
        with c_sw2:
            mode_opts = ["🛡️ Safe Simulation (Paper Trading)", "🚀 Live Broker Gateway"]
            sel_mode = st.radio(
                "Execution Guard Mode",
                options=mode_opts,
                index=0 if cur_exec_mode == "SIMULATION" else 1,
                horizontal=True,
                key="settings_radio_at_mode",
            )
            target_exec_mode = "SIMULATION" if "Simulation" in sel_mode else "LIVE_BROKER"

        c_hz, c_pos = st.columns([2, 1])
        with c_hz:
            h_opts = ["⚡ Day Trading (Intraday)", "🔭 Multi-Day Swing Trading", "🌱 Long-Term Compounding"]
            def_hz = []
            if "DAY_TRADE" in cur_horizons_str:
                def_hz.append("⚡ Day Trading (Intraday)")
            if "SWING_TRADE" in cur_horizons_str:
                def_hz.append("🔭 Multi-Day Swing Trading")
            if "LONG_TERM" in cur_horizons_str:
                def_hz.append("🌱 Long-Term Compounding")

            sel_hz = st.multiselect(
                "Authorized Trading Horizons",
                options=h_opts,
                default=def_hz if def_hz else h_opts,
                key="settings_ms_at_horizons",
            )
        with c_pos:
            max_p_val = st.slider(
                "Max Concurrent Positions",
                min_value=1,
                max_value=5,
                value=cur_max_pos,
                key="settings_slider_max_pos",
            )

        c_rk1, c_rk2 = st.columns(2)
        with c_rk1:
            risk_cap_val = st.slider(
                "Risk Cap Per Trade (%)",
                min_value=0.2,
                max_value=3.0,
                value=round(cur_risk_cap * 100, 1),
                step=0.1,
                key="settings_slider_risk_cap",
                help="Strict 1% risk budgeting rule: position sizes are mathematically scaled so that a stop-out never exceeds this % of capital.",
            ) / 100.0
        with c_rk2:
            broker_sel = st.selectbox(
                "Live Broker Gateway Provider",
                options=SUPPORTED_BROKERS,
                index=SUPPORTED_BROKERS.index(cur_broker) if cur_broker in SUPPORTED_BROKERS else 0,
                key="settings_broker_sel",
            )

        if target_exec_mode == "LIVE_BROKER":
            st.warning("⚠️ **Live Broker Gateway Activated**: Real orders will be transmitted to your broker endpoint.")
            brk_url_val = st.text_input(
                "Broker Webhook / Gateway Endpoint URL",
                value=cur_webhook,
                type="password",
                key="settings_broker_webhook_input",
                placeholder="https://api.kite.trade/orders",
            )
        else:
            brk_url_val = cur_webhook

        if st.button("💾 Save Auto-Trader Settings", key="btn_save_auto_trader_settings", use_container_width=True):
            mapped_h = []
            for h in sel_hz:
                if "Day" in h:
                    mapped_h.append("DAY_TRADE")
                if "Swing" in h:
                    mapped_h.append("SWING_TRADE")
                if "Long-Term" in h:
                    mapped_h.append("LONG_TERM")

            new_at_cfg = {
                "is_enabled": t_master,
                "execution_mode": target_exec_mode,
                "enabled_horizons": ",".join(mapped_h) if mapped_h else "DAY_TRADE",
                "max_concurrent_positions": max_p_val,
                "risk_pct_per_trade": risk_cap_val,
                "allocated_budget": float(get_user_preferences().get("total_capital", 500000.0)),
                "selected_broker": broker_sel,
                "broker_webhook_url": brk_url_val.strip(),
            }
            save_auto_trader_config(new_at_cfg)
            st.toast("✅ Auto-Trader preferences saved successfully!", icon="🤖")
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3: ACCOUNT & RISK PROFILE
    # ══════════════════════════════════════════════════════════════════════════
    with t_account:
        st.markdown("### 💰 Account Budget & Risk Profile")
        cur_prefs = get_user_preferences()
        saved_cap = float(cur_prefs.get("total_capital", 500000.0))
        saved_risk_pct = float(cur_prefs.get("risk_pct", 0.01))

        c_ac1, c_ac2 = st.columns(2)
        with c_ac1:
            acc_cap = st.number_input(
                "Total Trading Capital (₹)",
                min_value=1_000.0,
                value=saved_cap,
                step=25_000.0,
                key="settings_acc_capital_input",
                help="Your total portfolio capital, used to size all trades mathematically.",
            )
        with c_ac2:
            acc_risk = st.slider(
                "Default Risk Per Trade (%)",
                min_value=0.1,
                max_value=5.0,
                value=round(saved_risk_pct * 100, 1),
                step=0.1,
                key="settings_acc_risk_slider",
            ) / 100.0

        if st.button("💾 Save Account Budget", key="btn_save_account_budget", use_container_width=True):
            save_user_preference("total_capital", acc_cap)
            save_user_preference("risk_pct", acc_risk)
            st.session_state["total_capital"] = acc_cap
            st.session_state["risk_pct"] = acc_risk
            st.toast("✅ Account capital & risk preferences saved!", icon="💰")
            st.rerun()

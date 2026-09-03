# FinVision: Master Architecture, Operations & Reference Guide
> **Document Purpose**: Comprehensive system blueprint and state reference for future development sessions, AI agent handoffs, and operational maintenance.

---

## 📌 1. Project Identity & Vision

* **Project Name**: FinVision (Terminal & Wealth Copilot)
* **Target Market**: Indian Equity & Derivative Markets (NSE / BSE / Nifty 50 / Bank Nifty).
* **Core Philosophy**: A zero-knowledge-friendly, institutionally rigorous quantitative system designed to trade systematically, protect capital with mathematical stop-losses (1% max risk rule), compound multi-year wealth, and self-evolve into a mature algorithmic trader.

---

## 🌐 2. Live Deployment Endpoints & Environments

| Environment | Endpoint / Location | Details |
| :--- | :--- | :--- |
| **Cloud Production** | `https://finvision-8ysyduhykcish78fnyoxrf.streamlit.app` | Hosted on Streamlit Community Cloud. Linked to GitHub `main` branch. |
| **GitHub Master Repo** | `https://github.com/shriharinair-create/finvision` | Public repository. Auto-deploys to Streamlit Cloud on push. |
| **Local PC Repository** | `G:\AI\Stock\Stock_Claude\finvision_bkp` | Primary source workspace. |
| **Cloud Staging Dir** | `G:\AI\Stock\Stock_Claude\finvision_bkp\cloud_deploy` | Mirror directory pushed directly to GitHub. |
| **Android Client (APK)** | `G:\AI\FinVision_APKs\FinVision.apk` | Unified native Android container (`com.finvision.terminal`). |
| **Target Mobile Device** | OnePlus/Oppo CPH2793 (`3C166K010Q800000`) | Android 16 / ColorOS. Single app with 1-tap mode switcher. |

---

## 📱 3. Mobile Client Architecture

* **Package ID**: `com.finvision.terminal` (Legacy `com.finvision.pc` has been uninstalled).
* **Mode Switcher**:
  * **`[ 🌐 Cloud ]`**: Connects to the live Streamlit Community Cloud URL.
  * **`[ 💻 PC ]`**: Connects to the local PC Wi-Fi server (`http://<PC_IP>:8501`).
  * **`[ 📱 Mobile ]`**: Offline HTML5/JS standalone engine (`assets/standalone/index.html`).
  * **Floating Purple Wrench Button (`fabSwitchMode`)**: Instant switcher accessible from any screen.
* **Key Android Fixes**:
  * `swipeRefresh.setEnabled(false)` applied in `MainActivity.java` to eliminate gesture conflict where scrolling up would accidentally trigger page refreshes.
  * Cleartext traffic enabled via `network_security_config.xml` for seamless local LAN connectivity.

---

## 🧠 4. Core Quantitative & AI Intelligence Layers

### Layer 1: Market Regime Detection (`utils/regime.py`)
Monitors Nifty 50 (`^NSEI`) 20/50/200 EMA structure and India VIX (`^INDIAVIX`) to classify the market into 4 seasons:
1. **`BULL_MARKUP`**: Breakouts favored, $1.0\text{x}$ position size, $1.3\text{x}$ ATR profit targets.
2. **`HIGH_VOLATILITY_CHOP`**: Breakouts fail 65%+; switches to mean-reversion dip buying, $0.6\text{x}$ size, $1.35\text{x}$ stop buffer.
3. **`BEAR_MARKDOWN`**: Capital preservation mode, longs restricted, $0.4\text{x}$ size cap.
4. **`QUIET_ACCUMULATION`**: Low VIX ($<13$), Wyckoff float absorption favored.

### Layer 2: Lopez de Prado Meta-Labeling ("The Veteran Brain" — `utils/meta_labeling.py`)
A secondary filter evaluating trade setups against multi-dimensional market features:
* **$P(\text{Win}) < 45\%$**: **⛔ AI VETO (0.0x size)** — Skips setup to prevent drawdowns.
* **$45\% \le P(\text{Win}) < 62\%$**: **⚠️ HALF SIZE (0.5x size)** — Cautious risk execution.
* **$P(\text{Win}) \ge 62\%$**: **✅ FULL CONVICTION (1.0x size)** — High-probability alignment.

### Layer 3: Automated Trade Post-Mortem Autopsy Engine (`utils/trade_postmortem.py`)
Conducts automated autopsies on closed paper/live trades:
* **`LIQUIDITY_SWEEP_HUNT`**: Detects if price pierced SL by $<0.85\%$ and reversed straight to target $\rightarrow$ Auto-widens stock-specific ATR buffer multiplier (e.g. $1.0\text{x} \rightarrow 1.35\text{x}$).
* **`MACRO_REGIME_DRAG`**: Flags systemic Nifty drops ($>1.25\%$) rather than individual setup failure.
* **`TARGET_BLOWOFF_RUNNER`**: Detects runaway momentum and extends runner targets.

### Layer 4: Veteran Wisdom Fact-Check Lab (`utils/veteran_evaluator.py`)
* Parses unstructured advice from senior traders, books, and mentors.
* Runs automated **2-year empirical walk-forward backtests** across NSE historical data.
* Classifies as **`VALIDATED_ACTIVE`** (Win rate $\ge 55\%$, Profit Factor $\ge 1.35\text{x}$) or **`REJECTED_MYTH`** (discarded folklore).

### Layer 5: 15-Minute Institutional Candlestick Prediction Standard (`utils/forecasting.py`)
* Slices trading session into **25 clean 15-minute bars** (09:15 – 15:30 IST) instead of 75 5-minute bars.
* **Reduces microstructure random walk noise by $\approx 42\%$**, matching institutional TWAP/VWAP algorithmic execution blocks.

### Layer 6: Triple-Barrier Monte Carlo & Conformal Bounds (`utils/forecasting.py`)
* 1,000 Monte Carlo paths with Student's $t$ fat-tail innovations.
* Calculates path-dependent first-touch probabilities: $P(\text{Target Hit First})$, $P(\text{Stop Hit First})$, Expected Value ($\text{EV}\%$), and empirical 10th/90th percentile conformal bounds.

---

## 🗄️ 5. Database Schema (`finvision_data.db` via `utils/market_store.py`)

1. **`paper_trades`**: Simulated trade logs (Entry, Target, Stop, Shares, Realized P&L).
2. **`trade_postmortems`**: Diagnostic autopsies (Diagnosis Code, Root Cause Attribution, Corrective Learning, Buffer Multiplier).
3. **`adaptive_stock_buffers`**: Learned stock-specific ATR stop multipliers and operator liquidity sweep counts.
4. **`regime_history`**: Daily timeline of Indian Market Regimes.
5. **`veteran_wisdom_registry`**: Tested veteran rules, win rates, profit factors, and active status.
6. **`causal_rules`**: Mined keyword catalysts with Benjamini-Hochberg FDR correction.
7. **`intraday_forecast_snapshots`**: Real-time intraday forecast trajectory adaptation records.

---

## 🧭 6. Operating Modes & Sitemap

* **Mode 0: Smart Copilot**: Zero-knowledge autopilot. Displays active Regime Radar, Top Setups with Meta-Labeling Badges, Anti-Sweep Stops, ELI5 boxes, and Custom Stock Search.
* **Mode 1: Multi-Horizon Market Scanner**: Scans top liquid stocks for institutional momentum, delivery spikes, and Wyckoff volume absorption.
* **Mode 2: News & Catalyst Intelligence**: Semantic ChromaDB vector search + live multi-source news polling (Moneycontrol, ET, Mint, BS, YF).
* **Mode 3: Live Intraday Monitor**: Live auto-refreshing telemetry, VWAP, EMA 9, and 15-Minute Institutional Candlestick Forecast.
* **Mode 4: Quantitative Forecast Lab**: Fused confluence scoring, Triple-Barrier probability cards, 15m trajectory cone, and walk-forward backtest audits.
* **Mode 5: Long-Term Wealth Compounding**: Blue-chip fundamental scoring, wide-moat screening, and SIP compound growth calculators.
* **Mode 6: AI Academy & Evolution Lab**:
  * Tab 1: Live Paper Trading Portfolio.
  * Tab 2: 🧠 AI Post-Mortem & Evolution Lab (Autopsy feed & regime timeline).
  * Tab 3: 🎖️ Veteran Wisdom Fact-Check Lab (Empirical backtest validator).
  * Tab 4: Micro-Lessons & Financial Jargon Translator.

---

## 🛠️ 7. Standard Operational Runbook

### Running the PC Server:
```powershell
cd G:\AI\Stock\Stock_Claude\finvision_bkp
streamlit run app.py
```

### Deploying to Cloud & GitHub:
```powershell
Copy-Item "g:\AI\Stock\Stock_Claude\finvision_bkp\utils\*" "g:\AI\Stock\Stock_Claude\finvision_bkp\cloud_deploy\utils\" -Recurse -Force
Copy-Item "g:\AI\Stock\Stock_Claude\finvision_bkp\app_pages\*" "g:\AI\Stock\Stock_Claude\finvision_bkp\cloud_deploy\app_pages\" -Recurse -Force
Copy-Item "g:\AI\Stock\Stock_Claude\finvision_bkp\app.py" "g:\AI\Stock\Stock_Claude\finvision_bkp\cloud_deploy\app.py" -Force
git -C "g:\AI\Stock\Stock_Claude\finvision_bkp\cloud_deploy" add .
git -C "g:\AI\Stock\Stock_Claude\finvision_bkp\cloud_deploy" commit -m "<Description of changes>"
git -C "g:\AI\Stock\Stock_Claude\finvision_bkp\cloud_deploy" push origin main
```

### Recompiling Android APK:
```powershell
& "C:\Users\HomePod\.gradle\wrapper\dists\gradle-8.9-bin\90cnw93cvbtalezasaz0blq0a\gradle-8.9\bin\gradle.bat" -p "g:\AI\Stock\Stock_Claude\finvision_bkp\android_client" assembleDebug
Copy-Item "g:\AI\Stock\Stock_Claude\finvision_bkp\android_client\app\build\outputs\apk\debug\app-debug.apk" "G:\AI\FinVision_APKs\FinVision.apk" -Force
```

### Installing on Connected Android Device via ADB:
```powershell
adb -s 3C166K010Q800000 push "G:\AI\FinVision_APKs\FinVision.apk" /data/local/tmp/FinVision.apk
adb -s 3C166K010Q800000 shell pm install -r -t --user 0 /data/local/tmp/FinVision.apk
```

---

## 🔍 8. Key Known Resolutions & Diagnostics

1. **`torchvision` in Cloud Deployment**: Must be explicitly declared in `requirements.txt` alongside `torch` and `transformers` to prevent import failures in Streamlit Cloud Linux containers.
2. **HTML Markup in `st.markdown`**: CommonMark interprets lines with 4+ leading spaces as `<pre><code>` code blocks. All multiline HTML strings passed to `st.markdown(..., unsafe_allow_html=True)` must be wrapped in `textwrap.dedent(...)`.
3. **Android Client Default Launch**: Configured in `MainActivity.java` to default to `BuildConfig.DEFAULT_CLOUD_URL` so mobile users immediately receive the full, real-time Python Streamlit terminal instead of the offline HTML fallback.
4. **Dalal Street Veteran Wisdom Input**: Accessible both in **Mode 0 (Smart Copilot)** via the dedicated expander and **Mode 6 (AI Academy Tab 3)**, running 2-year empirical walk-forward backtests.


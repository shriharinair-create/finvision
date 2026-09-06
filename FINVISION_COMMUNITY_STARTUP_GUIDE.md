# 🚀 FinVision v3.0 — The Beginner's Field Manual
### *How to Set Up, Customize Your Quant Personas, Run Simulations, and Switch to Real Trading Safely*

Welcome to **FinVision**! Think of this platform as an institutional quantitative analyst and risk manager sitting beside you on Dalal Street. 

You do **not** need a degree in finance, programming experience, or years of chart-reading to use it. This manual takes you step-by-step from zero to running and customizing an automated quantitative trading system safely.

---

## 🗺️ The 6-Stage Mastery Roadmap

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     STAGE 1     │──►│     STAGE 2     │──►│     STAGE 3     │──►│     STAGE 4     │──►│     STAGE 5     │──►│     STAGE 6     │
│ Device & Login  │   │ Navigation Map  │   │ Quant Sandbox   │   │ 3 Trade Options │   │ Broker Plumbing │   │ Safe Scaling    │
│ (2 Minutes)     │   │ (Where Modes 1, │   │ (Custom Persona │   │ (Auto vs GTT    │   │ 1-Share Test    │   │ (10% ➔ 100%)    │
│ Zero App Hassle │   │  2 & Labs Live) │   │  & Sector Pods) │   │  vs Pro Manual) │   │ (API / GTT)     │   │ Compounding     │
└─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 📱 Stage 1: Getting FinVision on Your Device (2 Minutes)

Because the terminal is hosted 24/7 in the cloud, you can open it on any device without keeping your computer on.

### 🍏 On iPhone or iPad (Zero App Store Hassle)
1. Open **Safari** on your iPhone.
2. Go to your terminal link: **`http://92.4.71.16:8501`**
3. Tap the **Share button** at the bottom (square with an up arrow `[↑]`).
4. Scroll down and tap **"Add to Home Screen"** `[+]`.
5. Tap **Add**. 
*FinVision will now appear on your home screen with its app icon and launch fullscreen like a native iOS app.*

### 🤖 On Android Phones
* **Option A (Dedicated Native App):** Tap the **`📥 Download APK`** button directly on the FinVision login screen or download it directly from the server: **`http://92.4.71.16:8001/static/FinVision.apk`**. Once downloaded, tap the notification to install the dedicated mobile terminal.
* **Option B (Instant Browser PWA — Zero Download):** Open Chrome on your phone, navigate to `http://92.4.71.16:8501`, tap the three dots `⋮` at top-right $\rightarrow$ select **"Add to Home screen"** or **"Install App"**. FinVision will install seamlessly without any sideloading warnings.

### 💻 On Laptop / Desktop (Windows, Mac, Linux)
Open Chrome, Brave, Safari, or Edge and bookmark:
**`http://92.4.71.16:8501`**

---

## 🔑 Stage 1.5: Secure Profile Setup & Instant Login

FinVision uses an institutional **Multi-Tenant Profile Isolation** system with **Zero User Enumeration**. No visitor can ever see existing user accounts or administrator credentials on the login screen.

### 👤 Creating Your Private Account (First-Time Users):
1. Open `http://92.4.71.16:8501`.
2. Click the **"➕ New Profile"** tab.
3. Enter your details:
   * A unique **Trader Username** (e.g. `rahul`)
   * Your **Display Name** (e.g. `Rahul Sharma`)
   * A strong **Master Passphrase** (Min 8 characters)
   * A 4-Digit **Security PIN** (e.g. `1234`)
4. Click **✨ Create Account & Reveal Backup Phrase**.
5. **Private Ledger Guarantee:** FinVision gives you your own isolated virtual trading wallet. Your capital budget, watchlists, trade history, and active positions are completely private—no other trader can see or modify your account.
6. **Backup Phrase:** Save the 4-word recovery phrase displayed upon registration (e.g. `falcon-river-summit-copper`) in your private notes.

### ⚡ Unlocking Your Terminal (Returning Users):
1. Open `http://92.4.71.16:8501`.
2. In the **`⚡ Quick PIN`** tab:
   * **Save Username (No Need to Re-enter):** Check the **"💾 Remember Username"** checkbox. FinVision will permanently save your username on this device. On every future visit, your username is automatically pre-filled!
   * In the **4-Digit Security PIN** box, enter your secret PIN (e.g. `1234`).
   * Click **🚀 Unlock Terminal**.
3. **👆 Biometric & Touch ID / Face ID Unlock:**
   * **Mobile Keychain Face ID (Instant):** When prompted by your mobile browser (Apple Safari or Android Chrome), save your credentials to **Apple Keychain** or **Google Password Manager**. Tapping the PIN box will trigger native **Face ID / Touch ID / Fingerprint** to autofill your PIN in a single glance!
   * **Hardware WebAuthn Tab:** Switch to the **`👆 Biometric`** tab for hardware-level passkey authentication. *(Note: iOS Safari and Android Chrome require an HTTPS connection to access direct browser biometric hardware).*
4. **Master Passphrase Sign-In:** If using a new browser or clearing a PIN lockout, switch to the **`🔐 Passphrase`** tab.
5. **Self-Service PIN Reset (Zero App Required):** If you ever forget your PIN, switch to the **`🆘 Reset PIN`** tab to reset it in 5 seconds using your Master Passphrase or 4-Word Recovery Phrase directly in your browser.
6. **Switching Profiles / Locking:** To switch accounts or lock your terminal, tap **`🚪 Switch Profile / Logout`** in the left sidebar.

---

---

## 🧭 Stage 2: How to Navigate FinVision (Where to Find Mode 1, Mode 2 & All Features)

When you first unlock FinVision, the terminal defaults to **Mode 0: Smart Copilot**. 

### 📍 The Top Navigation Bar (Mode Switcher)
To navigate to any other mode—such as **Mode 1 (Pro Manual Trading)** or **Mode 2 (Market Scanner)**—look at the very top of your screen, directly beneath the red-and-white FinVision logo. 

Tap the dropdown box currently displaying **`🤖 Smart Copilot (0-Knowledge Autopilot) ▼`**. This opens the master mode selector drawer:

<div style="text-align: center; margin: 18px 0;">
  <img src="guide_assets/nav_mode_dropdown.png" style="max-width: 70%; border-radius: 10px; border: 1px solid #cbd5e1; box-shadow: 0 4px 14px rgba(0,0,0,0.12); display: inline-block;" />
  <p style="font-size: 11px; color: #64748b; font-style: italic; margin-top: 6px;"><b>Figure 1:</b> Master Mode Switcher Dropdown (select any mode from Dalal Street Copilot to Pro Terminal or Market Scanner).</p>
</div>

### 🗺️ Master Mode Directory:
* **🤖 Mode 0: Smart Copilot (Default)**: Institutional zero-knowledge autopilot. Hosts the Autonomous 4-Persona Quant Sandbox, sector pods, and daily trade recommendations.
* **⚙️ Settings & Cloud Backup Hub**: Connect your broker API keys (Zerodha, Upstox, Angel One), configure risk limits, and back up your private trading journal.
* **📡 Mode 2: Market Scanner & Top 10 Alpha**: Scans 500+ Indian equities for intraday momentum, Wyckoff breakouts, Camarilla pivots, and volume surges.
* **🌱 Mode 3: Long-Term Wealth & Compounder Lab**: Multi-year fundamental screener, DCF valuation models, Piotroski F-Scores, and debt-to-equity filters.
* **⚡ Mode 1: Live Intraday Monitor & Manual Ticker Analysis**: The Pro Manual Trading Terminal with multi-timeframe TradingView charts, quick stock selectors, and the Pro Order Pad.
* **🔬 Mode 4: Forecast & Correlation Lab**: Monte Carlo simulations and 10-day probabilistic cones for price trajectories.
* **🎓 Mode 6: AI Academy & Paper Trading**: Bite-sized lessons explaining institutional trading rules, risk:reward formulas, and finance terminology.

---

## 🎭 Stage 3: Customizing Your Auto-Trade Quant (Personas & Watchlists)

FinVision features an **Autonomous 4-Persona Quant Engine** embedded directly in **Mode 0 (AI Copilot)**. To prevent emotional human mistakes from contaminating the model, these personas explore different market setups in simulation.

<div style="text-align: center; margin: 18px 0;">
  <img src="guide_assets/nav_copilot_overview.png" style="max-width: 70%; border-radius: 10px; border: 1px solid #cbd5e1; box-shadow: 0 4px 14px rgba(0,0,0,0.12); display: inline-block;" />
  <p style="font-size: 11px; color: #64748b; font-style: italic; margin-top: 6px;"><b>Figure 2:</b> Mode 0 Copilot with the Autonomous Auto-Trader banner and real-time live scanner status.</p>
</div>

### 1. The 4 Algorithmic Personas:

| Persona | Quantitative Strategy | Target Market Regime | Natural Horizon |
| :--- | :--- | :--- | :--- |
| **⚡ Alpha Momentum Hunter** | High Beta (>1.05), RSI 55-72, ADX > 22, above 20 EMA | Trending Bull Markets | Swing (2–7 Days) |
| **🔄 Delta Mean Reverter** | RSI < 35, Lower Bollinger Band bounce, VWAP reversion | Rangebound Chop & Consolidation | Short Swing (1–3 Days) |
| **🛡️ Sigma Conservative Value** | Fundamental Quality > 75/100, Low Beta (<0.95), PE discount | Defensive / Correction Regimes | Positional (2–6 Weeks) |
| **🌪️ Vega Volatility Breakout** | Volume surge > 2.2x 20-day MA, ATR expansion, VIX burst | Event Breakouts & Earnings News | Intraday / Fast Scalp |

### 2. How to Control or Pause Your Automated Trades:

Because FinVision is a multi-user institutional platform, the central background daemon runs 24/7 on the cloud server under Admin management (powering real-time market scans and sector learning cohorts). You have complete, sovereign control over your own account's automation:

* **1-Tap Profile Pause (`🚨 PAUSE MY TRADES`):** Located right in the top engine card of Mode 0. A single click pauses all 4 of your personas immediately. No algorithmic trades will be placed for your account until you tap `▶️ RESUME MY TRADES`.
* **Fine-Grained Persona Toggles:** Open the **Autonomous 4-Persona Quant Sandbox** card in Mode 0 $\rightarrow$ expand **`⚙️ Persona Toggles & Capital Allocation (My Profile Only)`** $\rightarrow$ check or uncheck individual strategies:
   * `[x] ⚡ Alpha Momentum (Active)`
   * `[x] 🔄 Delta Mean Revert (Active)`
   * `[x] 🛡️ Sigma Value (Active)`
   * `[ ] 🌪️ Vega Breakout (Paused)` $\leftarrow$ *Disabled*
   * Tap **💾 Save Persona Settings**. 
   * *Your settings are 100% private and profile-specific. Pausing your personas never affects other community traders or the central scanner.*

### 3. How to Pick What Stocks the Personas Trade On:
Under **Mode 0 (AI Copilot)**, tap **`⚙️ Configure Autonomous Auto-Trader Settings & Toggles`**:
* **Option A: 🤖 Full AI Autopilot (Nifty 500 Radar) (Default)**:
  The scanning engine scans the liquid market universe to find the highest-probability technical setups matching active personas.
* **Option B: 🎯 Custom Watchlist (My Stocks Only)**:
  Select this to restrict autonomous scanning strictly to your favorite stocks. Enter comma-separated NSE tickers without `.NS`, for example:
  ```text
  RELIANCE, INFY, TATAMOTORS, HDFCBANK, ITC, TCS
  ```
  The bot will strictly scan and execute setups within this specific list, ignoring the rest of Dalal Street.

### 4. Automated 5 Sector Pods (Continuous Background Learning):
To accelerate machine learning across diverse sectors, FinVision runs **5 Automated Synthetic Sector Pods** on the server:
* **Banking & FinServ Pod** (₹50k)
* **IT & Tech Leaders Pod** (₹20k)
* **High-Beta Auto & Infra Pod** (₹50k)
* **FMCG & Pharma Defense Pod** (₹20k)
* **Full-Scale Core Blend Pod** (₹2 Lakhs Target)

You can monitor their comparative returns in Mode 0. When the calibration phase ends, a single click in the **"🗑️ Retire Synthetic Cohorts"** drawer safely removes all synthetic data. **Safety Guarantee:** All genuine personal trader accounts are protected by hardcoded safety whitelists and are 100% immune to deletion.

---

## 🎛️ Stage 4: Choosing Your Trading Mode (Where to Find the 3 Options)

FinVision supports 3 distinct operating paths depending on your comfort level:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      WHICH MODE IS RIGHT FOR YOU?                      │
├───────────────────┬───────────────────────────┬────────────────────────┤
│   OPTION A: AUTO  │   OPTION B: AI-ASSISTED   │   OPTION C: MANUAL     │
│   (Hands-Free)    │   (Human-in-the-Loop)     │   (Discretionary)      │
│                   │                           │                        │
│ The bot scans,    │ The AI suggests setups;   │ You analyze charts     │
│ calculates risk,  │ you review and approve    │ and execute trades     │
│ and executes      │ via 1-click Copy-Paste    │ with custom limits,    │
│ automatically via │ GTT order tickets in your │ stops, and horizons.   │
│ broker API.       │ mobile broker app.        │                        │
│                   │                           │                        │
│ Best for: Busy    │ Best for: Beginners who   │ Best for: Active chart │
│ professionals.    │ want 100% final sign-off. │ readers & scalpers.    │
└───────────────────┴───────────────────────────┴────────────────────────┘
```

---

### 🚀 Option A: Full Autonomous Auto-Trade (Hands-Free)

#### 📍 Where to Find It:
1. Switch to **Mode 0: Smart Copilot** (at the top dropdown).
2. Look directly below the header banner for the **`AUTONOMOUS AI ENGINE`** card.
3. **Engine Status:** You will see the server daemon badge: `🔒 Server Engine Daemon: 🟢 Running 24/7 (Managed by Platform Admin)`. The central engine continuously scans the market in the background so you never have to leave a laptop running.
4. **Pausing Your Account:** If you wish to temporarily halt automated trades on your profile, simply tap the red **`🚨 PAUSE MY TRADES`** button. All 4 of your personal personas will pause immediately. Tap **`▶️ RESUME MY TRADES`** when you want your personas to trade again.
5. **Configuration:** Click `⚙️ Configure Autonomous Auto-Trader Settings & Toggles` to choose your custom stock watchlist, maximum open positions, and account risk limits.

#### How It Works:
* During market hours (09:15 to 15:30 IST), the central engine scans Dalal Street every 3–5 minutes.
* It matches technical breakouts against active personas and sizes orders with strict 1% risk rules.
* **Simulation Mode (Default):** Automatically logs entries, exits, and PnL into your private trading journal.
* **Live Gateway Mode:** Dispatches orders directly through your linked broker API (Zerodha, Upstox, or Angel One).
* **Emergency RMS Circuit Breaker:** If your daily account drawdown reaches 2.5% or 3 consecutive losses occur, the RMS halts automated trading for your account for 24 hours.

---

### 🎯 Option B: AI-Assisted Manual Mode (1-Click Kite/Upstox GTT) — *RECOMMENDED FOR BEGINNERS*

This is the smartest way to transition from paper trading to real money without taking algorithmic execution risks:

#### 📍 Where to Find It:
1. In **Mode 0 (AI Copilot)** or inside any analyzed stock in **Mode 1**, look at the trade proposal card.
2. The AI calculates your exact position size, risk-to-reward ratio, entry, stop loss, and target exit.
3. Tap the **`📋 Copy Zerodha Kite GTT / Upstox Order`** drawer button:

<div style="text-align: center; margin: 18px 0;">
  <img src="guide_assets/nav_gtt_order_ticket.png" style="max-width: 70%; border-radius: 10px; border: 1px solid #cbd5e1; box-shadow: 0 4px 14px rgba(0,0,0,0.12); display: inline-block;" />
  <p style="font-size: 11px; color: #64748b; font-style: italic; margin-top: 6px;"><b>Figure 3:</b> AI-calculated 1% risk position sizer and 1-Click Zerodha Kite / Upstox GTT copy ticket.</p>
</div>

#### Step-by-Step GTT Execution:
1. Tap the **`🎯 1% Risk`** button to ensure your maximum potential loss is strictly bounded to 1% of your account capital.
2. Click **`📋 Copy Zerodha Kite GTT / Upstox Order`**. FinVision copies the pre-formatted order parameters to your clipboard.
3. Open your broker app (**Zerodha Kite** or **Upstox**) on your phone.
4. Search the stock ticker (e.g. `RELIANCE`) $\rightarrow$ select **Create GTT** (Good-Till-Triggered).
5. Paste or enter the pre-calculated numbers:
   * **Trigger Price:** AI Entry Price
   * **Stop-Loss Trigger:** AI Stop Price
   * **Target Trigger:** AI Target Exit
6. Tap **Place GTT**.
7. **Why this is unbeatable:** You maintain 100% human oversight. The order sits directly on the National Stock Exchange (NSE) servers. When hit, it executes automatically without you having to monitor live charts.

---

### ⚡ Option C: Full Manual Discretionary Trading Terminal

For traders who prefer to read candlestick charts, check Camarilla pivot levels, and place custom trades directly:

#### 📍 Where to Find It:
1. Open the top dropdown menu and tap **`⚡ Live Intraday Monitor`** or **`🔍 Manual Ticker Analysis`** (Mode 1).
2. You will see the **⚡ Pro Manual Trading Terminal** with Quick Access buttons for popular stocks (`RELIANCE`, `TCS`, `HDFCBANK`, `INFY`, `TATAMOTORS`, `ITC`, etc.):

<div style="text-align: center; margin: 18px 0;">
  <img src="guide_assets/nav_mode1_terminal.png" style="max-width: 70%; border-radius: 10px; border: 1px solid #cbd5e1; box-shadow: 0 4px 14px rgba(0,0,0,0.12); display: inline-block;" />
  <p style="font-size: 11px; color: #64748b; font-style: italic; margin-top: 6px;"><b>Figure 4:</b> Mode 1 Pro Manual Trading Terminal with quick stock selection chips.</p>
</div>

#### Using the Pro Order Pad:
1. Tap any stock button or type any valid NSE ticker into the search box.
2. Review the live technical chart with EMA 9/21, VWAP, Supertrend, or Bollinger Bands.
3. Scroll to the **📝 Pro Order Pad** located right beneath the charts:

<div style="text-align: center; margin: 18px 0;">
  <img src="guide_assets/nav_manual_order_pad.png" style="max-width: 70%; border-radius: 10px; border: 1px solid #cbd5e1; box-shadow: 0 4px 14px rgba(0,0,0,0.12); display: inline-block;" />
  <p style="font-size: 11px; color: #64748b; font-style: italic; margin-top: 6px;"><b>Figure 5:</b> Pro Order Pad with AI Conviction Radar, Market Regime filters, and custom limit controls.</p>
</div>

4. Configure your trade:
   * **Side:** `BUY (LONG)` or `SELL (SHORT)`
   * **Product:** `CNC (Delivery / Swing)` or `MIS (Intraday)`
   * **Order Type:** `LIMIT` or `MARKET`
   * **Entry Price, Stop Loss, and Target Exit**
5. Click **`🚀 Execute Paper Trade`** (or route to your connected broker gateway).
6. **Institutional AI Safety Net:** Even in manual mode, FinVision automatically scans your trade against the India VIX panic shield, market regime score, and corporate earnings blackouts to alert you if you are entering against the trend.

---

## 🔧 Stage 5: The "Broker Plumbing" Phase (Switching to Real Money)

Once you are satisfied with your simulation results (e.g. 30–50 paper trades completed), follow this safe transition checklist:

### 1. Linking Your Broker in Settings
1. In the sidebar, click **⚙️ Settings** $\rightarrow$ **Tab 2: Autonomous Auto-Trader Defaults**.
2. Select your broker:
   * **Zerodha Kite Connect**
   * **Angel One SmartAPI**
   * **Upstox API**
   * **TradingView / n8n Webhook**
3. Enter your API Key, Secret, and User ID.

### 2. The 1-Share Test Rule (MANDATORY SAFEGUARD)
**Never test a new broker connection with full capital.**
1. In the sidebar, set your capital budget to **₹1,000**.
2. Switch **Execution Guard Mode** from `Safe Simulation` to `Live Broker Gateway`.
3. Allow the system (or place an AI-assisted order) to trade **1 single share** (e.g. 1 share of ITC or Tata Motors).
4. Verify in your broker mobile app that:
   * The order was received.
   * The quantity was exactly 1.
   * The stop-loss was placed correctly.
5. Once verified, you have confirmed that the plumbing is 100% functional.

---

## 📈 Stage 6: Scaling Up Safely (The Institutional Ladder)

Never jump from ₹0 to ₹2 Lakhs in one day. Use this disciplined schedule:

```
Month 1:    ₹0 Real Money     (100% Simulation — Calibrate the 4 Personas)
Month 2:    ₹10,000 – ₹20,000 (AI-Assisted Manual GTTs — Build execution discipline)
Month 3:    ₹20,000 (10%)      (1-Share API Live Testing — Verify broker latency)
Month 4:    ₹50,000 (25%)      (Auto-Trade with 1-2 conservative personas)
Month 5:    ₹1,00,000 (50%)    (Scale up to 3 personas across balanced sectors)
Month 6+:   ₹2,00,000 (100%)   (Full deployment across all 4 personas)
```

---

## 🛡️ The 5 Golden Rules ("Never Lose Your Shirt")

1. **The 1% Rule:** Never risk more than 1% of your total capital on a single trade. (If capital is ₹2,00,000, your maximum loss on a bad trade must never exceed ₹2,000). FinVision enforces this math automatically.
2. **The VIX Panic Shield:** If the India VIX spikes above **22.0**, FinVision locks out breakout buys. Respect this. High volatility wipes out retail traders.
3. **Friday Afternoon Rule:** Never initiate new multi-day swing trades on Friday after **14:30 IST**. Geopolitical events over Saturday/Sunday can cause disastrous Monday gap-downs.
4. **Never Override the AI During a Trade:** If an order triggers a stop-loss, let it exit. Moving your stop-loss further away is the #1 reason retail accounts blow up.
5. **Emergency Kill Switch:** If you ever feel uncomfortable or market news breaks unexpectedly, open FinVision and tap **`🚨 EMERGENCY KILL`** to immediately halt all new entries for the day.

---

### Need Help or Looking for More Guidance?
* Open **Mode 6: Trader Academy** inside the app for bite-sized lessons on the 2:1 R:R rule, post-mortem autopsies, and the financial jargon dictionary.
* Open **Mode 4: Forecast Engine** for 10-day probabilistic cones and price trajectories before entering any manual trade.

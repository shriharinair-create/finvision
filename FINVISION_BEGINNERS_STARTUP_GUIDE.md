# 🚀 FinVision v3.0 — The Beginner's Field Manual
### *How to Set Up, Customize Your Quant Personas, Run Simulations, and Switch to Real Trading Safely*

Welcome to **FinVision**! Think of this platform as an institutional quantitative analyst and risk manager sitting beside you on Dalal Street. 

You do **not** need a degree in finance, programming experience, or years of chart-reading to use it. This manual takes you step-by-step from zero to running and customizing an automated quantitative trading system safely.

---

## 🗺️ The 5-Stage Mastery Roadmap

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│     STAGE 1     │ ───► │     STAGE 2     │ ───► │     STAGE 3     │ ───► │     STAGE 4     │ ───► │     STAGE 5     │
│ Device & Login  │      │ Quant Sandbox   │      │ Mode Selection  │      │ Broker Plumbing │      │ Safe Scaling    │
│ (2 Minutes)     │      │ (Custom Personas│      │ (Auto / AI-Assis│      │ 1-Share Test    │      │ (10% ➔ 100%)    │
│ Zero App Hassle │      │ & Sector Pods)  │      │ vs Full Manual) │      │ (API / GTT)     │      │ Compounding     │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

## 📱 Stage 1: Getting FinVision on Your Device (2 Minutes)

Because your server is hosted 24/7 in the cloud on an isolated Oracle VM, you can open it on any device without keeping your computer on.

### 🍏 On iPhone or iPad (Zero App Store Hassle)
1. Open **Safari** on your iPhone.
2. Go to: **`http://92.4.71.16:8501`**
3. Tap the **Share button** at the bottom (square with an up arrow `[↑]`).
4. Scroll down and tap **"Add to Home Screen"** `[+]`.
5. Tap **Add**. 
*FinVision will now appear on your home screen with its app icon and launch fullscreen like a native iOS app.*

### 🤖 On Android Phones
* **Option A (Installed App):** Install the provided `app-debug.apk`. Open the app—it connects directly to the 24/7 cloud terminal.
* **Option B (Chrome Browser):** Open Chrome, navigate to `http://92.4.71.16:8501`, tap the three dots `⋮` at top-right $\rightarrow$ **"Add to Home screen"**.

### 💻 On Laptop / Desktop (Windows, Mac, Linux)
Open Chrome, Brave, Safari, or Edge and bookmark:
**`http://92.4.71.16:8501`**

---

## 🔑 Stage 1.5: Privacy-First Multi-Tenant Login & Recovery

FinVision uses an institutional **Multi-Tenant Profile Isolation** system with **Zero User Enumeration**. No visitor can ever see existing user accounts or administrator credentials on the login screen.

### 👤 How YOU Log In (Any Device, Any Time):
1. On your phone, tablet, or laptop, open `http://92.4.71.16:8501`.
2. On the **"Access Your Private Trading Terminal"** card:
   * In the **Trader Username** box, type your username: **`shrihari`**.
   * In the **4-Digit Security PIN** box, enter your secret PIN.
   * Click **🚀 Unlock Terminal**.
3. **Alternative Master Passphrase:** If on a new device or locked out due to PIN attempts, switch to the **`🔐 Passphrase`** tab to sign in securely.
4. **Self-Service PIN Recovery (Zero App Required):** If you ever forget your PIN, switch to **`🆘 Reset PIN`** tab to reset it in 5 seconds using your Master Passphrase or 4-Word Recovery Phrase.

### 👥 How Your Friends Log In (Complete Isolation):
1. When your friends open the link on their device, the screen is completely blank.
2. They click the **"➕ New Profile"** tab.
3. They enter:
   * A unique **Username** (e.g., `rahul`)
   * Their **Display Name** (e.g., `Rahul Sharma`)
   * A secret **Master Passphrase** (Min 8 characters)
   * A 4-Digit **Security PIN** (e.g., `1234`)
4. Click **✨ Create Account & Reveal Backup Phrase**.
5. **Zero Interference Guarantee:** Each friend receives their own isolated paper trading ledger. If they change settings or test trades, **your portfolio and settings are 100% untouched**.
6. **Switching Accounts:** To switch profiles or lock the terminal, tap **`🚪 Switch Profile / Logout`** in the left sidebar.

---

## 🎭 Stage 2: Customizing Your Auto-Trade Quant (Personas & Watchlists)

FinVision features an **Autonomous 4-Persona Quant Engine** embedded directly in **Mode 0 (AI Copilot)**. To prevent emotional human mistakes from contaminating the model, these personas explore different market setups in simulation.

### 1. The 4 Algorithmic Personas:

| Persona | Quantitative Strategy | Target Market Regime | Natural Horizon |
| :--- | :--- | :--- | :--- |
| **⚡ Alpha Momentum Hunter** | High Beta (>1.05), RSI 55-72, ADX > 22, above 20 EMA | Trending Bull Markets | Swing (2–7 Days) |
| **🔄 Delta Mean Reverter** | RSI < 35, Lower Bollinger Band bounce, VWAP reversion | Rangebound Chop & Consolidation | Short Swing (1–3 Days) |
| **🛡️ Sigma Conservative Value** | Fundamental Quality > 75/100, Low Beta (<0.95), PE discount | Defensive / Correction Regimes | Positional (2–6 Weeks) |
| **🌪️ Vega Volatility Breakout** | Volume surge > 2.2x 20-day MA, ATR expansion, VIX burst | Event Breakouts & Earnings News | Intraday / Fast Scalp |

### 2. How to Turn Off Specific Personas:
1. Open **Mode 0 (AI Copilot)**.
2. Scroll to the **Autonomous 4-Persona Quant Sandbox** card.
3. Expand **`⚙️ Persona Toggles & Capital Allocation (My Profile Only)`**.
4. Uncheck the **Active** checkbox next to any persona you wish to pause:
   * `[x] ⚡ Alpha Momentum (Active)`
   * `[x] 🔄 Delta Mean Revert (Active)`
   * `[x] 🛡️ Sigma Value (Active)`
   * `[ ] 🌪️ Vega Breakout (Paused)` $\leftarrow$ *Disabled*
5. Click **💾 Save Persona Settings**. 
*The paused persona will display a `⏸️ PAUSED` badge and will no longer place trades for your profile. Your friends' settings are completely unaffected.*

### 3. How to Pick What Stocks the Personas Trade On:
Under **Mode 0 (AI Copilot)**, open the **Auto-Trader Settings Drawer** (gear icon above the Auto-Trade toggle):
* **Option A: 🤖 Full AI Autopilot (Nifty 500 Radar) (Default)**:
  The scanning engine scans the liquid market universe to find the highest-probability technical setups matching active personas.
* **Option B: 🎯 Custom Watchlist (My Stocks Only)**:
  Select this to restrict autonomous scanning strictly to your favorite stocks. Enter comma-separated NSE tickers without `.NS`, for example:
  ```text
  RELIANCE, INFY, TATAMOTORS, HDFCBANK, ITC, TCS
  ```
  The bot will strictly scan and execute setups within this specific list, ignoring the rest of Dalal Street.

### 4. Automated 5 Sector Pods (Continuous Background Learning):
To accelerate machine learning without relying on friends, FinVision runs **5 Automated Synthetic Sector Pods** on the server:
* **Banking & FinServ Pod** (₹50k)
* **IT & Tech Leaders Pod** (₹20k)
* **High-Beta Auto & Infra Pod** (₹50k)
* **FMCG & Pharma Defense Pod** (₹20k)
* **Full-Scale Core Blend Pod** (₹2 Lakhs Target)

You can monitor their comparative returns in Mode 0. When the calibration phase ends, a single click in the **"🗑️ Retire Synthetic Cohorts"** drawer safely removes all synthetic data. **Safety Guarantee:** Your personal account (`shrihari`) is protected by hardcoded safety whitelists and is 100% immune to deletion.

---

## 🎛️ Stage 3: Choosing Your Trading Mode (Auto vs AI-Assisted vs Full Manual)

FinVision supports 3 distinct operating modes depending on your comfort level:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      WHICH MODE IS RIGHT FOR YOU?                      │
├───────────────────┬───────────────────────────┬────────────────────────┤
│   MODE A: AUTO    │   MODE B: AI-ASSISTED     │   MODE C: MANUAL       │
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

### Mode A: Full Autonomous Auto-Trade (Hands-Free)
1. **How it works:** When the master Auto-Trade switch in Mode 0 is **ON**, the cloud engine scans Dalal Street every 3–5 minutes during market hours. It filters candidates, sizes orders with strict 1% risk rules, and automatically places orders.
2. **Simulation vs Live:**
   * In **Simulation Mode**, it records entries and exits to your virtual journal.
   * In **Live Broker Gateway Mode**, it dispatches orders directly to Zerodha, Angel One, Upstox, or Webhook.
3. **Safety Circuit Breakers:** If daily drawdown exceeds 2.5% or 3 consecutive losses occur, the RMS immediately trips the emergency brake and freezes trading for 24 hours.

### Mode B: AI-Assisted Manual Mode (The "Copilot" — RECOMMENDED FOR BEGINNERS)
This is the smartest way to transition from paper trading to real money:
1. In **Mode 0 (AI Copilot)**, view **Setup #1** or check the scan candidates.
2. The AI calculates:
   * **Exact Quantity** (sized so your loss is $\le 1\%$ of capital).
   * **Entry Trigger Price**
   * **Stop-Loss Trigger Price**
   * **Target Exit Price**
3. Open the **📋 Zerodha / Upstox GTT Order** box.
4. Open your Zerodha Kite or Upstox app on your phone $\rightarrow$ search the ticker $\rightarrow$ tap **Create GTT** $\rightarrow$ copy-paste the numbers provided by FinVision $\rightarrow$ tap **Place**.
5. **Why this is unbeatable:** You maintain 100% human oversight. The order sits directly on the National Stock Exchange (NSE) servers. When hit, it executes automatically without you having to stare at the screen.

### Mode C: Full Manual Discretionary Mode
1. Open **Mode 1 (Live Terminal & Chart)** or **Mode 2 (Scan & Screen)**.
2. Pick any stock from NSE or BSE.
3. Open the **Order Pad** on the right side:
   * Select order type (**MARKET**, **LIMIT**, or **SL**).
   * Select trading horizon (**INTRADAY**, **SWING**, or **LONG-TERM DELIVERY**).
   * Set your custom entry, target, and stop loss.
4. Click **🚀 Execute Paper Trade** (or route to broker).
5. **AI Safety Net:** Even in manual mode, FinVision automatically evaluates your setup against the India VIX panic shield, Wyckoff market regime, and corporate earnings blackouts.

---

## 🔧 Stage 4: The "Broker Plumbing" Phase (Switching to Real Money)

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

## 📈 Stage 5: Scaling Up Safely (The Institutional Ladder)

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

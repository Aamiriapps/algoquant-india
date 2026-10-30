# AlgoQuant India: NSE Algorithmic Trading Suite (Nifty 500 Universe)

A systematic quantitative trading suite for the **Indian Stock Market (NSE/BSE)** featuring the **Nifty 500 Market Cap Companies (NSE Nifty 500 Index)** with strictly no penny or illiquid stocks.

The platform provides **two distinct, dedicated strategy engines**:
1. **📅 Section 1: Daily Swing Trading Strategy** (`50 EMA + Supertrend 10, 3` on Daily Timeframe)
2. **⚡ Section 2: Intraday Momentum Strategy** (`200 EMA + Supertrend 10, 3` on 15-Minute Candles)

---

## 🎯 Dual Strategy Specifications

### 1. Daily Swing Trading Strategy (Daily Timeframe)
- **Universe**: Nifty 500 Market Cap Indian Companies
- **Timeframe**: Daily (`1d`)
- **Core Indicators**:
  - `EMA = 50`
  - `Supertrend: Period = 10, Multiplier = 3`
- **Signal Logic**:
  - **BUY**: Daily Close > 50 EMA AND Supertrend == Bullish (Green)
  - **SELL**: Daily Close < 50 EMA AND Supertrend == Bearish (Red)
- **Scan Lookback**: Last 7 Trading Days
- **Entry Suitability Classification**:
  - **Actionable (Option to Perform Entry)**: Triggered within 0–3 sessions, price within $\le 2.5\%$ buffer, stop-loss risk $\le 5.0\%$, favorable 1:1.5 and 1:2.5 Risk-to-Reward ratio.
  - **Not Suitable (Avoid / Do Not Chase)**: Overextended (> 4% from trigger), Invalidated (broken back below 50 EMA), or Risk Too Wide (> 6%).

---

### 2. Intraday Momentum Strategy (15-Minute Timeframe)
- **Universe**: Nifty 500 Market Cap Indian Companies
- **Timeframe**: 15-Minute (`15m` candles, 25 bars per trading day)
- **Core Indicators**:
  - `EMA = 200` (Intraday Trend Anchor)
  - `Supertrend: Period = 10, Multiplier = 3`
- **Signal Logic**:
  - **INTRADAY BUY**: 15m Close > 200 EMA AND Supertrend == Bullish (Green)
  - **INTRADAY SHORT**: 15m Close < 200 EMA AND Supertrend == Bearish (Red)
- **Scan Lookback**: Live / Recent Intraday Session Bars (last 25 bars)
- **Intraday Suitability Classification**:
  - **Actionable Intraday Entry**: Fresh trigger (1–4 bars ago), tight pullback to 200 EMA / Supertrend support, stop-loss $\le 1.8\%$, Target 1 (1:1.5) and Target 2 (1:2.5).
  - **Not Suitable Intraday**: Overextended (> 2.0% intraday surge), Invalidated (crossed back through 200 EMA), or Risk Too Wide (> 2.8%).

---

### 🌟 Enhanced Pro Algo Option (Both Modes)
- **Volume Expansion Filter**: Trigger volume $> 1.05\times$ (Daily) or $> 1.2\times$ (Intraday) 20-period Volume SMA.
- **RSI Momentum Corridor**: RSI between 42 and 68 (prevents buying at overbought exhaustion while ensuring momentum).
- **Macro 200 EMA Golden Trend Filter**: Ensures secular market direction alignment.

---

## 🖥️ Web Dashboard Features (`http://localhost:5000`)
- **Primary Mode Switcher**: Seamlessly toggle between **Daily Swing** and **Intraday** sections with one click.
- **KPI Metrics**: Dynamic counts for Actionable Entries, Overextended/Avoid, and Pro Picks.
- **Interactive Candlestick Charts**:
  - Daily mode displays Daily candles with 50 EMA (cyan), 200 EMA (purple), and Supertrend bands.
  - Intraday mode displays 15m candles with 200 EMA (cyan) and Supertrend bands.
  - Pre-drawn Stop-Loss and Target lines on every stock!
- **Position Sizing Calculator**: Calculates recommended shares and total investment based on your capital and risk budget (default 1.0% for Swing, 0.5% for Intraday).
- **1-Click CSV Export**: Download signals for Zerodha, Groww, Angel One, or Excel journals.

---

## 🚀 How to Run

### Web Terminal Dashboard
Double click [`start_dashboard.bat`](file:///c:/Users/Mohammed%20Ali/Youtube/start_dashboard.bat) or run:
```powershell
python server.py
```
Open **`http://localhost:5000`** in your browser.

### Terminal CLI Scanner
```powershell
# Daily Swing Scan (Actionable Only)
python algo_scanner_cli.py --mode daily --actionable

# Intraday 15m Momentum Scan (Actionable Only)
python algo_scanner_cli.py --mode intraday --actionable

# Enhanced Pro Setups Only
python algo_scanner_cli.py --mode daily --enhanced
python algo_scanner_cli.py --mode intraday --enhanced
```

---

## 👨‍💻 Author & Maintainer

**Mohammed Sadakath Ali**
- **GitHub**: [@Aamiriapps](https://github.com/Aamiriapps) / [@mohammedsadakathali-hub](https://github.com/mohammedsadakathali-hub)
- **Project**: [AlgoQuant India](https://github.com/Aamiriapps/algoquant-india)
- **Focus**: Quantitative Finance, Algorithmic Trading Systems & Full-Stack Development

---

## ⚠️ Disclaimer

*AlgoQuant India is designed for algorithmic screening, educational, and research purposes. Market trading involves capital risk. Always practice sound risk management (e.g., maximum 1% risk per trade) and verify setups before executing live trades.*


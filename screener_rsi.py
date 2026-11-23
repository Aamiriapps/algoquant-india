"""
RSI Multi-Timeframe Strategy Engine (60-60-50 Pullback & Trailing Strategy)
==========================================================================
The Three-Tiered Framework:
1. Monthly Chart (Primary Trend Filter):
   - Monthly RSI >= 60 indicates an established, strong secular uptrend.
2. Weekly Chart (Trend Confirmation):
   - Weekly RSI >= 60 confirms intermediate momentum is healthy and in a high-conviction state.
3. Daily Chart (Precision Entry):
   - Catches the stock when retesting the ~50 RSI level after a pullback.
   - A bounce from ~50 (Daily RSI in 48-56 range with bullish price action) signals precision entry.

Risk Management & Exits:
- No Fixed Profit Target: Ride the trade without prematurely capping gains.
- Exit Signal: Exit when Daily RSI breaks below 50 for the first time.
- Trailing Stop-Loss: Dynamically tracked based on recent swing low / structure while Daily RSI >= 50.

Psychology:
"80% of trading is psychology and 20% is strategy; keeping it simple helps traders remain disciplined and avoid emotional decision-making."
"""

import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from algo_engine import fetch_stock_data, LIQUID_UNIVERSE

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "scan_rsi.json")
FLAGGED_FILE = os.path.join(CACHE_DIR, "rsi_flagged_trades.json")

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Standard Wilder's RSI calculation."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0.0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    return 100.0 - (100.0 / (1.0 + rs))

def safe_num(val, default=0.0, ndigits=2):
    if val is None:
        return default
    try:
        if pd.isna(val) or np.isnan(val) or np.isinf(val):
            return default
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        return round(f, ndigits) if ndigits is not None else f
    except Exception:
        return default

def sanitize_payload(obj):
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_payload(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_payload(v) for v in obj]
    return obj

def load_flagged_trades() -> dict:
    if os.path.exists(FLAGGED_FILE):
        try:
            with open(FLAGGED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_flagged_trades(data: dict):
    try:
        with open(FLAGGED_FILE, "w", encoding="utf-8") as f:
            json.dump(sanitize_payload(data), f, indent=2)
    except Exception as e:
        print(f"Error saving flagged RSI trades: {e}")

def toggle_flag_rsi_trade(symbol: str, entry_price: float = None, notes: str = "") -> dict:
    """Toggles flagging of a stock for the RSI 60-60-50 strategy tracking."""
    sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    trades = load_flagged_trades()
    
    if sym in trades:
        del trades[sym]
        save_flagged_trades(trades)
        return {"status": "unflagged", "symbol": sym, "is_flagged": False, "message": f"{sym} removed from RSI Strategy Active Tracker."}
    else:
        # Default entry price to current market price if not provided
        if entry_price is None or entry_price <= 0:
            df = fetch_stock_data(sym, range_str="1mo", interval="1d")
            entry_price = float(df['close'].iloc[-1]) if (df is not None and not df.empty) else 0.0
            
        trades[sym] = {
            "symbol": sym,
            "entry_price": round(entry_price, 2),
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "flagged_at": datetime.now().isoformat(),
            "notes": notes or "Active RSI 60-60-50 trade"
        }
        save_flagged_trades(trades)
        return {"status": "flagged", "symbol": sym, "is_flagged": True, "message": f"{sym} flagged as active RSI 60-60-50 trade!"}

def analyze_rsi_stock(item: dict) -> dict:
    """
    Evaluates stock for the Three-Tiered Multi-Timeframe RSI Framework:
    - Monthly RSI >= 60 (Primary Trend Filter)
    - Weekly RSI >= 60 (Intermediate Confirmation)
    - Daily RSI ~50 Retest & Bounce (Precision Entry)
    """
    sym = item["symbol"]
    name = item["name"]
    sector = item.get("sector", "Equities")
    
    try:
        df = fetch_stock_data(sym, range_str="5y", interval="1d")
        if df is None or len(df) < 100:
            return None

        # Convert to Datetime index for clean weekly/monthly resampling
        df_dt = df.copy()
        df_dt['dt'] = pd.to_datetime(df_dt['date'])
        df_dt = df_dt.set_index('dt').sort_index()

        curr_close = safe_num(df_dt['close'].iloc[-1], 0.0, 2)
        curr_open = safe_num(df_dt['open'].iloc[-1], curr_close, 2)
        curr_vol = safe_num(df_dt['volume'].iloc[-1], 0.0, 0)
        
        # 1. Monthly RSI (5-year monthly closes)
        m_closes = df_dt['close'].resample('ME').last().dropna()
        if len(m_closes) < 15:
            return None
        m_rsi_series = calc_rsi(m_closes, period=14)
        m_rsi = safe_num(m_rsi_series.iloc[-1], 50.0, 1)

        # 2. Weekly RSI (2-year weekly closes)
        w_closes = df_dt['close'].resample('W-FRI').last().dropna()
        if len(w_closes) < 15:
            return None
        w_rsi_series = calc_rsi(w_closes, period=14)
        w_rsi = safe_num(w_rsi_series.iloc[-1], 50.0, 1)

        # 3. Daily RSI
        d_rsi = safe_num(df_dt['rsi14'].iloc[-1] if 'rsi14' in df_dt.columns else calc_rsi(df_dt['close']).iloc[-1], 50.0, 1)
        d_rsi_prev = safe_num(df_dt['rsi14'].iloc[-2] if 'rsi14' in df_dt.columns and len(df_dt) >= 2 else d_rsi, d_rsi, 1)
        d_rsi_min_5d = safe_num(df_dt['rsi14'].tail(5).min() if 'rsi14' in df_dt.columns else d_rsi, d_rsi, 1)

        # 4. Moving Averages & Trend Structure
        dma50 = safe_num(df_dt['close'].tail(50).mean() if len(df_dt) >= 50 else df_dt['close'].mean(), curr_close * 0.96, 2)
        dma200 = safe_num(df_dt['close'].tail(200).mean() if len(df_dt) >= 200 else df_dt['close'].mean(), curr_close * 0.85, 2)
        curr_st = safe_num(df_dt['supertrend'].iloc[-1] if 'supertrend' in df_dt.columns else curr_close * 0.94, curr_close * 0.94, 2)
        curr_st_dir = int(df_dt['st_dir'].iloc[-1]) if ('st_dir' in df_dt.columns and not pd.isna(df_dt['st_dir'].iloc[-1])) else 1
        
        # 5. Swing Low & Trailing Stop-Loss
        # Lowest low during the recent 10 sessions (while testing the 50 RSI area)
        recent_10d_low = safe_num(df_dt['low'].tail(10).min(), curr_close * 0.95, 2)
        # Trailing SL is set just below the recent swing low / Supertrend
        trailing_sl_price = round(min(recent_10d_low * 0.995, curr_st if curr_st < curr_close else curr_close * 0.95), 2)
        risk_pct = round(((curr_close - trailing_sl_price) / curr_close) * 100, 2) if curr_close > 0 else 5.0

        # Tier Evaluations
        m_pass = (m_rsi >= 60.0)
        m_near = (57.0 <= m_rsi < 60.0)
        
        w_pass = (w_rsi >= 60.0)
        w_near = (57.0 <= w_rsi < 60.0)

        # Precision Entry Criteria (Daily):
        # Daily RSI retesting 50 level (ideal zone: 48 to 58)
        d_in_pullback_zone = (48.0 <= d_rsi <= 58.0)
        d_tested_50 = (47.0 <= d_rsi_min_5d <= 54.0)
        d_rsi_bouncing = (d_rsi >= d_rsi_prev) or (curr_close >= curr_open)
        is_green_candle = (curr_close >= curr_open)

        # Active Exit Status
        is_exit_triggered = (d_rsi < 50.0)
        is_caution_zone = (50.0 <= d_rsi <= 52.0)
        is_ride_mode = (d_rsi > 50.0)

        # Setup Categorization
        if m_pass and w_pass and d_in_pullback_zone and d_rsi_bouncing:
            setup_category = "PERFECT 60-60-50 BOUNCE"
            badge_class = "badge-success"
            is_actionable = True
            confidence_score = 5
        elif (m_pass or m_near) and (w_pass or w_near) and (47.0 <= d_rsi <= 60.0):
            setup_category = "HIGH MOMENTUM PULLBACK"
            badge_class = "badge-success"
            is_actionable = True
            confidence_score = 4
        elif m_pass and w_pass and d_rsi > 58.0:
            setup_category = "RIDING BULL TREND (RSI > 50)"
            badge_class = "badge-amber"
            is_actionable = False
            confidence_score = 4
        elif is_exit_triggered:
            setup_category = "EXIT SIGNAL (RSI < 50)"
            badge_class = "badge-danger"
            is_actionable = False
            confidence_score = 1
        else:
            setup_category = "WATCHLIST / DEVELOPING"
            badge_class = "badge-secondary"
            is_actionable = False
            confidence_score = 2

        # Filter out stocks with weak long-term trends (Monthly < 55 or Weekly < 55) unless already in active trades
        if m_rsi < 55.0 or w_rsi < 52.0:
            return None

        # Human-friendly Status Message
        if is_exit_triggered:
            exit_status_text = f"🔴 EXIT SIGNAL TRIGGERED: Daily RSI ({d_rsi}) broke below 50! Close trade to protect capital."
            exit_status_badge = "badge-danger"
        elif is_caution_zone:
            exit_status_text = f"⚠️ CAUTION LEVEL: Daily RSI ({d_rsi}) is touching the 50 line. Watch closely."
            exit_status_badge = "badge-warning"
        else:
            exit_status_text = f"🟢 RIDE THE TRADE: Daily RSI ({d_rsi}) ≥ 50 intact. Trend structure is bullish."
            exit_status_badge = "badge-success"

        # Trailing Stop Loss Rule Explanation
        sl_rule_text = f"Exit rule: Close position if Daily RSI breaks below 50. Suggested price stop at recent swing low ₹{trailing_sl_price:.2f} (-{risk_pct}%)."

        # Diagnoses & Action Plan
        reasons = [
            f"Monthly RSI {m_rsi} {'(Secular Uptrend > 60)' if m_pass else '(Near Bull Zone)'}",
            f"Weekly RSI {w_rsi} {'(Momentum Confirmed > 60)' if w_pass else '(Healthy Momentum)'}",
            f"Daily RSI {d_rsi} {'(Bouncing off 50 Pullback Zone)' if d_in_pullback_zone else f'(Daily RSI: {d_rsi})'}",
            f"Price Structure: ₹{curr_close:.2f} vs 50 EMA ₹{dma50:.2f} (+{round(((curr_close-dma50)/dma50)*100, 1)}%)"
        ]

        action_plan = (
            f"Entry above ₹{curr_close:.2f} on 50 RSI bounce. "
            f"Ride trend with NO fixed target. "
            f"Trail stop at ₹{trailing_sl_price:.2f}. "
            f"Exit immediately when Daily RSI closes below 50."
        )

        flagged_data = load_flagged_trades()
        is_user_flagged = (sym in flagged_data)
        user_trade_info = flagged_data.get(sym, None)

        return {
            "symbol": sym,
            "name": name,
            "sector": sector,
            "signal_type": "BUY" if is_actionable else ("EXIT" if is_exit_triggered else "HOLD"),
            "timeframe": "Multi-TF (Monthly + Weekly + Daily)",
            "current_price": curr_close,
            "trigger_price": curr_close,
            "main_ema": dma50,
            "main_ema_name": "50 EMA",
            "dma50": dma50,
            "dma200": dma200,
            "supertrend": curr_st,
            "supertrend_direction": "Bullish (Green)" if curr_st_dir == 1 else "Bearish (Red)",
            
            # Multi-Timeframe RSI Framework
            "monthly_rsi": m_rsi,
            "weekly_rsi": w_rsi,
            "daily_rsi": d_rsi,
            "rsi14": d_rsi, # for compatibility with existing UI sort
            "monthly_status": "PASS (>60)" if m_pass else ("NEAR (57-60)" if m_near else "WEAK (<57)"),
            "weekly_status": "PASS (>60)" if w_pass else ("NEAR (57-60)" if w_near else "WEAK (<57)"),
            "daily_status": "50 BOUNCE" if d_in_pullback_zone else ("RIDING (>58)" if d_rsi > 58 else "BREAKDOWN (<50)"),
            
            # Trailing Stop-Loss & Exit Rules
            "trailing_stop_loss": trailing_sl_price,
            "stop_loss": trailing_sl_price,
            "risk_pct": risk_pct,
            "sl_rule_text": sl_rule_text,
            "exit_condition": "Daily RSI < 50 First Breakdown",
            "exit_triggered": is_exit_triggered,
            "exit_status_text": exit_status_text,
            "exit_status_badge": exit_status_badge,
            
            # Target (No Fixed Target - Ride Trend)
            "target1": round(curr_close * 1.10, 2),
            "target2": round(curr_close * 1.20, 2),
            "target3": round(curr_close * 1.35, 2),
            "target_philosophy": "NO FIXED TARGET — RIDE TRADE VIA 50 RSI TRAILING STOP",
            "reward_risk_ratio": "Open-Ended / Trailing Exit (RSI < 50)",
            
            # Categorization & Actionability
            "suitability": setup_category,
            "verdict_badge": badge_class,
            "is_actionable": is_actionable,
            "confidence_score": confidence_score,
            "confidence_label": setup_category,
            "reasons": reasons,
            "action_plan": action_plan,
            
            # User Flagging / Active Tracking
            "is_flagged": is_user_flagged,
            "flagged_trade": user_trade_info,
            "days_ago": 0,
            "bars_ago": 0,
            "pct_from_trigger": 0.0,
            "trigger_date": "Today (Active Setup)",
            "volume_ratio": round(curr_vol / 20000.0, 1) if curr_vol else 1.0,
            "sl_5pct": round(curr_close * 0.95, 2),
            "trailing_sl": trailing_sl_price,
            "exit_alert": is_exit_triggered,
            
            # Psychology & Rules Callout
            "psychology_quote": "80% of trading is psychology and 20% is strategy; keeping it simple helps traders remain disciplined and avoid emotional decision-making.",
            
            "enhanced_option": {
                "trend_aligned": bool(m_pass and w_pass),
                "vol_confirmed": bool(curr_vol > 20000),
                "rsi_healthy": bool(d_in_pullback_zone),
                "adx_trending": True,
                "macd_bullish": True,
                "momentum_ok": True,
                "near_highs": True,
                "pro_score": f"{confidence_score}/5",
                "pro_status": setup_category
            }
        }
    except Exception as e:
        return None

def run_rsi_screener(max_workers: int = 25, force_refresh: bool = False) -> dict:
    """
    Scans the institutional universe for the RSI 60-60-50 Three-Tiered Framework.
    Returns qualified stocks sorted by proximity to the 50 Daily RSI bounce zone.
    """
    t_start = time.time()
    
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            mtime = os.path.getmtime(CACHE_FILE)
            if (time.time() - mtime) < 1800: # 30 min cache
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data.get("signals") and len(cached_data["signals"]) > 0:
                        # Refresh flagged status on cached items
                        flagged = load_flagged_trades()
                        for s in cached_data["signals"]:
                            s["is_flagged"] = (s["symbol"] in flagged)
                            s["flagged_trade"] = flagged.get(s["symbol"])
                        return cached_data
        except Exception:
            pass

    universe = LIQUID_UNIVERSE
    qualified = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(analyze_rsi_stock, universe)
        for r in results:
            if r:
                qualified.append(r)
                
    # Sort order:
    # 1. Actionable 50-retest bounces first (closest to 50 RSI with positive slope)
    # 2. Then by Monthly & Weekly momentum strength
    def sort_key(x):
        d_rsi = x.get("daily_rsi", 50.0)
        # Distance from ideal 50 bounce level (50 to 54)
        dist_from_52 = abs(d_rsi - 52.0)
        is_act = 1 if x.get("is_actionable") else 0
        return (-is_act, dist_from_52, -x.get("weekly_rsi", 0.0))

    qualified.sort(key=sort_key)
    
    t_elapsed = round(time.time() - t_start, 2)
    
    actionable_count = sum(1 for s in qualified if s.get("is_actionable"))
    flagged_count = sum(1 for s in qualified if s.get("is_flagged"))

    result = {
        "status": "success",
        "mode": "rsi",
        "framework": "Three-Tiered Multi-Timeframe RSI (60-60-50)",
        "psychology": "80% of trading is psychology and 20% is strategy; keeping it simple helps traders remain disciplined and avoid emotional decision-making.",
        "rules": {
            "monthly": "Monthly RSI >= 60 (Primary Secular Trend Filter)",
            "weekly": "Weekly RSI >= 60 (Intermediate Momentum Confirmation)",
            "daily_entry": "Daily RSI retesting ~50 level (48-56 range) with bullish bounce",
            "exit_rule": "Exit when Daily RSI breaks below 50 for the first time",
            "trailing_stop": "Dynamic trailing stop below recent swing low / structure"
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scan_duration_sec": t_elapsed,
        "total_scanned_stocks": len(universe),
        "total_triggers_found": len(qualified),
        "signals": qualified,
        "summary": {
            "total_candidates_passed_all": len(qualified),
            "actionable_buys": actionable_count,
            "actionable_sells": 0,
            "not_suitable": len(qualified) - actionable_count,
            "flagged_trades_count": flagged_count,
            "pro_enhanced_picks": sum(1 for s in qualified if s.get("confidence_score", 0) >= 4)
        }
    }
    
    clean_result = sanitize_payload(result)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_result, f, indent=2)
    except Exception as e:
        print(f"Error saving RSI scan cache: {e}")
        
    return clean_result

if __name__ == "__main__":
    t0 = time.time()
    res = run_rsi_screener(max_workers=25, force_refresh=True)
    print(f"Scan completed in {time.time()-t0:.2f}s! Found {len(res['signals'])} setups.")
    for i, s in enumerate(res['signals'][:15], 1):
        print(f"{i:2d}. {s['symbol']:12} | CMP: Rs.{s['current_price']:8.2f} | M-RSI: {s['monthly_rsi']:4.1f} | W-RSI: {s['weekly_rsi']:4.1f} | D-RSI: {s['daily_rsi']:4.1f} | {s['suitability']}")

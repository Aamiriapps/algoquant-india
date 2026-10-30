import os
import sys
import json
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
from algo_engine import LIQUID_UNIVERSE, fetch_stock_data, calculate_supertrend

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def track_intraday_stock(item: dict, days_back: int = 7) -> list:
    symbol = item["symbol"]
    name = item["name"]
    sector = item["sector"]
    
    df = fetch_stock_data(symbol, range_str="1mo", interval="15m")
    if df.empty or len(df) < 220:
        return []
        
    df["is_buy"] = (df["close"] > df["ema200"]) & (df["st_dir"] == 1)
    df["is_sell"] = (df["close"] < df["ema200"]) & (df["st_dir"] == -1)
    
    prev_buy = df["is_buy"].shift(1).fillna(False).astype(bool)
    prev_sell = df["is_sell"].shift(1).fillna(False).astype(bool)
    
    df["buy_trigger"] = df["is_buy"] & (~prev_buy)
    df["sell_trigger"] = df["is_sell"] & (~prev_sell)
    
    # Identify unique trading dates
    df["trading_day"] = df["date"].dt.date
    unique_days = df["trading_day"].unique()
    if len(unique_days) < days_back:
        target_days = set(unique_days)
    else:
        target_days = set(unique_days[-days_back:])
        
    results = []
    total_bars = len(df)
    
    for i in range(200, total_bars):
        t_day = df["trading_day"].iloc[i]
        if t_day not in target_days:
            continue
            
        b_trig = bool(df["buy_trigger"].iloc[i])
        s_trig = bool(df["sell_trigger"].iloc[i])
        
        if not (b_trig or s_trig):
            continue
            
        sig_type = "BUY" if b_trig else "SELL"
        entry_price = float(df["close"].iloc[i])
        trig_time = df["date"].iloc[i].strftime("%d-%b %H:%M")
        trig_day_str = df["date"].iloc[i].strftime("%Y-%m-%d")
        curr_st = float(df["supertrend"].iloc[i])
        curr_ema200 = float(df["ema200"].iloc[i])
        
        # Enhanced pro indicators
        trig_vol = float(df["volume"].iloc[i])
        trig_vol_ma = float(df["vol_sma20"].iloc[i]) if not pd.isna(df["vol_sma20"].iloc[i]) else trig_vol
        vol_ratio = trig_vol / (trig_vol_ma + 1e-9)
        trig_rsi = float(df["rsi14"].iloc[i])
        is_pro = (vol_ratio >= 1.2) and ((42.0 <= trig_rsi <= 68.0) if sig_type == "BUY" else (trig_rsi <= 58.0))
        
        if sig_type == "BUY":
            stop_loss = round(min(curr_st, curr_ema200), 2)
            risk = max(entry_price - stop_loss, 0.01)
            target1 = round(entry_price + 1.5 * risk, 2)
            target2 = round(entry_price + 2.5 * risk, 2)
        else:
            stop_loss = round(max(curr_st, curr_ema200), 2)
            risk = max(stop_loss - entry_price, 0.01)
            target1 = round(entry_price - 1.5 * risk, 2)
            target2 = round(entry_price - 2.5 * risk, 2)
            
        risk_pct = round((risk / entry_price) * 100.0, 2)
        
        # Forward track within same day (Intraday position must close before end of session)
        outcome = "OPEN"
        exit_price = entry_price
        exit_time = trig_time
        hit_t1 = False
        hit_t2 = False
        hit_sl = False
        
        # Look forward through same day bars
        j = i + 1
        last_bar_idx = i
        while j < total_bars and df["trading_day"].iloc[j] == t_day:
            bar_high = float(df["high"].iloc[j])
            bar_low = float(df["low"].iloc[j])
            bar_close = float(df["close"].iloc[j])
            bar_time = df["date"].iloc[j].strftime("%d-%b %H:%M")
            last_bar_idx = j
            
            if sig_type == "BUY":
                # Check Stop Loss first (conservative evaluation)
                if bar_low <= stop_loss:
                    hit_sl = True
                    exit_price = stop_loss
                    exit_time = bar_time
                    break
                if bar_high >= target2:
                    hit_t2 = True
                    hit_t1 = True
                    exit_price = target2
                    exit_time = bar_time
                    break
                elif bar_high >= target1:
                    hit_t1 = True
            else: # SELL
                if bar_high >= stop_loss:
                    hit_sl = True
                    exit_price = stop_loss
                    exit_time = bar_time
                    break
                if bar_low <= target2:
                    hit_t2 = True
                    hit_t1 = True
                    exit_price = target2
                    exit_time = bar_time
                    break
                elif bar_low <= target1:
                    hit_t1 = True
            j += 1
            
        if hit_sl:
            outcome = "STOP LOSS HIT"
            pnl_pct = -risk_pct
            r_multiple = -1.0
            profit = False
        elif hit_t2:
            outcome = "TARGET 2 HIT"
            pnl_pct = round(risk_pct * 2.5, 2)
            r_multiple = 2.5
            profit = True
        elif hit_t1:
            outcome = "TARGET 1 HIT"
            pnl_pct = round(risk_pct * 1.5, 2)
            r_multiple = 1.5
            profit = True
        else:
            # End of session close
            if last_bar_idx > i:
                exit_price = float(df["close"].iloc[last_bar_idx])
                exit_time = df["date"].iloc[last_bar_idx].strftime("%d-%b %H:%M")
                if sig_type == "BUY":
                    pnl_pct = round(((exit_price - entry_price) / entry_price) * 100.0, 2)
                    r_multiple = round((exit_price - entry_price) / risk, 2)
                else:
                    pnl_pct = round(((entry_price - exit_price) / entry_price) * 100.0, 2)
                    r_multiple = round((entry_price - exit_price) / risk, 2)
                outcome = "EOD PROFIT" if pnl_pct > 0 else "EOD LOSS"
                profit = pnl_pct > 0
            else:
                outcome = "ACTIVE (TRIGGER BAR)"
                pnl_pct = 0.0
                r_multiple = 0.0
                profit = False
                
        results.append({
            "mode": "intraday",
            "symbol": symbol,
            "name": name,
            "sector": sector,
            "date": trig_day_str,
            "trigger_time": trig_time,
            "signal": sig_type,
            "entry": round(entry_price, 2),
            "stop_loss": stop_loss,
            "target1": target1,
            "target2": target2,
            "risk_pct": risk_pct,
            "exit_price": round(exit_price, 2),
            "exit_time": exit_time,
            "outcome": outcome,
            "profit": profit,
            "pnl_pct": pnl_pct,
            "r_multiple": r_multiple,
            "is_pro": is_pro
        })
        
    return results

def track_swing_stock(item: dict, months_back: int = 3) -> list:
    symbol = item["symbol"]
    name = item["name"]
    sector = item["sector"]
    
    df = fetch_stock_data(symbol, range_str="1y", interval="1d")
    if df.empty or len(df) < 65:
        return []
        
    df["is_buy"] = (df["close"] > df["ema50"]) & (df["st_dir"] == 1)
    df["is_sell"] = (df["close"] < df["ema50"]) & (df["st_dir"] == -1)
    
    prev_buy = df["is_buy"].shift(1).fillna(False).astype(bool)
    prev_sell = df["is_sell"].shift(1).fillna(False).astype(bool)
    
    df["buy_trigger"] = df["is_buy"] & (~prev_buy)
    df["sell_trigger"] = df["is_sell"] & (~prev_sell)
    
    # 3 months lookback = approx 65 trading days
    days_back = months_back * 22
    total_bars = len(df)
    start_idx = max(50, total_bars - days_back)
    
    results = []
    
    for i in range(start_idx, total_bars):
        b_trig = bool(df["buy_trigger"].iloc[i])
        s_trig = bool(df["sell_trigger"].iloc[i])
        
        if not (b_trig or s_trig):
            continue
            
        sig_type = "BUY" if b_trig else "SELL"
        entry_price = float(df["close"].iloc[i])
        trig_date = df["date"].iloc[i].strftime("%d-%b-%Y")
        curr_st = float(df["supertrend"].iloc[i])
        curr_ema50 = float(df["ema50"].iloc[i])
        curr_ema200 = float(df["ema200"].iloc[i])
        curr_atr = float(df["atr"].iloc[i])
        
        # Enhanced pro filters
        trig_vol = float(df["volume"].iloc[i])
        trig_vol_ma = float(df["vol_sma20"].iloc[i]) if not pd.isna(df["vol_sma20"].iloc[i]) else trig_vol
        vol_ratio = trig_vol / (trig_vol_ma + 1e-9)
        trig_rsi = float(df["rsi14"].iloc[i])
        trend_aligned = (entry_price > curr_ema200) if sig_type == "BUY" else (entry_price < curr_ema200)
        is_pro = trend_aligned and (vol_ratio >= 1.05) and ((45.0 <= trig_rsi <= 68.0) if sig_type == "BUY" else (trig_rsi <= 55.0))
        
        if sig_type == "BUY":
            stop_loss = round(min(curr_st, curr_ema50 - 0.5 * curr_atr), 2)
            risk = max(entry_price - stop_loss, 0.01)
            target1 = round(entry_price + 1.5 * risk, 2)
            target2 = round(entry_price + 2.5 * risk, 2)
        else:
            stop_loss = round(max(curr_st, curr_ema50 + 0.5 * curr_atr), 2)
            risk = max(stop_loss - entry_price, 0.01)
            target1 = round(entry_price - 1.5 * risk, 2)
            target2 = round(entry_price - 2.5 * risk, 2)
            
        risk_pct = round((risk / entry_price) * 100.0, 2)
        
        # Forward track up to today
        outcome = "IN PROGRESS"
        exit_price = entry_price
        exit_date = trig_date
        hit_t1 = False
        hit_t2 = False
        hit_sl = False
        invalidated = False
        
        j = i + 1
        last_idx = i
        while j < total_bars:
            bar_high = float(df["high"].iloc[j])
            bar_low = float(df["low"].iloc[j])
            bar_close = float(df["close"].iloc[j])
            bar_date = df["date"].iloc[j].strftime("%d-%b-%Y")
            bar_st_dir = int(df["st_dir"].iloc[j])
            bar_ema50 = float(df["ema50"].iloc[j])
            last_idx = j
            
            if sig_type == "BUY":
                if bar_low <= stop_loss:
                    hit_sl = True
                    exit_price = stop_loss
                    exit_date = bar_date
                    break
                if bar_high >= target2:
                    hit_t2 = True
                    hit_t1 = True
                    exit_price = target2
                    exit_date = bar_date
                    break
                elif bar_high >= target1:
                    hit_t1 = True
                    
                # Signal Invalidation (Trend reversal before target)
                if bar_close < bar_ema50 or bar_st_dir == -1:
                    invalidated = True
                    exit_price = bar_close
                    exit_date = bar_date
                    break
            else: # SELL
                if bar_high >= stop_loss:
                    hit_sl = True
                    exit_price = stop_loss
                    exit_date = bar_date
                    break
                if bar_low <= target2:
                    hit_t2 = True
                    hit_t1 = True
                    exit_price = target2
                    exit_date = bar_date
                    break
                elif bar_low <= target1:
                    hit_t1 = True
                    
                if bar_close > bar_ema50 or bar_st_dir == 1:
                    invalidated = True
                    exit_price = bar_close
                    exit_date = bar_date
                    break
            j += 1
            
        if hit_sl:
            outcome = "STOP LOSS HIT"
            pnl_pct = -risk_pct
            r_multiple = -1.0
            profit = False
        elif hit_t2:
            outcome = "TARGET 2 HIT"
            pnl_pct = round(risk_pct * 2.5, 2)
            r_multiple = 2.5
            profit = True
        elif hit_t1:
            outcome = "TARGET 1 HIT"
            pnl_pct = round(risk_pct * 1.5, 2)
            r_multiple = 1.5
            profit = True
        elif invalidated:
            if sig_type == "BUY":
                pnl_pct = round(((exit_price - entry_price) / entry_price) * 100.0, 2)
                r_multiple = round((exit_price - entry_price) / risk, 2)
            else:
                pnl_pct = round(((entry_price - exit_price) / entry_price) * 100.0, 2)
                r_multiple = round((entry_price - exit_price) / risk, 2)
            outcome = "TREND EXIT (PROFIT)" if pnl_pct > 0 else "TREND EXIT (LOSS)"
            profit = pnl_pct > 0
        else:
            # Trade is still active/open today
            cmp = float(df["close"].iloc[-1])
            exit_price = cmp
            exit_date = "STILL OPEN (CMP)"
            if sig_type == "BUY":
                pnl_pct = round(((cmp - entry_price) / entry_price) * 100.0, 2)
                r_multiple = round((cmp - entry_price) / risk, 2)
            else:
                pnl_pct = round(((entry_price - cmp) / entry_price) * 100.0, 2)
                r_multiple = round((entry_price - cmp) / risk, 2)
            outcome = "OPEN (PROFIT)" if pnl_pct > 0 else "OPEN (LOSS)"
            profit = pnl_pct > 0
            
        results.append({
            "mode": "swing",
            "symbol": symbol,
            "name": name,
            "sector": sector,
            "trigger_date": trig_date,
            "signal": sig_type,
            "entry": round(entry_price, 2),
            "stop_loss": stop_loss,
            "target1": target1,
            "target2": target2,
            "risk_pct": risk_pct,
            "exit_price": round(exit_price, 2),
            "exit_date": exit_date,
            "outcome": outcome,
            "profit": profit,
            "pnl_pct": pnl_pct,
            "r_multiple": r_multiple,
            "is_pro": is_pro
        })
        
    return results

def run_tracker():
    print("=" * 70)
    print("AlgoQuant Systematic Historical Tracker")
    print("1. Intraday (Last 7 Trading Days) - 15m 200 EMA + Supertrend")
    print("2. Swing (Last 3 Months) - Daily 50 EMA + Supertrend")
    print("=" * 70)
    
    t0 = time.time()
    
    # Run Intraday
    print("Scanning Intraday last 7 days across Top 140 liquid stocks...")
    intraday_trades = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(track_intraday_stock, item, 7) for item in LIQUID_UNIVERSE]
        for f in futures:
            try:
                res = f.result()
                if res:
                    intraday_trades.extend(res)
            except Exception as e:
                pass
                
    print(f"Intraday scan completed in {time.time()-t0:.1f}s. Total trade setups: {len(intraday_trades)}")
    
    t1 = time.time()
    # Run Swing
    print("Scanning Swing last 3 months across Top 140 liquid stocks...")
    swing_trades = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(track_swing_stock, item, 3) for item in LIQUID_UNIVERSE]
        for f in futures:
            try:
                res = f.result()
                if res:
                    swing_trades.extend(res)
            except Exception as e:
                pass
                
    print(f"Swing scan completed in {time.time()-t1:.1f}s. Total trade setups: {len(swing_trades)}")
    
    # Save results to disk
    os.makedirs("cache", exist_ok=True)
    with open("cache/tracker_intraday_7d.json", "w", encoding="utf-8") as f:
        json.dump(intraday_trades, f, indent=2)
    with open("cache/tracker_swing_3m.json", "w", encoding="utf-8") as f:
        json.dump(swing_trades, f, indent=2)
        
    # Generate Stats
    def compute_stats(trades, name):
        total = len(trades)
        if total == 0:
            return {"name": name, "total": 0}
        wins = [t for t in trades if t["profit"]]
        losses = [t for t in trades if not t["profit"]]
        win_rate = round((len(wins) / total) * 100, 2)
        
        # Pro stats
        pro_trades = [t for t in trades if t["is_pro"]]
        pro_wins = [t for t in pro_trades if t["profit"]]
        pro_win_rate = round((len(pro_wins) / len(pro_trades)) * 100, 2) if pro_trades else 0
        
        # Targets hit
        t1_hits = sum(1 for t in trades if "TARGET 1" in t["outcome"] or "TARGET 2" in t["outcome"])
        t2_hits = sum(1 for t in trades if "TARGET 2" in t["outcome"])
        sl_hits = sum(1 for t in trades if "STOP LOSS" in t["outcome"])
        
        total_r = round(sum(t["r_multiple"] for t in trades), 2)
        avg_r = round(total_r / total, 2)
        
        # Profit factor
        gross_profit = sum(t["pnl_pct"] for t in wins)
        gross_loss = abs(sum(t["pnl_pct"] for t in losses))
        profit_factor = round(gross_profit / (gross_loss + 1e-9), 2)
        
        # Best and worst
        sorted_by_pnl = sorted(trades, key=lambda x: x["pnl_pct"], reverse=True)
        best_stocks = sorted_by_pnl[:5]
        worst_stocks = sorted_by_pnl[-5:]
        
        stats = {
            "name": name,
            "total_trades": total,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": win_rate,
            "pro_trades": len(pro_trades),
            "pro_win_rate_pct": pro_win_rate,
            "target1_hits": t1_hits,
            "target2_hits": t2_hits,
            "stop_loss_hits": sl_hits,
            "total_r_return": total_r,
            "avg_r_per_trade": avg_r,
            "profit_factor": profit_factor,
            "gross_profit_pct": round(gross_profit, 2),
            "gross_loss_pct": round(gross_loss, 2),
            "best_performers": best_stocks,
            "worst_performers": worst_stocks
        }
        return stats
        
    intra_stats = compute_stats(intraday_trades, "Intraday (Last 7 Days)")
    swing_stats = compute_stats(swing_trades, "Swing (Last 3 Months)")
    
    with open("cache/tracker_summary.json", "w", encoding="utf-8") as f:
        json.dump({"intraday": intra_stats, "swing": swing_stats}, f, indent=2)
        
    print("\n--- INTRADAY STATS (Last 7 Days) ---")
    print(f"Total Triggers: {intra_stats['total_trades']}")
    print(f"Wins: {intra_stats['wins']} | Losses: {intra_stats['losses']}")
    print(f"Overall Win Rate: {intra_stats['win_rate_pct']}%")
    print(f"Pro Setups Win Rate: {intra_stats['pro_win_rate_pct']}% ({intra_stats['pro_trades']} pro setups)")
    print(f"Target 1 Hits: {intra_stats['target1_hits']} | Target 2 Hits: {intra_stats['target2_hits']} | Stop Loss Hits: {intra_stats['stop_loss_hits']}")
    print(f"Profit Factor: {intra_stats['profit_factor']} | Net R: {intra_stats['total_r_return']}R")
    
    print("\n--- SWING STATS (Last 3 Months) ---")
    print(f"Total Triggers: {swing_stats['total_trades']}")
    print(f"Wins: {swing_stats['wins']} | Losses: {swing_stats['losses']}")
    print(f"Overall Win Rate: {swing_stats['win_rate_pct']}%")
    print(f"Pro Setups Win Rate: {swing_stats['pro_win_rate_pct']}% ({swing_stats['pro_trades']} pro setups)")
    print(f"Target 1 Hits: {swing_stats['target1_hits']} | Target 2 Hits: {swing_stats['target2_hits']} | Stop Loss Hits: {swing_stats['stop_loss_hits']}")
    print(f"Profit Factor: {swing_stats['profit_factor']} | Net R: {swing_stats['total_r_return']}R")

if __name__ == "__main__":
    run_tracker()

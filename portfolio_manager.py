import os
import json
import uuid
import time
import threading
import tempfile
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from algo_engine import fetch_stock_data, LIQUID_UNIVERSE
try:
    from dynamic_universe import get_active_universe
except ImportError:
    get_active_universe = lambda: LIQUID_UNIVERSE

PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "portfolio.json")
PORTFOLIO_LOCK = threading.Lock()
PORTFOLIO_CACHE = {}  # maps portfolio_id -> {"data": result_dict, "timestamp": float}

def invalidate_portfolio_cache(portfolio_id: str = None):
    """Invalidates the in-memory portfolio analysis cache on position changes."""
    global PORTFOLIO_CACHE
    if portfolio_id and portfolio_id in PORTFOLIO_CACHE:
        PORTFOLIO_CACHE.pop(portfolio_id, None)
    else:
        PORTFOLIO_CACHE.clear()

def get_symbol_metadata(symbol: str) -> dict:
    """Finds name and sector from active dynamic universe or provides clean defaults."""
    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    active_u = get_active_universe() or LIQUID_UNIVERSE
    for item in active_u:
        if item["symbol"].upper() == clean_sym:
            return {"symbol": clean_sym, "name": item["name"], "sector": item["sector"]}
    for item in LIQUID_UNIVERSE:
        if item["symbol"].upper() == clean_sym:
            return {"symbol": clean_sym, "name": item["name"], "sector": item["sector"]}
    return {
        "symbol": clean_sym,
        "name": f"{clean_sym} (NSE)",
        "sector": "Indian Equities"
    }

def load_portfolio_data() -> dict:
    """
    Loads all portfolios from disk.
    Automatically migrates legacy single-portfolio format to multi-portfolio format
    preserving 100% of holdings, watchlist items, and historical trades without data loss.
    """
    data = None
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading portfolio data: {e}")

    today_str = datetime.now().strftime("%Y-%m-%d")

    # If completely empty or invalid, generate default initial portfolio
    if not data or not isinstance(data, dict):
        seed_portfolio = {
            "id": "default",
            "name": "Main Swing Portfolio",
            "created_at": datetime.now().isoformat(),
            "holdings": [
                {
                    "id": str(uuid.uuid4())[:8],
                    "symbol": "TATASTEEL",
                    "name": "Tata Steel Ltd",
                    "sector": "Metals & Mining",
                    "buy_price": 142.50,
                    "quantity": 250,
                    "buy_date": today_str,
                    "initial_sl": 136.00,
                    "target1": 152.00,
                    "target2": 162.00,
                    "notes": "50 EMA bounce with high institutional volume",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": str(uuid.uuid4())[:8],
                    "symbol": "BEL",
                    "name": "Bharat Electronics Ltd",
                    "buy_price": 285.00,
                    "quantity": 120,
                    "buy_date": today_str,
                    "initial_sl": 272.00,
                    "target1": 305.00,
                    "target2": 325.00,
                    "notes": "Defence momentum breakout above resistance",
                    "created_at": datetime.now().isoformat()
                }
            ],
            "watchlist": [
                {
                    "id": str(uuid.uuid4())[:8],
                    "symbol": "INFY",
                    "name": "Infosys Ltd",
                    "sector": "Information Technology",
                    "target_entry_price": 1160.00,
                    "notes": "Watching for daily close above 50 EMA and Supertrend green",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": str(uuid.uuid4())[:8],
                    "symbol": "RELIANCE",
                    "name": "Reliance Industries Ltd",
                    "sector": "Energy / Conglomerate",
                    "target_entry_price": 1250.00,
                    "notes": "Consolidation base near 50 EMA support",
                    "created_at": datetime.now().isoformat()
                }
            ],
            "history": [
                {
                    "id": str(uuid.uuid4())[:8],
                    "symbol": "HINDALCO",
                    "name": "Hindalco Industries Ltd",
                    "buy_price": 620.00,
                    "exit_price": 682.00,
                    "quantity": 50,
                    "buy_date": "2026-09-15",
                    "exit_date": "2026-10-05",
                    "hold_days": 20,
                    "realized_pnl": 3100.00,
                    "return_pct": 10.0,
                    "exit_reason": "Target 1 reached, trailed stop loss triggered at 682",
                    "is_win": True,
                    "notes": "Clean metal sector trend continuation"
                }
            ],
            "settings": {
                "total_capital": 500000.0,
                "max_risk_per_trade_pct": 1.0,
                "last_updated": datetime.now().isoformat()
            }
        }
        data = {
            "active_portfolio_id": "default",
            "portfolios": [seed_portfolio]
        }
        save_portfolio_data(data)
        return data

    # Auto-migrate legacy single-portfolio format to multi-portfolio format
    if "portfolios" not in data or not isinstance(data.get("portfolios"), list):
        legacy_holdings = data.get("holdings", [])
        legacy_watchlist = data.get("watchlist", [])
        legacy_history = data.get("history", [])
        legacy_settings = data.get("settings", {"total_capital": 500000.0, "max_risk_per_trade_pct": 1.0})

        default_portfolio = {
            "id": "default",
            "name": "Main Swing Portfolio",
            "created_at": datetime.now().isoformat(),
            "holdings": legacy_holdings,
            "watchlist": legacy_watchlist,
            "history": legacy_history,
            "settings": legacy_settings
        }
        data = {
            "active_portfolio_id": "default",
            "portfolios": [default_portfolio]
        }
        save_portfolio_data(data)
        return data

    # Ensure active portfolio exists and is valid
    if not data["portfolios"]:
        default_portfolio = {
            "id": "default",
            "name": "Main Swing Portfolio",
            "created_at": datetime.now().isoformat(),
            "holdings": [],
            "watchlist": [],
            "history": [],
            "settings": {"total_capital": 500000.0, "max_risk_per_trade_pct": 1.0}
        }
        data["portfolios"].append(default_portfolio)
        data["active_portfolio_id"] = "default"
        save_portfolio_data(data)

    existing_ids = [p["id"] for p in data["portfolios"]]
    if data.get("active_portfolio_id") not in existing_ids:
        data["active_portfolio_id"] = data["portfolios"][0]["id"]

    return data

def save_portfolio_data(data: dict):
    """Saves portfolio to disk safely using atomic write and thread lock."""
    with PORTFOLIO_LOCK:
        try:
            cache_dir = os.path.dirname(PORTFOLIO_FILE)
            os.makedirs(cache_dir, exist_ok=True)
            if "settings" in data:
                data["settings"]["last_updated"] = datetime.now().isoformat()
            with tempfile.NamedTemporaryFile("w", dir=cache_dir, delete=False, encoding="utf-8") as tf:
                json.dump(data, tf, indent=2)
                temp_name = tf.name
            os.replace(temp_name, PORTFOLIO_FILE)
            invalidate_portfolio_cache()
        except Exception as e:
            print(f"Error saving portfolio data: {e}")

def get_portfolio_by_id(data: dict, portfolio_id: str = None) -> tuple[dict, int]:
    """
    Returns (portfolio_dict, index).
    If portfolio_id is None or empty, returns the currently active portfolio.
    """
    portfolios = data.get("portfolios", [])
    if not portfolios:
        data = load_portfolio_data()
        portfolios = data.get("portfolios", [])

    target_id = portfolio_id or data.get("active_portfolio_id")
    for idx, p in enumerate(portfolios):
        if p["id"] == target_id:
            return p, idx

    # Fallback to the first portfolio if requested ID not found
    return portfolios[0], 0

def get_all_portfolios_meta() -> dict:
    """Returns summary metadata of all user portfolios and the active portfolio ID."""
    data = load_portfolio_data()
    active_id = data.get("active_portfolio_id", "default")
    return {
        "active_portfolio_id": active_id,
        "portfolios": [
            {
                "id": p["id"],
                "name": p["name"],
                "created_at": p.get("created_at"),
                "holdings_count": len(p.get("holdings", [])),
                "watchlist_count": len(p.get("watchlist", [])),
                "history_count": len(p.get("history", [])),
                "total_capital": p.get("settings", {}).get("total_capital", 500000.0),
                "max_risk_per_trade_pct": p.get("settings", {}).get("max_risk_per_trade_pct", 1.0),
                "is_active": p["id"] == active_id
            }
            for p in data.get("portfolios", [])
        ]
    }

def create_new_portfolio(name: str, total_capital: float = 500000.0, max_risk_pct: float = 1.0) -> dict:
    """Creates a new user-named portfolio and sets it as active."""
    data = load_portfolio_data()
    clean_name = (name or "").strip()
    if not clean_name:
        clean_name = f"Portfolio {len(data.get('portfolios', [])) + 1}"

    # Check for duplicate name
    for p in data.get("portfolios", []):
        if p["name"].lower() == clean_name.lower():
            return {"error": f"A portfolio named '{clean_name}' already exists. Please choose a unique name."}

    new_id = "p_" + str(uuid.uuid4())[:8]
    new_p = {
        "id": new_id,
        "name": clean_name,
        "created_at": datetime.now().isoformat(),
        "holdings": [],
        "watchlist": [],
        "history": [],
        "settings": {
            "total_capital": float(total_capital) if total_capital and float(total_capital) > 0 else 500000.0,
            "max_risk_per_trade_pct": float(max_risk_pct) if max_risk_pct and float(max_risk_pct) > 0 else 1.0,
            "last_updated": datetime.now().isoformat()
        }
    }
    data["portfolios"].append(new_p)
    data["active_portfolio_id"] = new_id
    save_portfolio_data(data)
    invalidate_portfolio_cache()
    return {"success": True, "message": f"Portfolio '{clean_name}' created successfully!", "portfolio": new_p}

def update_portfolio_meta(portfolio_id: str, name: str = None, total_capital: float = None, max_risk_pct: float = None) -> dict:
    """Updates name or settings of a specific portfolio."""
    data = load_portfolio_data()
    target_p, idx = get_portfolio_by_id(data, portfolio_id)
    if not target_p:
        return {"error": f"Portfolio {portfolio_id} not found."}

    if name and name.strip():
        clean_name = name.strip()
        for p in data.get("portfolios", []):
            if p["id"] != target_p["id"] and p["name"].lower() == clean_name.lower():
                return {"error": f"Another portfolio named '{clean_name}' already exists."}
        target_p["name"] = clean_name

    if total_capital is not None and float(total_capital) > 0:
        target_p["settings"]["total_capital"] = float(total_capital)

    if max_risk_pct is not None and float(max_risk_pct) > 0:
        target_p["settings"]["max_risk_per_trade_pct"] = float(max_risk_pct)

    target_p["settings"]["last_updated"] = datetime.now().isoformat()
    save_portfolio_data(data)
    invalidate_portfolio_cache(target_p["id"])
    return {"success": True, "message": f"Portfolio '{target_p['name']}' updated successfully!", "portfolio": target_p}

def delete_user_portfolio(portfolio_id: str) -> dict:
    """Deletes a portfolio (prevents deleting the last remaining portfolio)."""
    data = load_portfolio_data()
    portfolios = data.get("portfolios", [])
    if len(portfolios) <= 1:
        return {"error": "Cannot delete the only portfolio. You must have at least one active portfolio."}

    target_p, idx = get_portfolio_by_id(data, portfolio_id)
    if not target_p:
        return {"error": f"Portfolio {portfolio_id} not found."}

    deleted_name = target_p["name"]
    data["portfolios"] = [p for p in portfolios if p["id"] != target_p["id"]]

    # If deleted portfolio was active, switch active to the first remaining portfolio
    if data.get("active_portfolio_id") == target_p["id"]:
        data["active_portfolio_id"] = data["portfolios"][0]["id"]

    save_portfolio_data(data)
    invalidate_portfolio_cache()
    return {
        "success": True,
        "message": f"Portfolio '{deleted_name}' deleted.",
        "active_portfolio_id": data["active_portfolio_id"]
    }

def switch_active_portfolio(portfolio_id: str) -> dict:
    """Switches the active portfolio."""
    data = load_portfolio_data()
    target_p, idx = get_portfolio_by_id(data, portfolio_id)
    if not target_p:
        return {"error": f"Portfolio {portfolio_id} not found."}

    data["active_portfolio_id"] = target_p["id"]
    save_portfolio_data(data)
    return {"success": True, "active_portfolio_id": target_p["id"], "name": target_p["name"]}

def analyze_single_stock(symbol: str, is_bought: bool = False, buy_price: float = None, 
                         quantity: int = 0, buy_date: str = None, initial_sl: float = None, 
                         target1: float = None, target2: float = None,
                         target3: float = None, target4: float = None) -> dict:
    """
    Performs comprehensive pro swing algorithmic analysis:
    - If is_bought=True: Exit / Trailing SL / Target status / PnL.
    - If is_bought=False: Buy Entry / Safe Buy Zone / Initial SL / Targets / Position sizing.
    """
    clean_sym = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    ALIAS_MAP = {
        "LTIM": "LTM",
        "LTIMINDTREE": "LTM",
        "HDFC": "HDFCBANK",
        "HUL": "HINDUNILVR",
        "BOB": "BANKBARODA",
        "ICICILOMBARD": "ICICIGI",
        "SBICARDS": "SBICARD",
        "BAJAJ-AUTO": "BAJAJ-AUTO",
        "BAJAJAUTO": "BAJAJ-AUTO",
        "TATAMOTORS": "TATAMOTORS",
        "TATAMOTOR": "TATAMOTORS",
        "M&M": "M&M",
        "MM": "M&M",
        "BAJAJFINANCE": "BAJFINANCE",
        "BAJAJFINSERV": "BAJAJFINSV",
        "NESTLE": "NESTLEIND",
        "L&T": "LT",
        "LARSEN": "LT",
        "MCDOWELL": "MCDOWELL-N",
        "UNITEDSPIRITS": "MCDOWELL-N"
    }
    fetch_sym = ALIAS_MAP.get(clean_sym, clean_sym)
    meta = get_symbol_metadata(clean_sym)
    
    df = fetch_stock_data(fetch_sym, range_str="1y", interval="1d")
    if df.empty or len(df) < 10:
        return {
            "symbol": clean_sym,
            "name": meta["name"],
            "sector": meta["sector"],
            "error": "Insufficient market data from exchange. Please verify ticker symbol.",
            "is_bought": is_bought
        }
        
    curr_close = float(df["close"].iloc[-1])
    prev_close = float(df["close"].iloc[-2]) if len(df) >= 2 else curr_close
    day_change_pct = round(((curr_close - prev_close) / prev_close) * 100.0, 2)
    
    curr_ema50 = float(df["ema50"].iloc[-1])
    curr_ema200 = float(df["ema200"].iloc[-1])
    curr_st = float(df["supertrend"].iloc[-1])
    curr_st_dir = int(df["st_dir"].iloc[-1]) # 1: Bullish Green, -1: Bearish Red
    curr_rsi = float(df["rsi14"].iloc[-1])
    curr_atr = float(df["atr"].iloc[-1])
    
    curr_vol = float(df["volume"].iloc[-1])
    curr_vol_ma = float(df["vol_sma20"].iloc[-1]) if not pd.isna(df["vol_sma20"].iloc[-1]) else curr_vol
    vol_ratio = round(curr_vol / (curr_vol_ma + 1e-9), 2)
    
    dist_from_ema50_pct = round(((curr_close - curr_ema50) / curr_ema50) * 100.0, 2)
    
    # Price Action Highs: Recent 50-bar Swing High & 52-Week / All-Time High
    high_52w = float(df["high"].max())
    low_52w = float(df["low"].min())
    pct_from_52w_high = round(((curr_close - high_52w) / high_52w) * 100.0, 2)
    
    # Recent Price Action Swing High (major resistance peak of previous 2-3 months)
    if len(df) >= 45:
        # Exclude latest bar to identify the established swing resistance peak
        swing_high = float(df["high"].iloc[-50:-2].max())
    else:
        swing_high = high_52w
        
    if swing_high >= high_52w * 0.985:
        swing_high = high_52w
        
    dist_to_swing_high_pct = round(((swing_high - curr_close) / curr_close) * 100.0, 2)
    dist_to_ath_pct = round(((high_52w - curr_close) / curr_close) * 100.0, 2)

    base_result = {
        "symbol": clean_sym,
        "name": meta["name"],
        "sector": meta["sector"],
        "is_bought": is_bought,
        "current_price": round(curr_close, 2),
        "day_change_pct": day_change_pct,
        "ema50": round(curr_ema50, 2),
        "ema200": round(curr_ema200, 2),
        "supertrend": round(curr_st, 2),
        "supertrend_dir": curr_st_dir,
        "supertrend_badge": "BULLISH (BUY)" if curr_st_dir == 1 else "BEARISH (SELL)",
        "rsi14": round(curr_rsi, 1),
        "volume_surge_x": vol_ratio,
        "atr": round(curr_atr, 2),
        "dist_from_ema50_pct": dist_from_ema50_pct,
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "pct_from_52w_high": pct_from_52w_high,
        "price_action_high": round(swing_high, 2),
        "dist_to_swing_high_pct": dist_to_swing_high_pct,
        "dist_to_ath_pct": dist_to_ath_pct,
        "target1": round(swing_high, 2),
        "target2": round(high_52w, 2)
    }

    # =========================================================================
    # CASE 1: ALREADY BOUGHT (Active Portfolio Position -> EXIT & TRAIL ENGINE)
    # Strategy: Exit is strictly based on Supertrend asking to sell, OR reaching
    #           Price Action High / All-Time High (ATH).
    # =========================================================================
    if is_bought and buy_price and buy_price > 0:
        qty = int(quantity or 0)
        invested_capital = round(buy_price * qty, 2)
        current_value = round(curr_close * qty, 2)
        unrealized_pnl = round((curr_close - buy_price) * qty, 2)
        pnl_pct = round(((curr_close - buy_price) / buy_price) * 100.0, 2)

        # Calculate hold duration
        hold_days = 0
        if buy_date:
            try:
                b_date = datetime.strptime(buy_date, "%Y-%m-%d").date()
                hold_days = (date.today() - b_date).days
            except Exception:
                hold_days = 0

        # Trailing Stop-Loss: Pegged directly to Supertrend line
        # If in healthy profit, guarantee at least breakeven buy price
        if curr_st_dir == 1:
            trailing_sl = round(max(buy_price, curr_st) if pnl_pct >= 4.0 else curr_st, 2)
        else:
            trailing_sl = round(curr_st, 2)

        sl_price = round(float(initial_sl) if initial_sl and float(initial_sl) > 0 else trailing_sl, 2)
        sl_distance_pct = round(((curr_close - sl_price) / curr_close) * 100.0, 2)
        open_risk_amt = round(max(0.0, curr_close - sl_price) * qty, 2) if curr_st_dir == 1 else 0.0

        # Base risk unit per share for planning targets
        r_unit = max(buy_price - sl_price, buy_price * 0.025)

        # Standard R-multiple targets (1.5R, 2.5R, 3.5R, 5.0R)
        calc_t1 = round(buy_price + 1.5 * r_unit, 2)
        calc_t2 = round(buy_price + 2.5 * r_unit, 2)
        calc_t3 = round(buy_price + 3.5 * r_unit, 2)
        calc_t4 = round(buy_price + 5.0 * r_unit, 2)

        # Align with major swing high & ATH milestones if within range
        if swing_high > buy_price * 1.01 and swing_high < calc_t2:
            calc_t1 = round(swing_high, 2)
        elif swing_high > buy_price * 1.01 and swing_high < calc_t3:
            calc_t2 = round(swing_high, 2)

        if high_52w > buy_price * 1.02 and high_52w > calc_t2 and high_52w < calc_t4:
            calc_t3 = round(high_52w, 2)

        if calc_t2 <= calc_t1: calc_t2 = round(calc_t1 + r_unit, 2)
        if calc_t3 <= calc_t2: calc_t3 = round(calc_t2 + r_unit, 2)
        if calc_t4 <= calc_t3: calc_t4 = round(calc_t3 + 1.5 * r_unit, 2)

        final_t1 = float(target1) if target1 and float(target1) > 0 else calc_t1
        final_t2 = float(target2) if target2 and float(target2) > 0 else calc_t2
        final_t3 = float(target3) if target3 and float(target3) > 0 else calc_t3
        final_t4 = float(target4) if target4 and float(target4) > 0 else calc_t4

        t1_pct = round(((final_t1 - curr_close) / curr_close) * 100.0, 2)
        t2_pct = round(((final_t2 - curr_close) / curr_close) * 100.0, 2)
        t3_pct = round(((final_t3 - curr_close) / curr_close) * 100.0, 2)
        t4_pct = round(((final_t4 - curr_close) / curr_close) * 100.0, 2)

        t1_profit = round((final_t1 - buy_price) * qty, 2)
        t2_profit = round((final_t2 - buy_price) * qty, 2)
        t3_profit = round((final_t3 - buy_price) * qty, 2)
        t4_profit = round((final_t4 - buy_price) * qty, 2)

        trade_plan = {
            "entry_price": round(buy_price, 2),
            "sl": {
                "price": sl_price,
                "dist_pct": sl_distance_pct,
                "risk_per_share": round(r_unit, 2),
                "open_risk_amt": open_risk_amt,
                "label": "Trailing SL" if curr_st_dir == 1 else "Stop-Loss"
            },
            "t1": {
                "price": final_t1,
                "dist_pct": t1_pct,
                "rr": "1:1.5R",
                "profit": t1_profit,
                "is_hit": curr_close >= final_t1,
                "label": "T1 (1.5R)"
            },
            "t2": {
                "price": final_t2,
                "dist_pct": t2_pct,
                "rr": "1:2.5R",
                "profit": t2_profit,
                "is_hit": curr_close >= final_t2,
                "label": "T2 (2.5R)"
            },
            "t3": {
                "price": final_t3,
                "dist_pct": t3_pct,
                "rr": "1:3.5R",
                "profit": t3_profit,
                "is_hit": curr_close >= final_t3,
                "label": "T3 (3.5R)"
            },
            "t4": {
                "price": final_t4,
                "dist_pct": t4_pct,
                "rr": "1:5.0R",
                "profit": t4_profit,
                "is_hit": curr_close >= final_t4,
                "label": "T4 (5.0R Runner)"
            }
        }

        # Primary Exit Decision Logic
        exit_verdict = "HOLD"
        verdict_badge = "success"
        urgency = "LOW"
        reasons = []
        action_plan = ""

        # CONDITION 1: Supertrend Asking to Sell (Critical Trend Exit / Breakdown)
        if curr_st_dir == -1 or curr_close < curr_st:
            exit_verdict = "EXIT IMMEDIATELY - SUPERTREND ASKING TO SELL"
            verdict_badge = "danger"
            urgency = "CRITICAL"
            reasons.append(f"Supertrend (10, 3) has triggered a SELL signal (Red) at ₹{curr_st:.2f}!")
            reasons.append(f"Current price (₹{curr_close:.2f}) closed below the Supertrend line. Trend has officially broken down.")
            reasons.append("Pro Trader Rule: Always honor the Supertrend Sell signal immediately. Never hold or hope once Supertrend asks to sell.")
            action_plan = f"EXIT all {qty} shares immediately at market price. Capital preservation is priority #1."

        # CONDITION 2: All-Time High / 52-Week High Breakout (BLUE SKY MOMENTUM - RIDE & TRAIL)
        elif curr_close >= high_52w * 0.995 or float(df["high"].iloc[-1]) >= high_52w * 0.998:
            exit_verdict = "HOLD & RIDE - ALL-TIME HIGH (ATH) MOMENTUM BREAKOUT"
            verdict_badge = "success"
            urgency = "HOLD"
            reasons.append(f"🚀 Blue Sky Momentum: Stock is breaking out at All-Time High / 52-Week High (₹{high_52w:.2f})!")
            reasons.append(f"Unrealized profit is +{pnl_pct:.1f}%. With zero overhead resistance, institutional momentum can accelerate.")
            reasons.append(f"Pro Momentum Rule: Do NOT exit a breakout winner early. Trail your Stop-Loss strictly along Supertrend (₹{sl_price:.2f}) and let the trend run.")
            action_plan = f"HOLD & RIDE {qty} shares. Blue-sky breakout active. Trail Stop-Loss pegged to Supertrend at ₹{sl_price:.2f}. Let profits run until Supertrend turns Red."

        # CONDITION 3: Approaching or Reached Major Price Action Swing High
        elif (curr_close >= swing_high * 0.995 or float(df["high"].iloc[-1]) >= swing_high * 0.998) and swing_high < high_52w * 0.985 and curr_close > buy_price:
            exit_verdict = "HOLD & RIDE - PRICE ACTION SWING HIGH MOMENTUM"
            verdict_badge = "success"
            urgency = "HOLD"
            reasons.append(f"⚡ Swing Resistance Test: Stock tested prior swing high at ₹{swing_high:.2f} (+{pnl_pct:.1f}% P&L).")
            reasons.append(f"Supertrend remains Bullish Green at ₹{sl_price:.2f}, indicating buyers are absorbing supply.")
            reasons.append("Pro Momentum Rule: Trail Stop-Loss to Supertrend. If swing high breaks out, next target is All-Time High.")
            action_plan = f"HOLD & TRAIL Stop-Loss to Supertrend (₹{sl_price:.2f}). Allow runner to target All-Time High (₹{high_52w:.2f}). Optional: Book partial (25-50%) only if desired."

        # CONDITION 4: HOLD & RIDE (Supertrend is Bullish Green and price is approaching Highs)
        else:
            target_goal = high_52w if curr_close >= swing_high * 0.985 else swing_high
            goal_label = "All-Time High" if target_goal == high_52w else "Price Action High"
            dist_to_goal = round(((target_goal - curr_close) / curr_close) * 100.0, 1)

            exit_verdict = f"HOLD & RIDE - SUPERTREND BULLISH (TARGET: {goal_label.upper()})"
            verdict_badge = "success"
            urgency = "HOLD"
            reasons.append(f"Price (₹{curr_close:.2f}) is trading above Daily 50 EMA (₹{curr_ema50:.2f}) with Bullish (Green) Supertrend trailing at ₹{curr_st:.2f}.")
            reasons.append(f"Targeting {goal_label} at ₹{target_goal:.2f} (needs +{dist_to_goal}% move).")
            reasons.append("Supertrend has NOT asked to sell. Continue to ride the trend.")
            action_plan = f"HOLD with Trailing Stop-Loss at Supertrend (₹{sl_price:.2f}). Planning Targets: T1 ₹{final_t1:.2f} | T2 ₹{final_t2:.2f} | T3 ₹{final_t3:.2f} | T4 ₹{final_t4:.2f}."

        return {
            **base_result,
            "buy_price": buy_price,
            "quantity": qty,
            "buy_date": buy_date,
            "hold_days": hold_days,
            "invested_capital": invested_capital,
            "current_value": current_value,
            "unrealized_pnl": unrealized_pnl,
            "pnl_pct": pnl_pct,
            "stop_loss": sl_price,
            "initial_sl": initial_sl or round(curr_st, 2),
            "trailing_sl": trailing_sl,
            "sl_distance_pct": sl_distance_pct,
            "open_risk_amt": open_risk_amt,
            "target1": final_t1,
            "target2": final_t2,
            "target3": final_t3,
            "target4": final_t4,
            "target_price_action_high": round(swing_high, 2),
            "target_ath": round(high_52w, 2),
            "trade_plan": trade_plan,
            "exit_verdict": exit_verdict,
            "verdict_badge": verdict_badge,
            "urgency": urgency,
            "reasons": reasons,
            "action_plan": action_plan
        }

    # =========================================================================
    # CASE 2: NOT BOUGHT (Watchlist / Potential Buy Candidate -> BUY ENTRY ENGINE)
    # =========================================================================
    else:
        # We ONLY deal with Buy signals in swing trading!
        # Stop-Loss is pegged to Supertrend (10,3) or custom initial_sl
        suggested_sl = float(initial_sl) if initial_sl and float(initial_sl) > 0 else (
            round(curr_st, 2) if (curr_st_dir == 1 and curr_st < curr_close) else round(curr_close - 1.5 * curr_atr, 2)
        )
        risk_per_share = round(max(curr_close - suggested_sl, curr_close * 0.02), 2)
        risk_pct = round((risk_per_share / curr_close) * 100.0, 2)
        
        # Position sizing example for ₹2,000 risk
        std_risk_budget = 2000.0
        rec_shares = max(1, int(std_risk_budget // risk_per_share))
        rec_investment = round(rec_shares * curr_close, 2)

        # Standard R-multiple targets
        calc_t1 = round(curr_close + 1.5 * risk_per_share, 2)
        calc_t2 = round(curr_close + 2.5 * risk_per_share, 2)
        calc_t3 = round(curr_close + 3.5 * risk_per_share, 2)
        calc_t4 = round(curr_close + 5.0 * risk_per_share, 2)

        if swing_high > curr_close * 1.01 and swing_high < calc_t2:
            calc_t1 = round(swing_high, 2)
        elif swing_high > curr_close * 1.01 and swing_high < calc_t3:
            calc_t2 = round(swing_high, 2)

        if high_52w > curr_close * 1.02 and high_52w > calc_t2 and high_52w < calc_t4:
            calc_t3 = round(high_52w, 2)

        if calc_t2 <= calc_t1: calc_t2 = round(calc_t1 + risk_per_share, 2)
        if calc_t3 <= calc_t2: calc_t3 = round(calc_t2 + risk_per_share, 2)
        if calc_t4 <= calc_t3: calc_t4 = round(calc_t3 + 1.5 * risk_per_share, 2)

        final_t1 = float(target1) if target1 and float(target1) > 0 else calc_t1
        final_t2 = float(target2) if target2 and float(target2) > 0 else calc_t2
        final_t3 = float(target3) if target3 and float(target3) > 0 else calc_t3
        final_t4 = float(target4) if target4 and float(target4) > 0 else calc_t4

        t1_pct = round(((final_t1 - curr_close) / curr_close) * 100.0, 2)
        t2_pct = round(((final_t2 - curr_close) / curr_close) * 100.0, 2)
        t3_pct = round(((final_t3 - curr_close) / curr_close) * 100.0, 2)
        t4_pct = round(((final_t4 - curr_close) / curr_close) * 100.0, 2)

        t1_profit = round((final_t1 - curr_close) * rec_shares, 2)
        t2_profit = round((final_t2 - curr_close) * rec_shares, 2)
        t3_profit = round((final_t3 - curr_close) * rec_shares, 2)
        t4_profit = round((final_t4 - curr_close) * rec_shares, 2)

        trade_plan = {
            "entry_price": round(curr_close, 2),
            "sl": {
                "price": suggested_sl,
                "dist_pct": round(((curr_close - suggested_sl) / curr_close) * 100.0, 2),
                "risk_per_share": risk_per_share,
                "open_risk_amt": round(risk_per_share * rec_shares, 2),
                "label": "Supertrend SL" if curr_st_dir == 1 else "Stop-Loss"
            },
            "t1": {
                "price": final_t1,
                "dist_pct": t1_pct,
                "rr": "1:1.5R",
                "profit": t1_profit,
                "is_hit": curr_close >= final_t1,
                "label": "T1 (1.5R)"
            },
            "t2": {
                "price": final_t2,
                "dist_pct": t2_pct,
                "rr": "1:2.5R",
                "profit": t2_profit,
                "is_hit": curr_close >= final_t2,
                "label": "T2 (2.5R)"
            },
            "t3": {
                "price": final_t3,
                "dist_pct": t3_pct,
                "rr": "1:3.5R",
                "profit": t3_profit,
                "is_hit": curr_close >= final_t3,
                "label": "T3 (3.5R / ATH)"
            },
            "t4": {
                "price": final_t4,
                "dist_pct": t4_pct,
                "rr": "1:5.0R",
                "profit": t4_profit,
                "is_hit": curr_close >= final_t4,
                "label": "T4 (5.0R Runner)"
            }
        }

        entry_verdict = "NO BUY SETUP"
        verdict_badge = "secondary"
        reasons = []
        action_plan = ""
        is_actionable = False

        # Rule 1: Supertrend is asking to SELL or Bearish breakdown below Daily 50 EMA
        if curr_st_dir == -1 or curr_close < curr_ema50:
            entry_verdict = "NO BUY SETUP (BELOW 50 EMA OR SUPERTREND RED)"
            verdict_badge = "danger"
            if curr_close < curr_ema50:
                reasons.append(f"Daily Close (₹{curr_close:.2f}) is below the Daily 50 EMA (₹{curr_ema50:.2f}). Long swing buying strictly requires daily close above 50 EMA.")
            if curr_st_dir == -1:
                reasons.append(f"Supertrend (10,3) is in SELL mode (Red) at ₹{curr_st:.2f}.")
            action_plan = f"Do NOT enter. For Long swing buying, wait for Daily Close above 50 EMA (₹{curr_ema50:.2f}) with Supertrend Bullish Green."

        # Rule 2: Overextended from 50 EMA / Supertrend
        elif dist_from_ema50_pct > 4.5:
            entry_verdict = "BUY ON PULLBACK (OVEREXTENDED)"
            verdict_badge = "warning"
            pullback_zone_low = round(curr_ema50, 2)
            pullback_zone_high = round(curr_ema50 * 1.02, 2)
            reasons.append(f"Supertrend is Green, but price is +{dist_from_ema50_pct:.1f}% extended from 50 EMA.")
            reasons.append(f"RSI is {curr_rsi:.1f}. Favorable swing entry requires buying near support.")
            action_plan = f"Wait for pullback to support zone (₹{pullback_zone_low:.2f} - ₹{pullback_zone_high:.2f}) before entering."

        # Rule 3: All-Time High / 52W High Breakout Setup (BLUE SKY MOMENTUM BUY)
        elif curr_close >= high_52w * 0.99:
            is_actionable = True
            entry_verdict = "ACTIONABLE BUY (ATH MOMENTUM BREAKOUT)"
            verdict_badge = "success"
            reasons.append(f"🚀 Blue Sky Momentum Breakout: Trading at All-Time High / 52-Week High (₹{high_52w:.2f}).")
            reasons.append(f"Supertrend is Bullish Green at ₹{curr_st:.2f}. Stock has entered price discovery with zero overhead resistance.")
            reasons.append(f"Volume conviction ratio is {vol_surge_x}x. High-velocity institutional momentum setup.")
            action_plan = f"BUY MOMENTUM at ₹{curr_close:.2f}. Set Stop-Loss at Supertrend (₹{suggested_sl:.2f}, -{risk_pct:.1f}%). Targets: T1 ₹{final_t1:.2f} | T2 ₹{final_t2:.2f} | T3 ₹{final_t3:.2f} | T4 ₹{final_t4:.2f}. Trail stop-loss along Supertrend and let winner run."

        # Rule 4: Actionable Buy Setup (Standard Swing: Price above Daily 50 EMA + Supertrend Green)
        else:
            is_actionable = True
            entry_verdict = "ACTIONABLE BUY (PRICE > 50 EMA & SUPERTREND BULLISH)"
            verdict_badge = "success"
            reasons.append(f"Long Swing Criteria Met: Daily Close (₹{curr_close:.2f}) is above 50 EMA (₹{curr_ema50:.2f}).")
            reasons.append(f"Supertrend (10, 3) is Bullish Green at ₹{curr_st:.2f} (active trend support).")
            reasons.append(f"Favorable upside to Price Action High (₹{swing_high:.2f}, +{dist_to_swing_high_pct}%) and ATH (₹{high_52w:.2f}, +{dist_to_ath_pct}%).")
            action_plan = f"BUY at ₹{curr_close:.2f}. Set Stop-Loss at Supertrend (₹{suggested_sl:.2f}, -{risk_pct:.1f}%). Targets: T1 ₹{final_t1:.2f} | T2 ₹{final_t2:.2f} | T3 ₹{final_t3:.2f} | T4 ₹{final_t4:.2f}. Exit when Supertrend turns Red or targets are achieved."

        return {
            **base_result,
            "is_actionable": is_actionable,
            "entry_verdict": entry_verdict,
            "verdict_badge": verdict_badge,
            "suggested_entry_price": round(curr_close, 2),
            "suggested_sl": suggested_sl,
            "stop_loss": suggested_sl,
            "risk_per_share": risk_per_share,
            "risk_pct": risk_pct,
            "target1": final_t1,
            "target2": final_t2,
            "target3": final_t3,
            "target4": final_t4,
            "target_price_action_high": round(swing_high, 2),
            "target_ath": round(high_52w, 2),
            "trade_plan": trade_plan,
            "rec_shares_2k_risk": rec_shares,
            "rec_investment_2k_risk": rec_investment,
            "reasons": reasons,
            "action_plan": action_plan
        }

def analyze_entire_portfolio(portfolio_id: str = None, force_refresh: bool = False) -> dict:
    """
    Analyzes all active holdings and watchlist items for a specific portfolio concurrently.
    Computes portfolio health metrics, risk exposure, and pro advice.
    Uses 60s in-memory cache per portfolio when force_refresh=False for instant response.
    """
    data = load_portfolio_data()
    target_p, _ = get_portfolio_by_id(data, portfolio_id)
    p_id = target_p["id"]

    global PORTFOLIO_CACHE
    now_ts = time.time()
    if not force_refresh and p_id in PORTFOLIO_CACHE:
        cache_entry = PORTFOLIO_CACHE[p_id]
        if now_ts - cache_entry.get("timestamp", 0) < 180.0:
            cached_data = cache_entry.get("data")
            if cached_data:
                cached_data["all_portfolios"] = get_all_portfolios_meta()
                return cached_data

    # Map previous cached holdings/watchlist by ID to prevent transient network dropouts from breaking UI
    prev_holdings_map = {}
    prev_watchlist_map = {}
    if p_id in PORTFOLIO_CACHE and PORTFOLIO_CACHE[p_id].get("data"):
        for prev_h in PORTFOLIO_CACHE[p_id]["data"].get("holdings", []):
            if prev_h.get("id") and not prev_h.get("error"):
                prev_holdings_map[prev_h["id"]] = prev_h
        for prev_w in PORTFOLIO_CACHE[p_id]["data"].get("watchlist", []):
            if prev_w.get("id") and not prev_w.get("error"):
                prev_watchlist_map[prev_w["id"]] = prev_w

    holdings = target_p.get("holdings", [])
    watchlist = target_p.get("watchlist", [])
    history = target_p.get("history", [])
    settings = target_p.get("settings", {"total_capital": 500000.0, "max_risk_per_trade_pct": 1.0})

    analyzed_holdings = []
    analyzed_watchlist = []

    # Parallel processing for ultra-fast response
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit holdings
        future_to_holding = {
            executor.submit(
                analyze_single_stock,
                h["symbol"],
                is_bought=True,
                buy_price=float(h.get("buy_price", 0)),
                quantity=int(h.get("quantity", 0)),
                buy_date=h.get("buy_date"),
                initial_sl=float(h.get("initial_sl", 0)) if h.get("initial_sl") else None,
                target1=float(h.get("target1", 0)) if h.get("target1") else None,
                target2=float(h.get("target2", 0)) if h.get("target2") else None,
                target3=float(h.get("target3", 0)) if h.get("target3") else None,
                target4=float(h.get("target4", 0)) if h.get("target4") else None
            ): h for h in holdings
        }

        # Submit watchlist
        future_to_watchlist = {
            executor.submit(
                analyze_single_stock,
                w["symbol"],
                is_bought=False,
                initial_sl=float(w.get("initial_sl", 0)) if w.get("initial_sl") else None,
                target1=float(w.get("target1", 0)) if w.get("target1") else None,
                target2=float(w.get("target2", 0)) if w.get("target2") else None,
                target3=float(w.get("target3", 0)) if w.get("target3") else None,
                target4=float(w.get("target4", 0)) if w.get("target4") else None
            ): w for w in watchlist
        }

        for future in future_to_holding:
            h = future_to_holding[future]
            try:
                res = future.result()
                res["id"] = h["id"]
                res["notes"] = h.get("notes", "")
                res["created_at"] = h.get("created_at", "")
                if "error" in res and h["id"] in prev_holdings_map:
                    restored = prev_holdings_map[h["id"]].copy()
                    restored["notes"] = h.get("notes", "")
                    analyzed_holdings.append(restored)
                else:
                    analyzed_holdings.append(res)
            except Exception as e:
                print(f"Error analyzing holding {h['symbol']}: {e}")
                if h["id"] in prev_holdings_map:
                    analyzed_holdings.append(prev_holdings_map[h["id"]].copy())

        for future in future_to_watchlist:
            w = future_to_watchlist[future]
            try:
                res = future.result()
                res["id"] = w["id"]
                res["target_entry_price"] = w.get("target_entry_price")
                res["notes"] = w.get("notes", "")
                res["created_at"] = w.get("created_at", "")
                if "error" in res and w["id"] in prev_watchlist_map:
                    restored = prev_watchlist_map[w["id"]].copy()
                    restored["target_entry_price"] = w.get("target_entry_price")
                    restored["notes"] = w.get("notes", "")
                    analyzed_watchlist.append(restored)
                else:
                    analyzed_watchlist.append(res)
            except Exception as e:
                print(f"Error analyzing watchlist {w['symbol']}: {e}")
                if w["id"] in prev_watchlist_map:
                    analyzed_watchlist.append(prev_watchlist_map[w["id"]].copy())

    # Aggregate Portfolio Metrics
    total_invested = sum(h.get("invested_capital", 0.0) for h in analyzed_holdings if "invested_capital" in h)
    current_portfolio_value = sum(h.get("current_value", 0.0) for h in analyzed_holdings if "current_value" in h)
    total_unrealized_pnl = round(current_portfolio_value - total_invested, 2)
    total_pnl_pct = round((total_unrealized_pnl / total_invested * 100.0), 2) if total_invested > 0 else 0.0
    total_open_risk = sum(h.get("open_risk_amt", 0.0) for h in analyzed_holdings if "open_risk_amt" in h)
    
    total_capital = float(settings.get("total_capital", 500000.0))
    capital_deployed_pct = round((total_invested / total_capital * 100.0), 2) if total_capital > 0 else 0.0
    total_risk_pct_of_capital = round((total_open_risk / total_capital * 100.0), 2) if total_capital > 0 else 0.0

    # Calculate exact percentage weight/allocation for each holding
    for h in analyzed_holdings:
        inv = float(h.get("invested_capital", 0.0))
        h["allocation_pct"] = round((inv / total_invested * 100.0), 2) if total_invested > 0 else 0.0
        h["capital_weight_pct"] = round((inv / total_capital * 100.0), 2) if total_capital > 0 else 0.0

    # Risk Alerts & Pro Action Recommendations
    risk_alerts = []
    exit_now_count = 0
    t1_hit_count = 0

    for h in analyzed_holdings:
        if h.get("urgency") == "CRITICAL":
            exit_now_count += 1
            risk_alerts.append({
                "type": "danger",
                "symbol": h["symbol"],
                "message": f"🚨 SUPERTREND SELL SIGNAL on {h['symbol']}! Current price ₹{h['current_price']} is below Supertrend (₹{h.get('trailing_sl')}). Supertrend asks to sell. Exit immediately."
            })
        elif h.get("urgency") == "ACTIONABLE":
            t1_hit_count += 1
            high_label = "All-Time High (ATH)" if "ALL-TIME" in h.get("exit_verdict", "") else "Price Action High"
            risk_alerts.append({
                "type": "gold",
                "symbol": h["symbol"],
                "message": f"🏆 {h['symbol']} has reached {high_label} at ₹{h.get('current_price')} (+{h.get('pnl_pct')}%)! Exit / Book profits into resistance."
            })
        
        # Check concentration risk (> 25% of total invested)
        if total_invested > 0:
            inv_pct = (h.get("invested_capital", 0.0) / total_invested) * 100.0
            if inv_pct > 25.0:
                risk_alerts.append({
                    "type": "warning",
                    "symbol": h["symbol"],
                    "message": f"Overconcentration Warning: {h['symbol']} represents {inv_pct:.1f}% of total deployed capital. Max recommended is 20-25%."
                })

        # ATH Momentum Notification
        if "ALL-TIME HIGH (ATH) MOMENTUM" in h.get("exit_verdict", ""):
            risk_alerts.append({
                "type": "success",
                "symbol": h["symbol"],
                "message": f"🚀 ATH MOMENTUM BREAKOUT on {h['symbol']}! Breaking out into blue sky territory at ₹{h.get('current_price')} (+{h.get('pnl_pct')}%). Trail SL pegged to Supertrend (₹{h.get('trailing_sl')}) and let winner run."
            })

    # History Performance Stats
    total_trades = len(history)
    wins = [t for t in history if t.get("is_win", False) or t.get("realized_pnl", 0) > 0]
    losses = [t for t in history if not t.get("is_win", False) and t.get("realized_pnl", 0) <= 0]
    
    total_realized_pnl = round(sum(t.get("realized_pnl", 0.0) for t in history), 2)
    win_rate = round((len(wins) / total_trades * 100.0), 1) if total_trades > 0 else 0.0
    
    total_gain = sum(t.get("realized_pnl", 0.0) for t in wins)
    total_loss = abs(sum(t.get("realized_pnl", 0.0) for t in losses))
    profit_factor = round(total_gain / (total_loss + 1e-9), 2) if total_loss > 0 else (round(total_gain, 2) if total_gain > 0 else 1.0)
    
    avg_hold_days = round(sum(t.get("hold_days", 0) for t in history) / total_trades, 1) if total_trades > 0 else 0

    # Aladdin Institutional Portfolio Diagnostics & Capital Recycling Engine
    aladdin_diagnostics = calculate_aladdin_diagnostics(analyzed_holdings, total_invested)

    result_payload = {
        "status": "success",
        "portfolio_id": p_id,
        "portfolio_name": target_p["name"],
        "all_portfolios": get_all_portfolios_meta(),
        "timestamp": datetime.now().isoformat(),
        "holdings": analyzed_holdings,
        "watchlist": analyzed_watchlist,
        "history": history,
        "aladdin_diagnostics": aladdin_diagnostics,
        "summary": {
            "total_capital": total_capital,
            "total_invested": total_invested,
            "current_portfolio_value": current_portfolio_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_pnl_pct": total_pnl_pct,
            "capital_deployed_pct": capital_deployed_pct,
            "total_open_risk": total_open_risk,
            "total_risk_pct_of_capital": total_risk_pct_of_capital,
            "active_positions_count": len(analyzed_holdings),
            "watchlist_count": len(analyzed_watchlist),
            "exit_now_alerts": exit_now_count,
            "target1_alerts": t1_hit_count,
            "risk_alerts": risk_alerts
        },
        "history_stats": {
            "total_closed_trades": total_trades,
            "win_rate": win_rate,
            "total_realized_pnl": total_realized_pnl,
            "profit_factor": profit_factor,
            "wins_count": len(wins),
            "losses_count": len(losses),
            "avg_hold_days": avg_hold_days
        }
    }
    PORTFOLIO_CACHE[p_id] = {"data": result_payload, "timestamp": now_ts}
    return result_payload

def calculate_aladdin_diagnostics(analyzed_holdings: list, total_invested: float) -> dict:
    """
    Institutional Aladdin Portfolio Optimization & Capital Recycling Engine.
    Diagnoses each position based on Stan Weinstein Stage Analysis, Supertrend,
    and Relative Strength, providing actionable recovery roadmaps.
    """
    runners = []
    bases = []
    traps = []
    special = []
    
    for h in analyzed_holdings:
        sym = h.get("symbol", "").upper()
        curr_close = float(h.get("current_price", 0.0))
        buy_p = float(h.get("buy_price", 0.0))
        pnl_pct = float(h.get("pnl_pct", 0.0))
        pnl_amt = float(h.get("unrealized_pnl", 0.0))
        st_dir = int(h.get("supertrend_dir", 1))
        st_val = float(h.get("supertrend", 0.0))
        e50 = float(h.get("ema50", 0.0))
        e200 = float(h.get("ema200", 0.0))
        inv = float(h.get("invested_capital", 0.0))
        qty = int(h.get("quantity", 0))
        
        # 1. SPECIAL CASE: SUZLON (High-Beta Wind Turnaround)
        if sym == "SUZLON":
            crit_supp = round(st_val, 2)
            rel_targ = round(max(e50, curr_close * 1.15), 2)
            item = {
                "symbol": sym,
                "name": h.get("name", sym),
                "stage": "SPECIAL_CASE",
                "stage_label": "High-Beta Turnaround Watch",
                "stage_badge": "warning",
                "current_price": curr_close,
                "buy_price": buy_p,
                "quantity": qty,
                "pnl_pct": pnl_pct,
                "unrealized_pnl": pnl_amt,
                "invested_capital": inv,
                "critical_support": crit_supp,
                "relief_target": rel_targ,
                "verdict": f"HOLD ABOVE ₹{crit_supp:.2f} | HARD CUT IF ₹{crit_supp:.2f} BREAKS",
                "rationale": f"High-beta turnaround momentum stock. Supertrend support is active at ₹{crit_supp:.2f}. Position return is {pnl_pct:+.1f}% (bought @ ₹{buy_p:.2f}). Pro Rule: If ₹{crit_supp:.2f} holds on daily close, hold for technical relief bounce toward ₹{rel_targ:.2f} to trim. If daily close drops below ₹{crit_supp:.2f}, exit immediately to protect capital."
            }
            special.append(item)
            h["aladdin_stage"] = item["stage"]
            h["aladdin_verdict"] = item["verdict"]
            h["aladdin_badge"] = "warning"
            h["aladdin_rationale"] = item["rationale"]
            
        # 2. STAGE 2 MOMENTUM LEADERS (RUNNERS)
        elif st_dir == 1 and curr_close >= e50 and pnl_pct >= 0:
            item = {
                "symbol": sym,
                "name": h.get("name", sym),
                "stage": "STAGE_2_RUNNER",
                "stage_label": "Stage 2 Momentum Leader",
                "stage_badge": "success",
                "current_price": curr_close,
                "buy_price": buy_p,
                "quantity": qty,
                "pnl_pct": pnl_pct,
                "unrealized_pnl": pnl_amt,
                "invested_capital": inv,
                "trailing_sl": h.get("trailing_sl", st_val),
                "target_ath": h.get("high_52w", 0.0),
                "verdict": "LET WINNER RUN | TRAIL STOP AT SUPERTREND",
                "rationale": f"Secular institutional uptrend. Price > 50 EMA on Daily and Supertrend is Bullish Green. Do NOT sell prematurely. Trail stop loss pegged to Supertrend (₹{h.get('trailing_sl', st_val):.2f}). Ride momentum into blue sky territory beyond All-Time High (₹{h.get('high_52w', 0.0):.2f})."
            }
            runners.append(item)
            h["aladdin_stage"] = item["stage"]
            h["aladdin_verdict"] = item["verdict"]
            h["aladdin_badge"] = "success"
            h["aladdin_rationale"] = item["rationale"]
            
        # 3. STAGE 1 ACCUMULATION BASES (REVERSALS)
        elif st_dir == 1 and curr_close < e50:
            item = {
                "symbol": sym,
                "name": h.get("name", sym),
                "stage": "STAGE_1_BASE",
                "stage_label": "Stage 1 Base / Reversal",
                "stage_badge": "info",
                "current_price": curr_close,
                "buy_price": buy_p,
                "quantity": qty,
                "pnl_pct": pnl_pct,
                "unrealized_pnl": pnl_amt,
                "invested_capital": inv,
                "breakout_level": e50,
                "trailing_sl": st_val,
                "verdict": "HOLD AT BASE (NEVER AVERAGE DOWN)",
                "rationale": f"Supertrend has turned Bullish Green at ₹{st_val:.2f}, but price is still below 50 EMA (₹{e50:.2f}). Hold with strict trailing SL at ₹{st_val:.2f}. For Long swing buying, price must close above 50 EMA on Daily."
            }
            bases.append(item)
            h["aladdin_stage"] = item["stage"]
            h["aladdin_verdict"] = item["verdict"]
            h["aladdin_badge"] = "info"
            h["aladdin_rationale"] = item["rationale"]
            
        # 4. STAGE 4 VALUE TRAPS / SEVERE BLEEDERS
        else:
            relief_target = round(min(e50, curr_close * 1.06), 2)
            item = {
                "symbol": sym,
                "name": h.get("name", sym),
                "stage": "STAGE_4_VALUE_TRAP",
                "stage_label": "Stage 4 Downtrend / Below 50 EMA",
                "stage_badge": "danger",
                "current_price": curr_close,
                "buy_price": buy_p,
                "quantity": qty,
                "pnl_pct": pnl_pct,
                "unrealized_pnl": pnl_amt,
                "invested_capital": inv,
                "relief_exit_target": relief_target,
                "verdict": "CAPITAL RECYCLING / RELIEF EXIT",
                "rationale": f"Downtrend Alert: Technical breakdown (Supertrend SELL or below Daily 50 EMA). Holding this incurs severe opportunity cost. Action: Place limit sell at Daily 50 EMA resistance (₹{relief_target:.2f}) or execute Aladdin Capital Recycling into Long Momentum BUYs (above 50 EMA + Supertrend Green)."
            }
            traps.append(item)
            h["aladdin_stage"] = item["stage"]
            h["aladdin_verdict"] = item["verdict"]
            h["aladdin_badge"] = "danger"
            h["aladdin_rationale"] = item["rationale"]

    # Calculate Aladdin Capital Distribution
    inv_runners = sum(r["invested_capital"] for r in runners)
    inv_bases = sum(b["invested_capital"] for b in bases)
    inv_traps = sum(t["invested_capital"] for t in traps)
    inv_special = sum(s["invested_capital"] for s in special)
    total_trapped_loss = sum(t["unrealized_pnl"] for t in traps)
    
    # Portfolio Health Score (0 - 100)
    health_score = 50.0
    if total_invested > 0:
        health_score = round(((inv_runners * 1.0 + inv_bases * 0.60 + inv_special * 0.35) / total_invested) * 100.0, 1)
        
    return {
        "health_score": health_score,
        "health_status": "CRITICAL ATTENTION REQUIRED" if health_score < 55 else ("MODERATE" if health_score < 75 else "EXCELLENT"),
        "stage2_runners": runners,
        "stage1_bases": bases,
        "stage4_traps": traps,
        "special_cases": special,
        "summary": {
            "total_invested": round(total_invested, 2),
            "runners_invested": round(inv_runners, 2),
            "runners_pct": round((inv_runners / total_invested * 100.0), 1) if total_invested else 0,
            "bases_invested": round(inv_bases, 2),
            "bases_pct": round((inv_bases / total_invested * 100.0), 1) if total_invested else 0,
            "traps_invested": round(inv_traps, 2),
            "traps_pct": round((inv_traps / total_invested * 100.0), 1) if total_invested else 0,
            "special_invested": round(inv_special, 2),
            "total_trapped_loss": round(total_trapped_loss, 2),
            "estimated_opportunity_cost_monthly": round(inv_traps * 0.02, 2)
        }
    }

def add_portfolio_item(item_type: str, item_data: dict, portfolio_id: str = None) -> dict:
    """Adds stock to either 'holdings', 'watchlist', or 'history' in the specified portfolio."""
    data = load_portfolio_data()
    target_p, _ = get_portfolio_by_id(data, portfolio_id)
    if not target_p:
        return {"error": "Target portfolio not found."}

    clean_sym = item_data["symbol"].upper().replace(".NS", "").replace(".BO", "").strip()
    meta = get_symbol_metadata(clean_sym)
    new_id = str(uuid.uuid4())[:8]

    if item_type == "holding":
        # Check if already in holdings of target portfolio
        for h in target_p.get("holdings", []):
            if h["symbol"] == clean_sym:
                return {"error": f"{clean_sym} is already in '{target_p['name']}' holdings. Use Edit to adjust position."}
                
        # Remove from watchlist if present
        target_p["watchlist"] = [w for w in target_p.get("watchlist", []) if w["symbol"] != clean_sym]

        holding_obj = {
            "id": new_id,
            "symbol": clean_sym,
            "name": meta["name"],
            "sector": meta["sector"],
            "buy_price": float(item_data.get("buy_price", 0.0)),
            "quantity": int(item_data.get("quantity", 1)),
            "buy_date": item_data.get("buy_date") or datetime.now().strftime("%Y-%m-%d"),
            "initial_sl": float(item_data.get("initial_sl")) if item_data.get("initial_sl") else None,
            "target1": float(item_data.get("target1")) if item_data.get("target1") else None,
            "target2": float(item_data.get("target2")) if item_data.get("target2") else None,
            "target3": float(item_data.get("target3")) if item_data.get("target3") else None,
            "target4": float(item_data.get("target4")) if item_data.get("target4") else None,
            "notes": item_data.get("notes", "").strip(),
            "created_at": datetime.now().isoformat()
        }
        if "holdings" not in target_p:
            target_p["holdings"] = []
        target_p["holdings"].append(holding_obj)
        save_portfolio_data(data)
        invalidate_portfolio_cache(target_p["id"])
        return {"success": True, "message": f"{clean_sym} added to '{target_p['name']}'!", "item": holding_obj}

    elif item_type == "watchlist":
        for w in target_p.get("watchlist", []):
            if w["symbol"] == clean_sym:
                return {"error": f"{clean_sym} is already in '{target_p['name']}' Watchlist."}

        watchlist_obj = {
            "id": new_id,
            "symbol": clean_sym,
            "name": meta["name"],
            "sector": meta["sector"],
            "target_entry_price": float(item_data.get("target_entry_price", 0.0)) if item_data.get("target_entry_price") else None,
            "initial_sl": float(item_data.get("initial_sl")) if item_data.get("initial_sl") else None,
            "target1": float(item_data.get("target1")) if item_data.get("target1") else None,
            "target2": float(item_data.get("target2")) if item_data.get("target2") else None,
            "target3": float(item_data.get("target3")) if item_data.get("target3") else None,
            "target4": float(item_data.get("target4")) if item_data.get("target4") else None,
            "notes": item_data.get("notes", "").strip(),
            "created_at": datetime.now().isoformat()
        }
        if "watchlist" not in target_p:
            target_p["watchlist"] = []
        target_p["watchlist"].append(watchlist_obj)
        save_portfolio_data(data)
        invalidate_portfolio_cache(target_p["id"])
        return {"success": True, "message": f"{clean_sym} added to '{target_p['name']}' Watchlist!", "item": watchlist_obj}

    elif item_type == "history":
        buy_p = float(item_data.get("buy_price", 0.0))
        exit_p = float(item_data.get("exit_price", 0.0))
        q = int(item_data.get("quantity", 1))
        b_date = item_data.get("buy_date", datetime.now().strftime("%Y-%m-%d"))
        e_date = item_data.get("exit_date", datetime.now().strftime("%Y-%m-%d"))

        # Duration can be any number for history
        if item_data.get("hold_days") is not None and str(item_data.get("hold_days")).strip() != "":
            h_days = int(item_data["hold_days"])
        else:
            try:
                b_d = datetime.strptime(b_date, "%Y-%m-%d").date()
                e_d = datetime.strptime(e_date, "%Y-%m-%d").date()
                h_days = max(0, (e_d - b_d).days)
            except Exception:
                h_days = 0

        pnl = round((exit_p - buy_p) * q, 2)
        ret_pct = round(((exit_p - buy_p) / buy_p * 100.0), 2) if buy_p > 0 else 0.0

        hist_obj = {
            "id": new_id,
            "symbol": clean_sym,
            "name": meta["name"],
            "buy_price": buy_p,
            "exit_price": exit_p,
            "quantity": q,
            "buy_date": b_date,
            "exit_date": e_date,
            "hold_days": h_days,
            "realized_pnl": pnl,
            "return_pct": ret_pct,
            "is_win": pnl > 0,
            "exit_reason": item_data.get("exit_reason", "Target reached / Pro Trailing exit"),
            "notes": item_data.get("notes", "").strip(),
            "created_at": datetime.now().isoformat()
        }
        if "history" not in target_p:
            target_p["history"] = []
        target_p["history"].insert(0, hist_obj)
        save_portfolio_data(data)
        invalidate_portfolio_cache(target_p["id"])
        return {"success": True, "message": f"{clean_sym} logged to '{target_p['name']}' Trade Journal (Duration: {h_days} days)!", "item": hist_obj}

    return {"error": "Invalid item_type"}

def update_portfolio_item(item_type: str, item_id: str, updated_data: dict, portfolio_id: str = None) -> dict:
    """Edits holding or watchlist item in target portfolio (or across portfolios if not specified)."""
    data = load_portfolio_data()
    found = False
    affected_p_id = None

    portfolios_to_check = []
    if portfolio_id:
        p, _ = get_portfolio_by_id(data, portfolio_id)
        if p:
            portfolios_to_check = [p]
    if not portfolios_to_check:
        portfolios_to_check = data.get("portfolios", [])

    for target_p in portfolios_to_check:
        if item_type == "holding":
            for h in target_p.get("holdings", []):
                if h["id"] == item_id:
                    if "buy_price" in updated_data:
                        h["buy_price"] = float(updated_data["buy_price"])
                    if "quantity" in updated_data:
                        h["quantity"] = int(updated_data["quantity"])
                    if "buy_date" in updated_data:
                        h["buy_date"] = updated_data["buy_date"]
                    if "initial_sl" in updated_data:
                        h["initial_sl"] = float(updated_data["initial_sl"]) if updated_data["initial_sl"] else None
                    if "target1" in updated_data:
                        h["target1"] = float(updated_data["target1"]) if updated_data["target1"] else None
                    if "target2" in updated_data:
                        h["target2"] = float(updated_data["target2"]) if updated_data["target2"] else None
                    if "target3" in updated_data:
                        h["target3"] = float(updated_data["target3"]) if updated_data["target3"] else None
                    if "target4" in updated_data:
                        h["target4"] = float(updated_data["target4"]) if updated_data["target4"] else None
                    if "notes" in updated_data:
                        h["notes"] = updated_data["notes"].strip()
                    found = True
                    affected_p_id = target_p["id"]
                    break

        elif item_type == "watchlist":
            for w in target_p.get("watchlist", []):
                if w["id"] == item_id:
                    if "target_entry_price" in updated_data:
                        w["target_entry_price"] = float(updated_data["target_entry_price"]) if updated_data["target_entry_price"] else None
                    if "initial_sl" in updated_data:
                        w["initial_sl"] = float(updated_data["initial_sl"]) if updated_data["initial_sl"] else None
                    if "target1" in updated_data:
                        w["target1"] = float(updated_data["target1"]) if updated_data["target1"] else None
                    if "target2" in updated_data:
                        w["target2"] = float(updated_data["target2"]) if updated_data["target2"] else None
                    if "target3" in updated_data:
                        w["target3"] = float(updated_data["target3"]) if updated_data["target3"] else None
                    if "target4" in updated_data:
                        w["target4"] = float(updated_data["target4"]) if updated_data["target4"] else None
                    if "notes" in updated_data:
                        w["notes"] = updated_data["notes"].strip()
                    found = True
                    affected_p_id = target_p["id"]
                    break
        if found:
            break

    if found:
        save_portfolio_data(data)
        invalidate_portfolio_cache(affected_p_id)
        return {"success": True, "message": "Updated successfully!"}
    return {"error": f"Item {item_id} not found."}

def delete_portfolio_item(item_type: str, item_id: str, portfolio_id: str = None) -> dict:
    """Deletes holding, watchlist, or history item upon user confirmation."""
    data = load_portfolio_data()
    deleted = False
    affected_p_id = None

    portfolios_to_check = []
    if portfolio_id:
        p, _ = get_portfolio_by_id(data, portfolio_id)
        if p:
            portfolios_to_check = [p]
    if not portfolios_to_check:
        portfolios_to_check = data.get("portfolios", [])

    for target_p in portfolios_to_check:
        if item_type == "holding":
            orig = len(target_p.get("holdings", []))
            target_p["holdings"] = [h for h in target_p.get("holdings", []) if h["id"] != item_id]
            if len(target_p["holdings"]) < orig:
                deleted = True
                affected_p_id = target_p["id"]
                break
        elif item_type == "watchlist":
            orig = len(target_p.get("watchlist", []))
            target_p["watchlist"] = [w for w in target_p.get("watchlist", []) if w["id"] != item_id]
            if len(target_p["watchlist"]) < orig:
                deleted = True
                affected_p_id = target_p["id"]
                break
        elif item_type == "history":
            orig = len(target_p.get("history", []))
            target_p["history"] = [t for t in target_p.get("history", []) if t["id"] != item_id]
            if len(target_p["history"]) < orig:
                deleted = True
                affected_p_id = target_p["id"]
                break

    if deleted:
        save_portfolio_data(data)
        invalidate_portfolio_cache(affected_p_id)
        return {"success": True, "message": "Deleted successfully."}
    return {"error": f"Item {item_id} not found."}

def close_trade_and_log(item_id: str, exit_price: float, exit_date: str = None, exit_reason: str = "", hold_days: int = None, portfolio_id: str = None) -> dict:
    """
    Exits a holding and moves it to the Trade History Journal.
    Calculates realized PnL, percentage return, and hold duration (unbounded, can be any number of days).
    """
    data = load_portfolio_data()
    target_holding = None
    target_p = None

    portfolios_to_check = []
    if portfolio_id:
        p, _ = get_portfolio_by_id(data, portfolio_id)
        if p:
            portfolios_to_check = [p]
    if not portfolios_to_check:
        portfolios_to_check = data.get("portfolios", [])

    for p in portfolios_to_check:
        for h in p.get("holdings", []):
            if h["id"] == item_id:
                target_holding = h
                target_p = p
                break
        if target_holding:
            break

    if not target_holding or not target_p:
        return {"error": f"Holding with id {item_id} not found."}

    buy_price = float(target_holding["buy_price"])
    qty = int(target_holding["quantity"])
    buy_date_str = target_holding.get("buy_date", datetime.now().strftime("%Y-%m-%d"))
    exit_date_str = exit_date or datetime.now().strftime("%Y-%m-%d")

    # Duration: no bound, can be any number for history
    if hold_days is not None and hold_days >= 0:
        duration_days = int(hold_days)
    else:
        duration_days = 0
        try:
            b_d = datetime.strptime(buy_date_str, "%Y-%m-%d").date()
            e_d = datetime.strptime(exit_date_str, "%Y-%m-%d").date()
            duration_days = max(0, (e_d - b_d).days)
        except Exception:
            duration_days = 0

    realized_pnl = round((exit_price - buy_price) * qty, 2)
    return_pct = round(((exit_price - buy_price) / buy_price) * 100.0, 2) if buy_price > 0 else 0.0
    is_win = realized_pnl > 0

    history_record = {
        "id": str(uuid.uuid4())[:8],
        "symbol": target_holding["symbol"],
        "name": target_holding["name"],
        "buy_price": buy_price,
        "exit_price": round(exit_price, 2),
        "quantity": qty,
        "buy_date": buy_date_str,
        "exit_date": exit_date_str,
        "hold_days": duration_days,
        "realized_pnl": realized_pnl,
        "return_pct": return_pct,
        "is_win": is_win,
        "exit_reason": exit_reason or ("Stop Loss hit" if not is_win else "Target reached / Pro Trailing exit"),
        "notes": target_holding.get("notes", "")
    }

    # Remove from holdings and append to history of target portfolio
    target_p["holdings"] = [h for h in target_p.get("holdings", []) if h["id"] != item_id]
    if "history" not in target_p:
        target_p["history"] = []
    target_p["history"].insert(0, history_record)
    save_portfolio_data(data)
    invalidate_portfolio_cache(target_p["id"])

    return {
        "success": True,
        "message": f"Trade closed for {target_holding['symbol']} in '{target_p['name']}'! Realized P&L: ₹{realized_pnl:+,.2f} ({return_pct:+.2f}%) recorded to Trade Journal.",
        "record": history_record
    }

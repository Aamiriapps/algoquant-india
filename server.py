import os
import sys
import json
import csv
import io
import time
import threading
from datetime import datetime, timezone, timedelta, time as d_time
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from algo_engine import run_full_scan, get_chart_data, LIQUID_UNIVERSE
try:
    from dynamic_universe import get_active_universe, refresh_dynamic_momentum_universe, load_cached_universe
except ImportError:
    get_active_universe = None
    refresh_dynamic_momentum_universe = None
    load_cached_universe = None

from portfolio_manager import (
    analyze_entire_portfolio,
    analyze_single_stock,
    add_portfolio_item,
    update_portfolio_item,
    delete_portfolio_item,
    close_trade_and_log,
    get_all_portfolios_meta,
    create_new_portfolio,
    update_portfolio_meta,
    delete_user_portfolio,
    switch_active_portfolio,
    load_portfolio_data,
    get_portfolio_by_id
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

app = Flask(__name__, static_folder="static", static_url_path="")
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Persistent Disk Cache for Instant Startup
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def load_disk_cache(mode: str):
    file_path = os.path.join(CACHE_DIR, f"scan_{mode}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"Error loading {mode} cache from disk: {e}")
    return None

def save_disk_cache(mode: str, data: dict):
    if not data:
        return
    file_path = os.path.join(CACHE_DIR, f"scan_{mode}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving {mode} cache to disk: {e}")

# Dual-Cache: Daily Swing and Intraday Momentum
SCAN_CACHE = {
    "daily": {
        "data": load_disk_cache("daily"),
        "last_scanned": None,
        "is_scanning": False
    },
    "intraday": {
        "data": load_disk_cache("intraday"),
        "last_scanned": None,
        "is_scanning": False
    }
}

def background_cache_worker(mode: str):
    """Refreshes cache in background thread without blocking web server."""
    global SCAN_CACHE
    if SCAN_CACHE[mode]["is_scanning"]:
        return
    SCAN_CACHE[mode]["is_scanning"] = True
    try:
        print(f"[{mode.upper()}] Starting background scan across Nifty 500 stocks...")
        data = run_full_scan(mode=mode)
        SCAN_CACHE[mode]["data"] = data
        SCAN_CACHE[mode]["last_scanned"] = datetime.now().isoformat()
        save_disk_cache(mode, data)
        triggers = data.get("total_triggers_found", 0) if data else 0
        print(f"[{mode.upper()}] Background scan complete! {triggers} triggers found.")
    except Exception as e:
        print(f"Error caching {mode} scan: {e}")
    finally:
        SCAN_CACHE[mode]["is_scanning"] = False

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

MARKET_STATUS_CACHE = {
    "data": None,
    "timestamp": 0
}

@app.route("/api/market-status", methods=["GET"])
def api_market_status():
    """Returns live Nifty 50, India VIX, and NSE market trading session status."""
    global MARKET_STATUS_CACHE
    now_ts = time.time()
    if MARKET_STATUS_CACHE["data"] and (now_ts - MARKET_STATUS_CACHE["timestamp"] < 30.0):
        return jsonify(MARKET_STATUS_CACHE["data"])
        
    try:
        from algo_engine import _HTTP_SESSION
        session = _HTTP_SESSION
    except Exception:
        import requests
        session = requests
        
    indices_data = {}
    for sym, key in [('^NSEI', 'nifty'), ('^INDIAVIX', 'vix')]:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
            r = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            q = r.json()["chart"]["result"][0]
            meta = q["meta"]
            price = meta.get("regularMarketPrice", 0.0)
            prev = meta.get("previousClose") or meta.get("chartPreviousClose") or price
            diff = round(price - prev, 2)
            pct = round((diff / prev) * 100, 2) if prev else 0.0
            indices_data[key] = {"price": price, "change": diff, "change_pct": pct}
        except Exception:
            indices_data[key] = {"price": 0.0, "change": 0.0, "change_pct": 0.0}

    # Market Open Status (NSE regular hours: 09:15 - 15:30 IST, Mon-Fri)
    now_utc = datetime.now(timezone.utc)
    ist = now_utc + timedelta(hours=5, minutes=30)
    weekday = ist.weekday()
    market_time = ist.time()
    is_open = (weekday < 5) and (d_time(9, 15) <= market_time <= d_time(15, 30))

    # Market Regime Assessment
    nifty_pct = indices_data.get("nifty", {}).get("change_pct", 0.0)
    vix_val = indices_data.get("vix", {}).get("price", 15.0)
    if nifty_pct >= 0.2 and vix_val < 18.0:
        regime = "BULLISH TRENDING"
        regime_badge = "badge-success"
    elif nifty_pct < -0.5 or vix_val > 21.0:
        regime = "RISK-OFF / VOLATILE"
        regime_badge = "badge-danger"
    else:
        regime = "CONSOLIDATION / NEUTRAL"
        regime_badge = "badge-neutral"

    res = {
        "status": "success",
        "nifty": indices_data.get("nifty", {}),
        "vix": indices_data.get("vix", {}),
        "is_open": is_open,
        "market_status_text": "MARKET OPEN (LIVE)" if is_open else "MARKET CLOSED",
        "market_regime": regime,
        "regime_badge": regime_badge,
        "time_str": ist.strftime("%I:%M %p IST"),
        "date_str": ist.strftime("%d %b %Y")
    }
    MARKET_STATUS_CACHE["data"] = res
    MARKET_STATUS_CACHE["timestamp"] = now_ts
    return jsonify(res)

@app.route("/api/scan", methods=["GET"])
def api_scan():
    """
    Returns scan results with resilient fallback:
    - Never blocks the HTTP worker thread if cached/disk data is available.
    - If user requests force refresh, triggers background scan and immediately returns cached data with is_updating=True.
    """
    mode = request.args.get("mode", "daily").lower()
    if mode not in ["daily", "intraday"]:
        mode = "daily"
        
    force_refresh = request.args.get("refresh", "false").lower() == "true"
    buy_only = request.args.get("buy_only", "true").lower() == "true" if mode == "daily" else False
    days = int(request.args.get("days", 14))
    bars = int(request.args.get("bars", 25))
    
    global SCAN_CACHE
    now_ts = time.time()
    # Cache Max-Age: 5 minutes (300s) for Intraday mode, 30 minutes (1800s) for Daily mode
    max_cache_age_sec = 300.0 if mode == "intraday" else 1800.0

    if not force_refresh:
        # Check in-memory cache and its age
        mem_data = SCAN_CACHE[mode]["data"]
        last_scanned_str = SCAN_CACHE[mode]["last_scanned"]
        is_mem_fresh = False
        if mem_data is not None and last_scanned_str:
            try:
                scanned_dt = datetime.fromisoformat(last_scanned_str)
                age = (datetime.now() - scanned_dt).total_seconds()
                is_mem_fresh = (age < max_cache_age_sec)
            except Exception:
                is_mem_fresh = False

        if is_mem_fresh:
            return jsonify(mem_data)

        # Check disk cache and file age
        disk_data = load_disk_cache(mode)
        if disk_data is not None:
            file_path = os.path.join(CACHE_DIR, f"scan_{mode}.json")
            file_mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
            file_age = now_ts - file_mtime

            # If disk cache is fresh, serve it immediately
            if file_age < max_cache_age_sec:
                SCAN_CACHE[mode]["data"] = disk_data
                SCAN_CACHE[mode]["last_scanned"] = datetime.fromtimestamp(file_mtime).isoformat()
                return jsonify(disk_data)
            
            # If disk cache is expired, serve stale data immediately while auto-refreshing in background
            SCAN_CACHE[mode]["data"] = disk_data
            if not SCAN_CACHE[mode]["is_scanning"]:
                print(f"[{mode.upper()}] Cache expired (age: {file_age/60:.1f} mins). Triggering auto-refresh in background...")
                threading.Thread(target=background_cache_worker, args=(mode,), daemon=True).start()
            res = dict(disk_data)
            res["is_updating"] = True
            return jsonify(res)

        # If cold startup and already scanning, wait up to 10 seconds
        if SCAN_CACHE[mode]["is_scanning"]:
            for _ in range(20):
                time.sleep(0.5)
                if SCAN_CACHE[mode]["data"] is not None:
                    return jsonify(SCAN_CACHE[mode]["data"])
                if not SCAN_CACHE[mode]["is_scanning"]:
                    break
    else:
        # Force refresh requested: trigger background worker without blocking web server
        if not SCAN_CACHE[mode]["is_scanning"]:
            threading.Thread(target=background_cache_worker, args=(mode,), daemon=True).start()
        if SCAN_CACHE[mode]["data"] is not None:
            res = dict(SCAN_CACHE[mode]["data"])
            res["is_updating"] = True
            return jsonify(res)
        
    results = run_full_scan(mode=mode, days_lookback=days, bars_lookback=bars, buy_only=buy_only)
    SCAN_CACHE[mode]["data"] = results
    SCAN_CACHE[mode]["last_scanned"] = datetime.now().isoformat()
    save_disk_cache(mode, results)
    return jsonify(results)

@app.route("/api/universe", methods=["GET"])
def api_get_universe():
    """Returns active dynamic universe information and constituent symbols."""
    active = get_active_universe() if get_active_universe else []
    cached = load_cached_universe() if load_cached_universe else {}
    return jsonify({
        "status": "success",
        "total_stocks": len(active),
        "last_updated": (cached or {}).get("last_updated", datetime.now().isoformat()),
        "top_momentum_leaders": (cached or {}).get("top_momentum_leaders", []),
        "stocks": active
    })

@app.route("/api/universe/refresh", methods=["POST"])
def api_refresh_universe():
    """Triggers dynamic momentum discovery across NSE stocks and refreshes screener."""
    if not refresh_dynamic_momentum_universe:
        return jsonify({"error": "Dynamic universe module not found"}), 500
    
    def worker():
        try:
            print("[UNIVERSE REFRESH] Running dynamic momentum screener across Nifty 500...")
            refresh_dynamic_momentum_universe(top_n=500)
            # Invalidate daily scan cache to re-scan with fresh momentum leaders
            global SCAN_CACHE
            background_cache_worker("daily")
        except Exception as e:
            print(f"Error in background universe refresh: {e}")
            
    threading.Thread(target=worker, daemon=True).start()
    return jsonify({
        "status": "started",
        "message": "Auto-discovery launched in background. Analyzing momentum leaders across NSE stocks and refreshing screener!"
    })

@app.route("/api/stock/<symbol>", methods=["GET"])
def api_stock_chart(symbol):
    """
    Returns candlestick OHLCV and indicator data for the interactive chart.
    Query param `mode`: 'daily' or 'intraday'
    """
    mode = request.args.get("mode", "daily").lower()
    if mode not in ["daily", "intraday"]:
        mode = "daily"
    data = get_chart_data(symbol, mode=mode)
    return jsonify(data)

@app.route("/api/calculate_position", methods=["POST"])
def api_calculate_position():
    """
    Calculates exact risk management position sizing based on:
    - Capital (₹)
    - Max Risk % (default 1.0% for swing, 0.5% for intraday)
    - Entry Price
    - Stop Loss Level
    """
    req = request.get_json() or {}
    capital = float(req.get("capital", 200000))
    risk_pct = float(req.get("risk_pct", 1.0))
    entry_price = float(req.get("entry_price", 1000))
    stop_loss = float(req.get("stop_loss", 960))
    
    max_risk_amount = capital * (risk_pct / 100.0)
    risk_per_share = abs(entry_price - stop_loss)
    
    if risk_per_share <= 0:
        return jsonify({"error": "Stop loss cannot be identical to entry price"}), 400
        
    shares = int(max_risk_amount // risk_per_share)
    total_investment = round(shares * entry_price, 2)
    position_pct_of_capital = round((total_investment / capital) * 100.0, 2)
    
    target1 = round(entry_price + (1.5 * risk_per_share if entry_price > stop_loss else -1.5 * risk_per_share), 2)
    target2 = round(entry_price + (2.5 * risk_per_share if entry_price > stop_loss else -2.5 * risk_per_share), 2)
    potential_profit_t1 = round(shares * abs(target1 - entry_price), 2)
    potential_profit_t2 = round(shares * abs(target2 - entry_price), 2)
    
    return jsonify({
        "capital": capital,
        "risk_pct": risk_pct,
        "max_risk_amount": round(max_risk_amount, 2),
        "shares_to_buy": shares,
        "total_investment": total_investment,
        "portfolio_allocation_pct": position_pct_of_capital,
        "risk_per_share": round(risk_per_share, 2),
        "target1": target1,
        "target2": target2,
        "profit_target1": potential_profit_t1,
        "profit_target2": potential_profit_t2,
        "reward_risk_ratio": "1 : 1.5 (T1) / 2.5 (T2)"
    })

@app.route("/api/export_csv", methods=["GET"])
def api_export_csv():
    """Exports current scan results to CSV."""
    mode = request.args.get("mode", "daily").lower()
    if mode not in ["daily", "intraday"]:
        mode = "daily"
        
    global SCAN_CACHE
    if SCAN_CACHE[mode]["data"] is None:
        SCAN_CACHE[mode]["data"] = run_full_scan(mode=mode)
        
    signals = SCAN_CACHE[mode]["data"].get("signals", [])
    output = io.StringIO()
    writer = csv.writer(output)
    
    ema_label = "50 EMA (Daily)" if mode == "daily" else "200 EMA (Intraday)"
    time_label = "Trigger Date" if mode == "daily" else "Trigger Bar Time"
    
    writer.writerow([
        "Symbol", "Company Name", "Sector", "Strategy Mode", "Signal", "Age", time_label, 
        "Trigger Price (₹)", "Current Price (₹)", "% Move", ema_label, "Supertrend (10,3)", 
        "Stop Loss (₹)", "Risk %", "Target 1 (₹)", "Target 2 (₹)", "Suitability Verdict", "Reason", "Action Plan"
    ])
    
    for s in signals:
        writer.writerow([
            s["symbol"], s["name"], s["sector"], mode.upper(), s["signal_type"], 
            f"{s['days_ago']}d" if mode == "daily" else f"{s['bars_ago']} bars", s["trigger_date"],
            s["trigger_price"], s["current_price"], s["pct_from_trigger"], s["main_ema"], s["supertrend"],
            s["stop_loss"], s["risk_pct"], s["target1"], s["target2"], s["suitability"], 
            s["reasons"][0] if s["reasons"] else "", s["action_plan"]
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=nse_{mode}_algo_signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"}
    )

@app.route("/api/tracker", methods=["GET"])
def api_tracker():
    """
    Returns historical signal performance audit data.
    Query param `mode`: 'intraday' (last 7 days) or 'swing' (last 3 months)
    """
    mode = request.args.get("mode", "intraday").lower()
    if mode not in ["intraday", "swing"]:
        mode = "intraday"
        
    summary_path = os.path.join(CACHE_DIR, "tracker_summary.json")
    trades_path = os.path.join(CACHE_DIR, f"tracker_{mode}_{'7d' if mode=='intraday' else '3m'}.json")
    
    summary = {}
    trades = []
    
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                full_summary = json.load(f)
                summary = full_summary.get(mode, {})
        except Exception as e:
            print(f"Error loading tracker summary: {e}")
            
    if os.path.exists(trades_path):
        try:
            with open(trades_path, "r", encoding="utf-8") as f:
                trades = json.load(f)
        except Exception as e:
            print(f"Error loading tracker trades: {e}")
            
    return jsonify({
        "status": "success",
        "mode": mode,
        "summary": summary,
        "total_trades_count": len(trades),
        "trades": trades
    })

# ==============================================================================
# PRO SWING TRADER PORTFOLIO & REAL-TIME ANALYZER ENDPOINTS
# ==============================================================================

@app.route("/api/portfolios", methods=["GET"])
def api_list_portfolios():
    """Lists metadata for all user portfolios and which one is active."""
    return jsonify(get_all_portfolios_meta())

@app.route("/api/portfolios", methods=["POST"])
def api_create_portfolio():
    """Creates a new user portfolio."""
    req = request.get_json() or {}
    name = req.get("name", "").strip()
    capital = float(req.get("total_capital", 500000.0))
    risk_pct = float(req.get("max_risk_pct", 1.0))
    res = create_new_portfolio(name, capital, risk_pct)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route("/api/portfolios/<portfolio_id>", methods=["PUT"])
def api_update_portfolio(portfolio_id):
    """Updates portfolio name, capital, or risk limit."""
    req = request.get_json() or {}
    name = req.get("name")
    capital = req.get("total_capital")
    risk_pct = req.get("max_risk_pct")
    res = update_portfolio_meta(portfolio_id, name, capital, risk_pct)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route("/api/portfolios/<portfolio_id>", methods=["DELETE"])
def api_delete_portfolio(portfolio_id):
    """Deletes a portfolio if there are at least two portfolios."""
    res = delete_user_portfolio(portfolio_id)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route("/api/portfolios/switch", methods=["POST"])
def api_switch_portfolio():
    """Switches the active portfolio."""
    req = request.get_json() or {}
    portfolio_id = req.get("portfolio_id")
    if not portfolio_id:
        return jsonify({"error": "Portfolio ID is required"}), 400
    res = switch_active_portfolio(portfolio_id)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route("/api/portfolio", methods=["GET"])
def api_get_portfolio():
    """Returns real-time analysis of entire portfolio & watchlist."""
    force = request.args.get("refresh", "false").lower() == "true"
    portfolio_id = request.args.get("portfolio_id")
    result = analyze_entire_portfolio(portfolio_id=portfolio_id, force_refresh=force)
    return jsonify(result)

@app.route("/api/portfolio/analyze", methods=["GET"])
def api_analyze_stock():
    """
    On-demand analysis for any custom symbol (even before adding to portfolio).
    Query params: symbol, is_bought (true/false), buy_price, quantity, buy_date, initial_sl
    """
    symbol = request.args.get("symbol", "").strip()
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
        
    is_bought = request.args.get("is_bought", "false").lower() == "true"
    buy_price = float(request.args.get("buy_price", 0.0)) if request.args.get("buy_price") else None
    quantity = int(request.args.get("quantity", 0)) if request.args.get("quantity") else 0
    buy_date = request.args.get("buy_date", "")
    initial_sl = float(request.args.get("initial_sl", 0.0)) if request.args.get("initial_sl") else None
    target1 = float(request.args.get("target1", 0.0)) if request.args.get("target1") else None
    target2 = float(request.args.get("target2", 0.0)) if request.args.get("target2") else None
    target3 = float(request.args.get("target3", 0.0)) if request.args.get("target3") else None
    target4 = float(request.args.get("target4", 0.0)) if request.args.get("target4") else None
    
    result = analyze_single_stock(
        symbol=symbol,
        is_bought=is_bought,
        buy_price=buy_price,
        quantity=quantity,
        buy_date=buy_date,
        initial_sl=initial_sl,
        target1=target1,
        target2=target2,
        target3=target3,
        target4=target4
    )
    return jsonify(result)

@app.route("/api/portfolio/item", methods=["POST"])
def api_add_portfolio_item():
    """Adds a holding or watchlist item."""
    req = request.get_json() or {}
    item_type = req.get("type", "holding")
    item_data = req.get("data", {})
    portfolio_id = req.get("portfolio_id") or request.args.get("portfolio_id")
    if not item_data.get("symbol"):
        return jsonify({"error": "Symbol is required"}), 400
        
    res = add_portfolio_item(item_type, item_data, portfolio_id=portfolio_id)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route("/api/portfolio/item", methods=["PUT"])
def api_update_portfolio_item():
    """Updates a holding or watchlist item."""
    req = request.get_json() or {}
    item_type = req.get("type", "holding")
    item_id = req.get("id")
    item_data = req.get("data", {})
    portfolio_id = req.get("portfolio_id") or request.args.get("portfolio_id")
    if not item_id:
        return jsonify({"error": "Item ID is required"}), 400
        
    res = update_portfolio_item(item_type, item_id, item_data, portfolio_id=portfolio_id)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route("/api/portfolio/item", methods=["DELETE"])
def api_delete_portfolio_item():
    """Deletes an item upon user confirmation."""
    item_type = request.args.get("type", "holding")
    item_id = request.args.get("id")
    portfolio_id = request.args.get("portfolio_id")
    if not item_id:
        return jsonify({"error": "Item ID is required"}), 400
        
    res = delete_portfolio_item(item_type, item_id, portfolio_id=portfolio_id)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route("/api/portfolio/close_trade", methods=["POST"])
def api_close_trade():
    """Exits a holding and logs it into the historical Trade Journal."""
    req = request.get_json() or {}
    item_id = req.get("id")
    exit_price = float(req.get("exit_price", 0.0))
    exit_date = req.get("exit_date")
    exit_reason = req.get("exit_reason", "")
    hold_days = req.get("hold_days")
    portfolio_id = req.get("portfolio_id") or request.args.get("portfolio_id")
    if hold_days is not None and str(hold_days).strip() != "":
        try:
            hold_days = int(hold_days)
        except ValueError:
            hold_days = None
    else:
        hold_days = None
    
    if not item_id or exit_price <= 0:
        return jsonify({"error": "Valid Item ID and Exit Price are required"}), 400
        
    res = close_trade_and_log(item_id, exit_price, exit_date, exit_reason, hold_days=hold_days, portfolio_id=portfolio_id)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route("/api/portfolio/export_history_csv", methods=["GET"])
def api_export_history_csv():
    """Exports the closed trades journal of the specified portfolio to CSV for audit and methodology study."""
    data = load_portfolio_data()
    portfolio_id = request.args.get("portfolio_id")
    target_p, _ = get_portfolio_by_id(data, portfolio_id)
    if not target_p:
        return jsonify({"error": "Portfolio not found"}), 404

    history = target_p.get("history", [])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Symbol", "Company Name", "Buy Date", "Exit Date", "Hold Duration (Days)",
        "Buy Price (₹)", "Exit Price (₹)", "Quantity", "Realized P&L (₹)",
        "Return %", "Outcome", "Exit Reason", "Notes"
    ])
    for t in history:
        writer.writerow([
            t.get("symbol", ""),
            t.get("name", ""),
            t.get("buy_date", ""),
            t.get("exit_date", ""),
            t.get("hold_days", 0),
            t.get("buy_price", 0.0),
            t.get("exit_price", 0.0),
            t.get("quantity", 0),
            t.get("realized_pnl", 0.0),
            t.get("return_pct", 0.0),
            "WIN" if t.get("is_win", False) else "LOSS",
            t.get("exit_reason", ""),
            t.get("notes", "")
        ])

    output.seek(0)
    p_name = target_p.get("name", "portfolio").replace(" ", "_").lower()
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=trade_history_{p_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"}
    )

def get_free_port(default_port=5000):
    """Finds an available port if the default port is occupied by another application."""
    if os.environ.get("PORT"):
        return int(os.environ.get("PORT"))
    import socket
    for p in [default_port, 5001, 5002, 5005, 8080]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", p))
                return p
            except OSError:
                continue
    return default_port

if __name__ == "__main__":
    port = get_free_port(5000)
    
    # Save active port info to disk for tools and batch scripts
    try:
        with open(os.path.join(CACHE_DIR, "server_info.json"), "w", encoding="utf-8") as f:
            json.dump({"port": port, "url": f"http://localhost:{port}"}, f)
    except Exception:
        pass

    print("=" * 70)
    print("  AlgoQuant India Web Server - NSE Nifty 500 Algorithmic Screener")
    print("=" * 70)
    if port != 5000:
        print(f"[PORT NOTICE] Port 5000 is currently in use by another app.")
        print(f"[PORT NOTICE] Running AlgoQuant India on port {port} -> http://localhost:{port}")
    else:
        print(f"Server starting on http://localhost:{port} ...")
    
    # Pre-warm Daily and Intraday scans concurrently in background threads
    print("[1/2] Launching Daily 50 EMA scan across Nifty 500 stocks in background...")
    threading.Thread(target=background_cache_worker, args=("daily",), daemon=True).start()
    
    print("[2/2] Launching Intraday 200 EMA scan in background...")
    threading.Thread(target=background_cache_worker, args=("intraday",), daemon=True).start()
    
    print(f"\nServer ready! Open in browser: http://localhost:{port}")
    print("Press Ctrl+C in this console window anytime to stop the server.\n")
    
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

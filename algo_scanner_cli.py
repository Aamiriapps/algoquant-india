import sys
import argparse
from algo_engine import run_full_scan

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Terminal ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_banner(mode: str):
    print(f"{CYAN}{BOLD}")
    print("=" * 86)
    if mode == "daily":
        print("      ALGOQUANT INDIA - NSE NIFTY 500 MARKET CAP COMPANIES (DAILY SWING)")
        print("         Strategy: Price vs 50 EMA & Supertrend (10, 3) | Lookback: 7 Days")
    else:
        print("      ALGOQUANT INDIA - NSE NIFTY 500 MARKET CAP COMPANIES (INTRADAY MOMENTUM)")
        print("       Strategy: 15m Price vs 200 EMA & Supertrend (10, 3) | Live Intraday Bars")
    print("=" * 86)
    print(f"{RESET}")

def main():
    parser = argparse.ArgumentParser(description="NSE Nifty 500 Companies Algo Screener (Daily & Intraday)")
    parser.add_argument("--mode", type=str, choices=["daily", "intraday"], default="daily", help="Strategy Mode: daily or intraday (default: daily)")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days for Daily mode (default: 7)")
    parser.add_argument("--bars", type=int, default=25, help="Lookback bars for Intraday mode (default: 25 bars)")
    parser.add_argument("--actionable", action="store_true", help="Show actionable entries only")
    parser.add_argument("--enhanced", action="store_true", help="Show Enhanced Pro Algo setups only")
    args = parser.parse_args()

    print_banner(args.mode)
    print(f"[*] Scanning Nifty 500 Indian Stocks (Mode: {args.mode.upper()})...")
    res = run_full_scan(mode=args.mode, days_lookback=args.days, bars_lookback=args.bars)

    print(f"{GREEN}[✓] Scan complete in {res['scan_duration_sec']}s{RESET}")
    print(f"    Total Stocks Scanned: {res['total_scanned_stocks']} (Nifty 500 Universe)")
    print(f"    Triggers Found: {res['total_triggers_found']}")
    print(f"    Actionable Buys: {res['summary']['actionable_buys']} | Actionable Sells: {res['summary']['actionable_sells']}")
    print(f"    Not Suitable (Avoid): {res['summary']['not_suitable']} | Pro Enhanced Picks: {res['summary']['pro_enhanced_picks']}\n")

    signals = res["signals"]
    if args.actionable:
        signals = [s for s in signals if s["is_actionable"]]
    if args.enhanced:
        signals = [s for s in signals if s["enhanced_option"]["vol_confirmed"]]

    if not signals:
        print(f"{YELLOW}No signals found matching the specified filters.{RESET}")
        return

    actionable = [s for s in signals if s["is_actionable"]]
    not_suitable = [s for s in signals if not s["is_actionable"]]

    age_label = "Triggered"

    if actionable:
        print(f"{GREEN}{BOLD}=== [1] ACTIONABLE ENTRIES (You still have the option to enter) ==={RESET}")
        for s in actionable:
            sig_col = GREEN if s["signal_type"] == "BUY" else RED
            age_str = f"{s['days_ago']}d ago" if args.mode == "daily" else f"{s['bars_ago']} bars ago ({s['days_ago']}h)"
            if args.mode == "daily" and s["days_ago"] == 0:
                age_str = "TODAY (FRESH)"
            elif args.mode == "intraday" and s["bars_ago"] <= 1:
                age_str = "LIVE SESSION / JUST NOW"

            print(f"\n{sig_col}{BOLD}▶ [{s['signal_type']}] {s['symbol']} - {s['name']}{RESET} ({s['sector']})")
            print(f"   {age_label}: {age_str} ({s['trigger_date']}) @ Rs.{s['trigger_price']} | Current Price: Rs.{s['current_price']} ({s['pct_from_trigger']:+.2f}%)")
            print(f"   {s['main_ema_name']}: Rs.{s['main_ema']} | Supertrend (10,3): Rs.{s['supertrend']}")
            print(f"   {GREEN}Risk Management:{RESET} Stop-Loss: Rs.{s['stop_loss']} (-{s['risk_pct']}%) | Target 1: Rs.{s['target1']} | Target 2: Rs.{s['target2']}")
            print(f"   {CYAN}Verdict:{RESET} {BOLD}{s['suitability']}{RESET}")
            print(f"   {BOLD}Action Plan:{RESET} {s['action_plan']}")
            if s['enhanced_option']['vol_confirmed']:
                print(f"   {MAGENTA}★ Pro Algo Score: {s['enhanced_option']['pro_score']} (Volume Surge + RSI Corridor){RESET}")

    if not_suitable and not args.actionable:
        print(f"\n{YELLOW}{BOLD}=== [2] NOT SUITABLE (Do NOT Enter / Overextended / Invalidated) ==={RESET}")
        for s in not_suitable[:15]: # Show top 15 unsuitable to avoid terminal flood
            sig_col = GREEN if s["signal_type"] == "BUY" else RED
            age_str = f"{s['days_ago']}d ago" if args.mode == "daily" else f"{s['bars_ago']} bars ago"
            print(f"\n{sig_col}[{s['signal_type']}]{RESET} {BOLD}{s['symbol']}{RESET} | Age: {age_str} @ Rs.{s['trigger_price']} -> Current: Rs.{s['current_price']} ({s['pct_from_trigger']:+.2f}%)")
            print(f"   {YELLOW}Verdict:{RESET} {s['suitability']}")
            print(f"   {RED}Reason:{RESET} {s['reasons'][0]}")
            print(f"   Guidance: {s['action_plan']}")

    print("\n" + "=" * 86)
    print(f"Tip: Open the Web Dashboard by running {CYAN}python server.py{RESET} and browsing to {CYAN}http://localhost:5000{RESET}")
    print(f"To run Intraday Screener in CLI: {CYAN}python algo_scanner_cli.py --mode intraday --actionable{RESET}")
    print("=" * 86 + "\n")

if __name__ == "__main__":
    main()

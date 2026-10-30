import json
import uuid
from datetime import datetime, date
from portfolio_manager import analyze_single_stock, load_portfolio_data, save_portfolio_data

user_portfolio = [
    {"symbol": "ACC", "quantity": 40, "buy_price": 1365.70, "name": "ACC Ltd"},
    {"symbol": "DABUR", "quantity": 120, "buy_price": 425.00, "name": "Dabur India Ltd"},
    {"symbol": "RELIANCE", "quantity": 21, "buy_price": 1313.00, "name": "Reliance Industries Ltd"},
    {"symbol": "HCLTECH", "quantity": 41, "buy_price": 1237.00, "name": "HCL Technologies Ltd"},
    {"symbol": "HDFCBANK", "quantity": 64, "buy_price": 785.00, "name": "HDFC Bank Ltd"},
    {"symbol": "HDFCLIFE", "quantity": 100, "buy_price": 551.80, "name": "HDFC Life Insurance Co"},
    {"symbol": "HINDUNILVR", "quantity": 25, "buy_price": 2121.00, "name": "Hindustan Unilever Ltd"},
    {"symbol": "ICICIGI", "quantity": 30, "buy_price": 1651.50, "name": "ICICI Lombard General Insurance"},
    {"symbol": "INFY", "quantity": 57, "buy_price": 1255.78, "name": "Infosys Ltd"},
    {"symbol": "BANKBARODA", "quantity": 360, "buy_price": 242.00, "name": "Bank of Baroda"},
    {"symbol": "LTIM", "quantity": 19, "buy_price": 4416.00, "name": "LTIMindtree Ltd"},
    {"symbol": "SBICARD", "quantity": 90, "buy_price": 671.00, "name": "SBI Cards and Payment Services"},
    {"symbol": "SUZLON", "quantity": 986, "buy_price": 55.08, "name": "Suzlon Energy Ltd"},
    {"symbol": "TCS", "quantity": 32, "buy_price": 2624.62, "name": "Tata Consultancy Services"},
    {"symbol": "LTTS", "quantity": 13, "buy_price": 3587.42, "name": "L&T Technology Services"},
]

print(f"Loading and analyzing {len(user_portfolio)} holdings...")
analyzed_holdings = []
holdings_to_save = []

for item in user_portfolio:
    sym = item["symbol"]
    qty = item["quantity"]
    bp = item["buy_price"]
    
    analysis = analyze_single_stock(sym, is_bought=True, buy_price=bp, quantity=qty)
    analyzed_holdings.append(analysis)
    
    holdings_to_save.append({
        "id": str(uuid.uuid4())[:8],
        "symbol": sym,
        "name": analysis.get("name", item["name"]),
        "sector": analysis.get("sector", "Equities"),
        "buy_price": bp,
        "quantity": qty,
        "buy_date": "2026-10-22",
        "initial_sl": analysis.get("trailing_sl"),
        "target1": analysis.get("price_action_high"),
        "target2": analysis.get("high_52w"),
        "notes": f"Swing Portfolio Holding ({qty} shares @ ₹{bp})",
        "created_at": datetime.now().isoformat()
    })

# Save directly to persistent portfolio JSON
data = load_portfolio_data()
data["holdings"] = holdings_to_save
save_portfolio_data(data)

# Save analysis report for presentation
with open("user_portfolio_analysis.json", "w", encoding="utf-8") as f:
    json.dump(analyzed_holdings, f, indent=2)

print("SUCCESS: Portfolio saved and analyzed successfully!")

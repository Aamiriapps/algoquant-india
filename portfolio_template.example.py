"""
Example template for programmatically seeding a portfolio.
Copy this file to a private script or use the web UI to manage your portfolio.
"""
import uuid
from datetime import datetime
from portfolio_manager import analyze_single_stock, load_portfolio_data, save_portfolio_data

# Generic sample holdings (dummy data)
sample_portfolio = [
    {"symbol": "TATASTEEL", "quantity": 100, "buy_price": 140.00, "name": "Tata Steel Ltd"},
    {"symbol": "INFY", "quantity": 50, "buy_price": 1500.00, "name": "Infosys Ltd"},
]

def seed_sample_portfolio():
    print(f"Loading and analyzing {len(sample_portfolio)} sample holdings...")
    holdings_to_save = []

    for item in sample_portfolio:
        sym = item["symbol"]
        qty = item["quantity"]
        bp = item["buy_price"]
        
        analysis = analyze_single_stock(sym, is_bought=True, buy_price=bp, quantity=qty)
        
        holdings_to_save.append({
            "id": str(uuid.uuid4())[:8],
            "symbol": sym,
            "name": analysis.get("name", item["name"]),
            "sector": analysis.get("sector", "Equities"),
            "buy_price": bp,
            "quantity": qty,
            "buy_date": datetime.now().strftime("%Y-%m-%d"),
            "initial_sl": analysis.get("trailing_sl"),
            "target1": analysis.get("price_action_high"),
            "target2": analysis.get("high_52w"),
            "notes": f"Sample Holding ({qty} shares @ ₹{bp})",
            "created_at": datetime.now().isoformat()
        })

    data = load_portfolio_data()
    data["holdings"] = holdings_to_save
    save_portfolio_data(data)
    print("Sample portfolio initialized successfully in local cache/portfolio.json!")

if __name__ == "__main__":
    seed_sample_portfolio()


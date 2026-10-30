import json

with open('user_portfolio_analysis.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

tot_invested = sum(i['invested_capital'] for i in items)
tot_current = sum(i['current_value'] for i in items)
tot_pnl = tot_current - tot_invested
tot_pnl_pct = (tot_pnl / tot_invested) * 100

print(f"TOTAL INVESTED: Rs {tot_invested:,.2f} | CURRENT VALUE: Rs {tot_current:,.2f} | TOTAL P&L: Rs {tot_pnl:,.2f} ({tot_pnl_pct:+.2f}%)")
print("=" * 125)
header = f"{'SYMBOL':<11} | {'QTY':<4} | {'BUY':<8} | {'LTP':<8} | {'PNL%':<7} | {'SUPERTREND':<11} | {'ST-DIR':<8} | {'PA HIGH':<8} | {'ATH':<8} | {'VERDICT'}"
print(header)
print("-" * 125)

for i in items:
    sym = i['symbol']
    qty = i['quantity']
    bp = i['buy_price']
    ltp = i['current_price']
    pnl = i['pnl_pct']
    st = i['supertrend']
    st_b = "BULLISH" if i['supertrend_dir'] == 1 else "SELL"
    pa = i.get('price_action_high', 0)
    ath = i.get('high_52w', 0)
    v = i['exit_verdict']
    print(f"{sym:<11} | {qty:<4} | Rs {bp:<5.1f} | Rs {ltp:<5.1f} | {pnl:>+6.1f}% | Rs {st:<8.1f} | {st_b:<8} | Rs {pa:<5.1f} | Rs {ath:<5.1f} | {v}")

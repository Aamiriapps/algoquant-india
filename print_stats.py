import json

with open('cache/tracker_intraday_7d.json', 'r', encoding='utf-8') as f:
    intra = json.load(f)
with open('cache/tracker_swing_3m.json', 'r', encoding='utf-8') as f:
    swing = json.load(f)

print('=== INTRADAY (7 DAYS) BREAKDOWN ===')
print('Total raw triggers:', len(intra))
intra_actionable = [t for t in intra if t['risk_pct'] <= 2.8]
print('Actionable (Risk <= 2.8%):', len(intra_actionable))
act_wins = [t for t in intra_actionable if t['profit']]
print(f"Actionable Win Rate: {len(act_wins)/len(intra_actionable)*100:.2f}% ({len(act_wins)}/{len(intra_actionable)})")
act_r = sum(t['r_multiple'] for t in intra_actionable)
print(f"Actionable Total R: {act_r:.2f}R | Avg R: {act_r/len(intra_actionable):.2f}R")

print('\n=== SWING (3 MONTHS) BREAKDOWN ===')
print('Total raw triggers:', len(swing))
swing_actionable = [t for t in swing if t['risk_pct'] <= 6.0]
print('Actionable (Risk <= 6.0%):', len(swing_actionable))
if swing_actionable:
    sw_act_wins = [t for t in swing_actionable if t['profit']]
    print(f"Actionable Win Rate: {len(sw_act_wins)/len(swing_actionable)*100:.2f}% ({len(sw_act_wins)}/{len(swing_actionable)})")
    sw_act_r = sum(t['r_multiple'] for t in swing_actionable)
    print(f"Actionable Total R: {sw_act_r:.2f}R | Avg R: {sw_act_r/len(swing_actionable):.2f}R")

# Stock-by-stock consistency
stock_intra_wins = {}
for t in intra:
    sym = t['symbol']
    if sym not in stock_intra_wins: stock_intra_wins[sym] = {'win': 0, 'loss': 0, 'pnl': 0.0, 'name': t['name']}
    if t['profit']: stock_intra_wins[sym]['win'] += 1
    else: stock_intra_wins[sym]['loss'] += 1
    stock_intra_wins[sym]['pnl'] += t['pnl_pct']

top_win_stocks = sorted(stock_intra_wins.items(), key=lambda x: x[1]['pnl'], reverse=True)[:10]
worst_loss_stocks = sorted(stock_intra_wins.items(), key=lambda x: x[1]['pnl'])[:10]
print('\nTop 7 Intraday Stocks by Cumulative PnL:')
for s, d in top_win_stocks[:7]:
    total_st = d['win'] + d['loss']
    wr = (d['win'] / total_st) * 100
    print(f"  {s} ({d['name']}): Wins: {d['win']}, Losses: {d['loss']}, Win Rate: {wr:.1f}%, Net PnL: +{d['pnl']:.2f}%")

print('\nBottom 7 Intraday Stocks by Cumulative PnL (Failed Most):')
for s, d in worst_loss_stocks[:7]:
    total_st = d['win'] + d['loss']
    wr = (d['win'] / total_st) * 100
    print(f"  {s} ({d['name']}): Wins: {d['win']}, Losses: {d['loss']}, Win Rate: {wr:.1f}%, Net PnL: {d['pnl']:.2f}%")

# Swing stock by stock
stock_swing_wins = {}
for t in swing:
    sym = t['symbol']
    if sym not in stock_swing_wins: stock_swing_wins[sym] = {'win': 0, 'loss': 0, 'pnl': 0.0, 't1': 0, 't2': 0, 'sl': 0, 'name': t['name']}
    if t['profit']: stock_swing_wins[sym]['win'] += 1
    else: stock_swing_wins[sym]['loss'] += 1
    stock_swing_wins[sym]['pnl'] += t['pnl_pct']
    if 'TARGET 1' in t['outcome']: stock_swing_wins[sym]['t1'] += 1
    if 'TARGET 2' in t['outcome']: stock_swing_wins[sym]['t2'] += 1
    if 'STOP LOSS' in t['outcome']: stock_swing_wins[sym]['sl'] += 1

top_swing_stocks = sorted(stock_swing_wins.items(), key=lambda x: x[1]['pnl'], reverse=True)[:10]
worst_swing_stocks = sorted(stock_swing_wins.items(), key=lambda x: x[1]['pnl'])[:10]
print('\nTop 7 Swing Stocks by Cumulative PnL:')
for s, d in top_swing_stocks[:7]:
    total_st = d['win'] + d['loss']
    wr = (d['win'] / total_st) * 100
    print(f"  {s} ({d['name']}): Wins: {d['win']}, Losses: {d['loss']}, Win Rate: {wr:.1f}%, T1/T2: {d['t1']}/{d['t2']}, Net PnL: +{d['pnl']:.2f}%")

print('\nBottom 7 Swing Stocks by Cumulative PnL (Failed Most):')
for s, d in worst_swing_stocks[:7]:
    total_st = d['win'] + d['loss']
    wr = (d['win'] / total_st) * 100
    print(f"  {s} ({d['name']}): Wins: {d['win']}, Losses: {d['loss']}, Win Rate: {wr:.1f}%, Net PnL: {d['pnl']:.2f}%")

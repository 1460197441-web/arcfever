import sqlite3
conn = sqlite3.connect(r"C:/Users/arcfever/Documents/New project/python/gold_strategy_alert/runtime/gold_strategy.db")
conn.row_factory = sqlite3.Row
minute = conn.execute("SELECT observed_at, price, source FROM minute_prices ORDER BY observed_at DESC LIMIT 1").fetchone()
bar = conn.execute("SELECT start_at, end_at, open, high, low, close FROM bars_5m ORDER BY start_at DESC LIMIT 1").fetchone()
print('MINUTE=', dict(minute) if minute else None)
print('BAR=', dict(bar) if bar else None)

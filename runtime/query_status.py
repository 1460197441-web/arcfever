import sqlite3
conn = sqlite3.connect(r"C:/Users/arcfever/Documents/New project/python/gold_strategy_alert/runtime/gold_strategy.db")
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT phase, has_position, entry_price, current_stop_loss, pending_entry_reason, last_decision_time, consecutive_fetch_failures, fetch_alert_active FROM runtime_state WHERE id = 1").fetchone()
print('RUNTIME=', dict(row) if row else None)
print('MINUTE_LAST5=', [tuple(r) for r in conn.execute("SELECT observed_at, price, source FROM minute_prices ORDER BY observed_at DESC LIMIT 5").fetchall()])
print('BARS_LAST5=', [tuple(r) for r in conn.execute("SELECT start_at, end_at, open, high, low, close, is_complete FROM bars_5m ORDER BY start_at DESC LIMIT 5").fetchall()])
print('EVENTS_LAST8=', [tuple(r) for r in conn.execute("SELECT event_time, event_type, event_key, message FROM events ORDER BY id DESC LIMIT 8").fetchall()])
print('NOTIFY_LAST5=', [tuple(r) for r in conn.execute("SELECT sent_at, title, notification_type, success, simulated_send FROM notifications ORDER BY id DESC LIMIT 5").fetchall()])

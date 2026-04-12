import sqlite3
from pathlib import Path
path = Path(r"C:/Users/arcfever/Documents/New project/python/gold_strategy_alert/runtime/gold_strategy.db")
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row
state = conn.execute("SELECT phase, has_position, position_size_grams, entry_price, current_stop_loss, trailing_active, h_star, cooldown_end_time, last_exit_time, last_exit_reason, pending_entry_signal_time, pending_entry_deadline, pending_entry_stop_price, pending_entry_reason, last_decision_time, consecutive_fetch_failures, fetch_alert_active FROM runtime_state WHERE id = 1").fetchone()
print('STATE=', dict(state) if state else None)
print('LATEST_MINUTE=', conn.execute("SELECT observed_at, price, source FROM minute_prices ORDER BY observed_at DESC LIMIT 1").fetchone())
print('LATEST_BAR=', conn.execute("SELECT start_at, end_at, open, high, low, close, is_complete FROM bars_5m ORDER BY start_at DESC LIMIT 1").fetchone())
print('LAST_EVENTS=', [tuple(r) for r in conn.execute("SELECT event_time, event_type, event_key, message FROM events ORDER BY id DESC LIMIT 8").fetchall()])
print('LAST_NOTIFS=', [tuple(r) for r in conn.execute("SELECT sent_at, title, notification_type, success, simulated_send FROM notifications ORDER BY id DESC LIMIT 5").fetchall()])

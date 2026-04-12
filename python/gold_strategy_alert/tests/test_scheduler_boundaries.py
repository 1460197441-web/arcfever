from __future__ import annotations

from datetime import datetime

from config import default_config
from scheduler import is_decision_boundary, is_in_trading_window


def test_trading_window_allows_0910_and_2230_boundaries() -> None:
    config = default_config()
    assert is_in_trading_window(config, datetime(2026, 3, 23, 9, 10, 0)) is True
    assert is_in_trading_window(config, datetime(2026, 3, 23, 22, 30, 0)) is True


def test_trading_window_rejects_outside_boundary() -> None:
    config = default_config()
    assert is_in_trading_window(config, datetime(2026, 3, 23, 9, 9, 59)) is False
    assert is_in_trading_window(config, datetime(2026, 3, 23, 22, 30, 1)) is False


def test_decision_boundary_is_every_5_minutes_on_zero_second() -> None:
    config = default_config()
    assert is_decision_boundary(config, datetime(2026, 3, 23, 10, 5, 0)) is True
    assert is_decision_boundary(config, datetime(2026, 3, 23, 10, 10, 0)) is True
    assert is_decision_boundary(config, datetime(2026, 3, 23, 10, 6, 0)) is False
    assert is_decision_boundary(config, datetime(2026, 3, 23, 10, 5, 1)) is False

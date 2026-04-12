from __future__ import annotations

from pathlib import Path

from models import DecisionOutput


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_no_magic_threshold_triggering() -> None:
    files = [
        PROJECT_ROOT / "strategy.py",
        PROJECT_ROOT / "config" / "config.example.yaml",
        PROJECT_ROOT / "config.py",
        PROJECT_ROOT / "risk_gate.py",
    ]
    combined = "\n".join(_read(path) for path in files)
    banned_snippets = [
        "atr_entry_low",
        "atr_entry_high",
        "breakout_atr_multiplier",
        "initial_stop_loss_pct",
        "initial_stop_atr_multiplier",
        "trailing_activation_pct",
        "trailing_floor_pct",
        "trailing_drawdown_pct",
        "trailing_atr_multiplier",
        "hard_take_profit_pct",
        "reentry_breakout_atr_multiplier",
        "time_stop_minutes",
        "0.78",
        "0.82",
        "0.88",
        "1.6R",
        "2.2R",
        "0.10%",
    ]
    for snippet in banned_snippets:
        assert snippet not in combined


def test_docs_and_schema_consistency_if_applicable() -> None:
    readme = _read(PROJECT_ROOT / "README.md").lower()
    constraints = _read(PROJECT_ROOT / "docs" / "00_constraints.md").lower()
    spec = _read(PROJECT_ROOT / "docs" / "01_strategy_spec.md").lower()
    architecture = _read(PROJECT_ROOT / "docs" / "02_architecture.md").lower()
    checklist = _read(PROJECT_ROOT / "docs" / "03_acceptance_checklist.md").lower()
    sample_config = _read(PROJECT_ROOT / "config" / "config.example.yaml").lower()

    for text in [readme, constraints, spec, architecture, checklist]:
        assert "confidence" in text
        assert "not" in text

    assert "classic" in readme
    assert "not claimed to be optimal" in readme
    assert "walk-forward" in readme
    assert "parameter sensitivity" in readme
    assert "replay backtest" in readme
    assert "mode a" in readme
    assert "signal_bar_close" in readme
    assert "buy_now" in readme

    assert "atr_period: 14" in sample_config
    assert "bollinger_period: 20" in sample_config
    assert "bollinger_stddev: 2.0" in sample_config
    assert "donchian_entry_period: 20" in sample_config
    assert "donchian_exit_period: 10" in sample_config
    assert "ema_fast_period: 20" in sample_config
    assert "ema_slow_period: 50" in sample_config

    annotation_names = DecisionOutput.__annotations__.keys()
    assert "confidence" in annotation_names

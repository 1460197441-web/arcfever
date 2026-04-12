"""Minimal CLI for running, replaying, and inspecting the gold assist service."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
import json
from pathlib import Path
import sys
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from config import AppConfig, default_config
from data_provider import build_default_market_data_provider
from logger import configure_logging
from main import run_forever, run_once
from notifier import EmailNotifier
from scheduler import ReplayController
from state_store import SQLiteStateStore

try:
    import yaml
except Exception:  # noqa: BLE001
    yaml = None


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


def _merge_dataclass(target: Any, payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        if not hasattr(target, key):
            continue
        current = getattr(target, key)
        if is_dataclass(current) and isinstance(value, dict):
            _merge_dataclass(current, value)
            continue
        if isinstance(current, Path) and isinstance(value, str):
            setattr(target, key, Path(value))
            continue
        if isinstance(current, time) and isinstance(value, str):
            setattr(target, key, time.fromisoformat(value))
            continue
        setattr(target, key, value)


def load_config(config_path: str | None) -> AppConfig:
    config = default_config()
    if not config_path:
        return config
    if yaml is None:
        raise RuntimeError("PyYAML is required to load YAML config files.")
    payload = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("Top-level config must be a mapping.")
    _merge_dataclass(config, payload)
    return config


def _build_runtime(config: AppConfig) -> tuple[SQLiteStateStore, EmailNotifier]:
    configure_logging(config.storage.log_path)
    store = SQLiteStateStore(config.storage.sqlite_path)
    store.initialize()
    notifier = EmailNotifier(config.email)
    notifier.configure_test_mode(
        enable_test_mode=config.runtime.enable_test_mode,
        send_real_email_in_test_mode=config.runtime.send_real_email_in_test_mode,
    )
    return store, notifier


def command_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    store, notifier = _build_runtime(config)
    if config.runtime.run_mode == "replay" and config.runtime.replay_data_path:
        controller = ReplayController.from_csv(Path(config.runtime.replay_data_path), mode=config.runtime.replay_speed)
        if args.once:
            result = run_once(config, store, notifier, replay_controller=controller)
            print(json.dumps(_serialize(result), ensure_ascii=False, indent=2))
            return 0
        run_forever(config, store, notifier, replay_controller=controller)
        return 0
    if args.once:
        result = run_once(config, store, notifier, live_provider=build_default_market_data_provider(config))
        print(json.dumps(_serialize(result), ensure_ascii=False, indent=2))
        return 0
    run_forever(config, store, notifier, live_provider=build_default_market_data_provider(config))
    return 0


def command_replay_backtest(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    config.runtime.run_mode = "replay"
    config.runtime.replay_data_path = args.input
    if args.fast:
        config.runtime.replay_speed = "fast_forward"
    store, notifier = _build_runtime(config)
    controller = ReplayController.from_csv(Path(args.input), mode=config.runtime.replay_speed)
    while controller.cursor < len(controller.ticks):
        run_once(config, store, notifier, replay_controller=controller)
        if controller.mode == "step":
            break
    decisions = store.load_recent_decisions(limit=20)
    print(json.dumps([decision.as_json_dict() for decision in decisions], ensure_ascii=False, indent=2))
    return 0


def command_signal_replay(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    store, _ = _build_runtime(config)
    decision = store.load_decision_by_id(args.signal_id)
    if decision is None:
        raise SystemExit(f"Decision {args.signal_id} not found.")
    print(json.dumps(decision.as_json_dict(), ensure_ascii=False, indent=2))
    return 0


def command_show_config(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    print(json.dumps(_serialize(config), ensure_ascii=False, indent=2))
    return 0


def command_walk_forward(args: argparse.Namespace) -> int:
    payload = {
        "command": "walk-forward",
        "status": "reserved_entry_point",
        "message": "Walk-forward remains a reserved research entry point. The production service keeps the hook visible but does not ship a full research harness yet.",
        "config": args.config,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_parameter_scan(args: argparse.Namespace) -> int:
    payload = {
        "command": "parameter-scan",
        "status": "reserved_entry_point",
        "message": "Parameter sensitivity analysis remains a reserved research entry point. Use replay-backtest today and extend this hook with your research harness.",
        "config": args.config,
        "input": args.input,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gold_strategy_alert")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", default=None)
    run_parser.add_argument("--once", action="store_true")
    run_parser.set_defaults(func=command_run)

    replay_parser = subparsers.add_parser("replay-backtest")
    replay_parser.add_argument("--config", default=None)
    replay_parser.add_argument("--input", required=True)
    replay_parser.add_argument("--fast", action="store_true")
    replay_parser.set_defaults(func=command_replay_backtest)

    signal_parser = subparsers.add_parser("signal-replay")
    signal_parser.add_argument("--config", default=None)
    signal_parser.add_argument("--signal-id", type=int, required=True)
    signal_parser.set_defaults(func=command_signal_replay)

    walk_parser = subparsers.add_parser("walk-forward")
    walk_parser.add_argument("--config", default=None)
    walk_parser.set_defaults(func=command_walk_forward)

    parameter_scan_parser = subparsers.add_parser("parameter-scan")
    parameter_scan_parser.add_argument("--config", default=None)
    parameter_scan_parser.add_argument("--input", default=None)
    parameter_scan_parser.set_defaults(func=command_parameter_scan)

    show_parser = subparsers.add_parser("show-config")
    show_parser.add_argument("--config", default=None)
    show_parser.set_defaults(func=command_show_config)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))

#!/usr/bin/env python3
"""Gold price monitor with strategy-based email alerts."""

from __future__ import annotations

import argparse
import json
import re
import smtplib
import ssl
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import requests


@dataclass
class PriceSnapshot:
    price: float
    symbol: str
    currency: str
    fetched_at: datetime
    source_name: str
    raw: dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def extract_json_path(payload: Any, path: str) -> Any:
    current = payload
    for segment in path.split("."):
        if isinstance(current, list):
            current = current[int(segment)]
        else:
            current = current[segment]
    return current


def fetch_price(config: dict[str, Any]) -> PriceSnapshot:
    market_data = config["market_data"]
    provider = market_data["provider"]
    timeout_seconds = market_data.get("timeout_seconds", 10)

    if provider == "goldapi":
        base_url = market_data.get("base_url", "https://www.goldapi.io/api")
        symbol = market_data.get("symbol", "XAU")
        currency = market_data.get("currency", "USD")
        token = market_data["api_key"]
        response = requests.get(
            f"{base_url.rstrip('/')}/{symbol}/{currency}",
            headers={
                "x-access-token": token,
                "Content-Type": "application/json",
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return PriceSnapshot(
            price=float(payload["price"]),
            symbol=symbol,
            currency=currency,
            fetched_at=utc_now(),
            source_name="goldapi",
            raw=payload,
        )

    if provider == "generic_json":
        response = requests.get(
            market_data["url"],
            headers=market_data.get("headers"),
            params=market_data.get("params"),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        symbol = market_data.get("symbol", "XAU")
        currency = market_data.get("currency", "USD")
        value = extract_json_path(payload, market_data["json_path"])
        multiplier = float(market_data.get("value_multiplier", 1.0))
        return PriceSnapshot(
            price=float(value) * multiplier,
            symbol=symbol,
            currency=currency,
            fetched_at=utc_now(),
            source_name=market_data.get("source_name", "generic_json"),
            raw=payload,
        )

    if provider == "html_regex":
        headers = {
            "User-Agent": market_data.get(
                "user_agent",
                (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
            )
        }
        extra_headers = market_data.get("headers", {})
        headers.update(extra_headers)
        response = requests.get(
            market_data["url"],
            headers=headers,
            params=market_data.get("params"),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        html = response.text
        pattern = market_data["price_regex"]
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Could not extract gold price from webpage with provided regex.")

        raw_value = match.group(1)
        normalized_value = raw_value.replace(",", "")
        symbol = market_data.get("symbol", "XAU")
        currency = market_data.get("currency", "USD")
        multiplier = float(market_data.get("value_multiplier", 1.0))
        return PriceSnapshot(
            price=float(normalized_value) * multiplier,
            symbol=symbol,
            currency=currency,
            fetched_at=utc_now(),
            source_name=market_data.get("source_name", "html_regex"),
            raw={"matched_value": raw_value, "url": market_data["url"]},
        )

    raise ValueError(f"Unsupported market_data.provider: {provider}")


def matches_direction(value: float, direction: str) -> bool:
    if direction == "either":
        return True
    if direction == "up":
        return value > 0
    if direction == "down":
        return value < 0
    raise ValueError(f"Unsupported direction: {direction}")


def evaluate_strategies(
    config: dict[str, Any],
    snapshot: PriceSnapshot,
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    strategies = config.get("strategies", [])
    last_price = state.get("last_price")
    triggers: list[dict[str, Any]] = []

    for strategy in strategies:
        strategy_type = strategy["type"]
        name = strategy.get("name", strategy_type)

        if strategy_type == "price_above":
            threshold = float(strategy["threshold"])
            if snapshot.price >= threshold:
                triggers.append(
                    {
                        "name": name,
                        "message": f"Current gold price {snapshot.price:.2f} >= {threshold:.2f}",
                        "key": f"{name}:{strategy_type}",
                    }
                )
            continue

        if strategy_type == "price_below":
            threshold = float(strategy["threshold"])
            if snapshot.price <= threshold:
                triggers.append(
                    {
                        "name": name,
                        "message": f"Current gold price {snapshot.price:.2f} <= {threshold:.2f}",
                        "key": f"{name}:{strategy_type}",
                    }
                )
            continue

        if strategy_type == "change_percent":
            if last_price is None:
                continue

            change_percent = ((snapshot.price - float(last_price)) / float(last_price)) * 100
            threshold = float(strategy["threshold"])
            direction = strategy.get("direction", "either")

            if abs(change_percent) >= threshold and matches_direction(change_percent, direction):
                triggers.append(
                    {
                        "name": name,
                        "message": (
                            f"Compared with previous price {float(last_price):.2f}, "
                            f"change is {change_percent:.2f}% and reached threshold {threshold:.2f}%"
                        ),
                        "key": f"{name}:{strategy_type}:{direction}",
                    }
                )
            continue

        raise ValueError(f"Unsupported strategy type: {strategy_type}")

    return triggers


def filter_by_cooldown(
    config: dict[str, Any],
    triggers: list[dict[str, Any]],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    alert_config = config.get("alert", {})
    cooldown_minutes = int(alert_config.get("cooldown_minutes", 30))
    last_alert_at = parse_datetime(state.get("last_alert_at"))
    last_alert_keys = set(state.get("last_alert_keys", []))

    if last_alert_at is None:
        return triggers

    if utc_now() - last_alert_at >= timedelta(minutes=cooldown_minutes):
        return triggers

    return [trigger for trigger in triggers if trigger["key"] not in last_alert_keys]


def build_email(config: dict[str, Any], snapshot: PriceSnapshot, triggers: list[dict[str, Any]]) -> EmailMessage:
    email_config = config["email"]
    subject = email_config.get(
        "subject_template",
        "Gold alert: {symbol}/{currency} {price:.2f}",
    ).format(symbol=snapshot.symbol, currency=snapshot.currency, price=snapshot.price)

    lines = [
        "Gold price alert triggered.",
        "",
        f"Instrument: {snapshot.symbol}/{snapshot.currency}",
        f"Current price: {snapshot.price:.2f}",
        f"Fetched at (UTC): {snapshot.fetched_at.isoformat()}",
        f"Source: {snapshot.source_name}",
        "",
        "Triggered strategies:",
    ]
    lines.extend(f"- {trigger['name']}: {trigger['message']}" for trigger in triggers)
    lines.extend(
        [
            "",
            "To reduce email frequency, increase cooldown_minutes or raise the strategy threshold.",
        ]
    )

    message = EmailMessage()
    message["From"] = email_config["username"]
    message["To"] = ", ".join(email_config["to"])
    message["Subject"] = subject
    message.set_content("\n".join(lines))
    return message


def send_email(config: dict[str, Any], message: EmailMessage) -> None:
    email_config = config["email"]
    host = email_config["smtp_host"]
    port = int(email_config["smtp_port"])
    username = email_config["username"]
    password = email_config["password"]
    use_ssl = bool(email_config.get("use_ssl", True))

    if use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(username, password)
            server.send_message(message)
        return

    with smtplib.SMTP(host, port) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(username, password)
        server.send_message(message)


def update_state(state_path: Path, snapshot: PriceSnapshot, sent_triggers: list[dict[str, Any]]) -> None:
    payload = {
        "last_price": snapshot.price,
        "last_seen_at": snapshot.fetched_at.isoformat(),
        "last_alert_at": utc_now().isoformat() if sent_triggers else None,
        "last_alert_keys": [trigger["key"] for trigger in sent_triggers],
    }

    if state_path.exists():
        existing = load_json(state_path)
        existing.update({k: v for k, v in payload.items() if v is not None})
        if not sent_triggers:
            existing["last_alert_keys"] = existing.get("last_alert_keys", [])
        save_json(state_path, existing)
        return

    if not sent_triggers:
        payload["last_alert_keys"] = []
    save_json(state_path, payload)


def run_once(config_path: Path, test_email_only: bool = False) -> int:
    config = load_json(config_path)
    state_path = config_path.parent / config.get("state_file", "state.json")
    state = load_json(state_path) if state_path.exists() else {}

    if test_email_only:
        snapshot = PriceSnapshot(
            price=0.0,
            symbol=config["market_data"].get("symbol", "XAU"),
            currency=config["market_data"].get("currency", "USD"),
            fetched_at=utc_now(),
            source_name="test",
            raw={},
        )
        message = build_email(
            config,
            snapshot,
            [{"name": "Test email", "message": "This is a test notification.", "key": "test"}],
        )
        send_email(config, message)
        print("Test email sent.")
        return 0

    snapshot = fetch_price(config)
    triggers = evaluate_strategies(config, snapshot, state)
    filtered_triggers = filter_by_cooldown(config, triggers, state)

    if filtered_triggers:
        message = build_email(config, snapshot, filtered_triggers)
        send_email(config, message)
        print(
            f"[{snapshot.fetched_at.isoformat()}] Alert sent for "
            f"{snapshot.symbol}/{snapshot.currency} at {snapshot.price:.2f}"
        )
        update_state(state_path, snapshot, filtered_triggers)
        return 0

    print(
        f"[{snapshot.fetched_at.isoformat()}] No alert. "
        f"{snapshot.symbol}/{snapshot.currency}={snapshot.price:.2f}"
    )
    update_state(state_path, snapshot, [])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gold price monitor")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON file",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one polling cycle and exit",
    )
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Only send a test email and exit",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    interval_seconds = int(config.get("poll_interval_seconds", 60))

    if args.once or args.test_email:
        return run_once(config_path, test_email_only=args.test_email)

    while True:
        try:
            run_once(config_path)
        except KeyboardInterrupt:
            print("Stopped by user.")
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"Run failed: {exc}", file=sys.stderr)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())

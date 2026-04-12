"""Runtime scheduling, session-mode behavior, and replay helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from config import AppConfig
from models import PriceTick


@dataclass(slots=True)
class RuntimeClock:
    timezone_name: str

    def now(self) -> datetime:
        try:
            return datetime.now(ZoneInfo(self.timezone_name))
        except ZoneInfoNotFoundError:
            return datetime.now()


def is_in_trading_window(config: AppConfig, now: datetime) -> bool:
    local_time = now.timetz().replace(tzinfo=None)
    return config.trading_window.start <= local_time <= config.trading_window.end


def is_decision_boundary(config: AppConfig, now: datetime) -> bool:
    return now.minute % config.sampling.decision_interval_minutes == 0 and now.second == 0


def next_sample_time(config: AppConfig, now: datetime) -> datetime:
    sample_seconds = max(config.sampling.price_sample_seconds, 1)
    rounded = now.replace(second=0, microsecond=0) + timedelta(seconds=sample_seconds)
    return rounded


def seconds_until_next_sample(config: AppConfig, now: datetime) -> float:
    target = next_sample_time(config, now)
    return max((target - now).total_seconds(), 0.0)


def is_strategy_decision_allowed(config: AppConfig, now: datetime) -> bool:
    if config.runtime.session_mode == "force_open":
        return True
    if config.runtime.session_mode == "notify_only":
        return False
    return is_in_trading_window(config, now)


def should_run_pipeline(config: AppConfig) -> bool:
    return config.runtime.session_mode in {"market_hours", "force_open", "notify_only"}


@dataclass(slots=True)
class ReplayController:
    ticks: list[PriceTick]
    mode: str = "realtime"
    cursor: int = 0

    @classmethod
    def from_csv(cls, csv_path: Path, symbol: str = "ICBC_ACC_GOLD", mode: str = "realtime") -> "ReplayController":
        ticks: list[PriceTick] = []
        with csv_path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                ticks.append(
                    PriceTick(
                        symbol=row.get("symbol", symbol),
                        price=float(row["price"]),
                        observed_at=datetime.fromisoformat(row["observed_at"]),
                        source=row.get("source", "replay_csv"),
                    )
                )
        return cls(ticks=sorted(ticks, key=lambda item: item.observed_at), mode=mode)

    @classmethod
    def from_sqlite(
        cls,
        sqlite_path: Path,
        symbol: str = "ICBC_ACC_GOLD",
        mode: str = "realtime",
    ) -> "ReplayController":
        with sqlite3.connect(sqlite_path) as conn:
            rows = conn.execute(
                """
                SELECT observed_at, symbol, price, source FROM minute_prices
                WHERE symbol = ?
                ORDER BY observed_at ASC
                """,
                (symbol,),
            ).fetchall()
        ticks = [
            PriceTick(
                symbol=row[1],
                price=float(row[2]),
                observed_at=datetime.fromisoformat(row[0]),
                source=row[3],
            )
            for row in rows
        ]
        return cls(ticks=ticks, mode=mode)

    def next_tick(self) -> PriceTick | None:
        if self.cursor >= len(self.ticks):
            return None
        tick = self.ticks[self.cursor]
        self.cursor += 1
        return tick

    def step(self) -> PriceTick | None:
        return self.next_tick()

    def fast_forward(self, steps: int | None = None) -> list[PriceTick]:
        if self.cursor >= len(self.ticks):
            return []
        if steps is None:
            steps = len(self.ticks) - self.cursor
        result = self.ticks[self.cursor : self.cursor + steps]
        self.cursor += len(result)
        return result

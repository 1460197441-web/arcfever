"""Collector for SGE Au99.99 daily reference data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from collectors.icbc_accumulated_gold import CollectorError
from models import ReferenceDailyQuote


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SgeAu9999Collector:
    """Collector for Shanghai Gold Exchange Au99.99 daily filter data."""

    base_url: str = "https://www.sge.com.cn/h5_sjzx/yshq"
    timeout_seconds: int = 10
    max_retries: int = 3
    headers: dict[str, str] = field(
        default_factory=lambda: {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
        }
    )
    selectors: dict[str, Any] = field(
        default_factory=lambda: {
            "symbol_keywords": ["Au99.99", "AU99.99", "au99.99"],
            "fallback_header_order": ["last", "high", "low", "open"],
        }
    )
    session: requests.Session = field(init=False)
    last_fetch_metadata: dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.session = requests.Session()

    def close(self) -> None:
        self.session.close()

    def fetch_daily_quote(self, now: datetime) -> ReferenceDailyQuote:
        fetch_result = self._get_html()
        self.last_fetch_metadata = fetch_result
        return self.parse_daily_quote(
            fetch_result["html"],
            now=fetch_result["fetched_at"],
            page_url=fetch_result["final_url"],
            http_status=fetch_result["http_status"],
            fetched_at=fetch_result["fetched_at"],
        )

    def parse_daily_quote(
        self,
        html: str,
        now: datetime,
        page_url: str | None = None,
        http_status: int | None = None,
        fetched_at: datetime | None = None,
    ) -> ReferenceDailyQuote:
        soup = BeautifulSoup(html, "html.parser")
        page_url = page_url or self.base_url
        fetched_at = fetched_at or now

        for parser in (self._parse_from_rows, self._parse_from_scripts):
            result = parser(soup, fetched_at)
            if result is not None:
                result.raw_payload.setdefault("final_url", page_url)
                result.raw_payload.setdefault("http_status", http_status)
                return result

        raise CollectorError(f"Could not parse SGE Au99.99 quote from {page_url}")

    def _get_html(self) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(self.base_url, headers=self.headers, timeout=self.timeout_seconds)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or response.encoding or "utf-8"
                fetched_at = datetime.now()
                return {
                    "html": response.text,
                    "final_url": str(response.url),
                    "http_status": response.status_code,
                    "fetched_at": fetched_at,
                }
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                LOGGER.warning("SGE collector attempt %s failed: %s", attempt, exc)
                if attempt < self.max_retries:
                    time.sleep(float(attempt))
        raise CollectorError(f"Failed to fetch SGE Au99.99 page: {last_error}") from last_error

    def _parse_from_rows(self, soup: BeautifulSoup, fetched_at: datetime) -> ReferenceDailyQuote | None:
        keywords = self.selectors["symbol_keywords"]
        table_headers = self._extract_header_map(soup)

        for row in soup.select("tr"):
            cells = [self._normalize_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            if not cells:
                continue
            symbol_index = next(
                (index for index, cell in enumerate(cells) if any(keyword in cell for keyword in keywords)),
                None,
            )
            if symbol_index is None:
                continue

            symbol = cells[symbol_index]
            price_cells = cells[symbol_index + 1 :]
            quote_time = self._extract_datetime_from_text(" ".join(cells))

            if table_headers is not None:
                mapped = self._map_by_headers(price_cells, table_headers)
            else:
                mapped = self._map_by_fallback_order(price_cells)

            return ReferenceDailyQuote(
                symbol=symbol,
                open=mapped["open"],
                high=mapped["high"],
                low=mapped["low"],
                last=mapped["last"],
                quote_time=quote_time or fetched_at,
                quote_time_source="page_time" if quote_time is not None else "fetch_time",
                source_name="SGE Au99.99",
                raw_payload={
                    "parser": "row_mapping",
                    "header_map": table_headers,
                    "row_cells": cells,
                },
            )
        return None

    def _parse_from_scripts(self, soup: BeautifulSoup, fetched_at: datetime) -> ReferenceDailyQuote | None:
        for script in soup.find_all("script"):
            text = script.string or script.get_text(" ", strip=True)
            if "Au99.99" not in text and "AU99.99" not in text:
                continue
            payload = self._extract_json(text)
            if payload is None:
                continue
            node = self._find_symbol_node(payload)
            if node is None:
                continue
            quote_time = self._extract_datetime_from_text(text)
            return ReferenceDailyQuote(
                symbol=str(node.get("symbol") or node.get("name") or "Au99.99"),
                open=self._must_float(node, ["open", "openPrice"]),
                high=self._must_float(node, ["high", "highPrice"]),
                low=self._must_float(node, ["low", "lowPrice"]),
                last=self._must_float(node, ["last", "latest", "price"]),
                quote_time=quote_time or fetched_at,
                quote_time_source="page_time" if quote_time is not None else "fetch_time",
                source_name="SGE Au99.99",
                raw_payload={"parser": "script_fallback", "payload": node},
            )
        return None

    def _extract_header_map(self, soup: BeautifulSoup) -> dict[str, int] | None:
        for row in soup.select("tr"):
            headers = [self._normalize_text(cell.get_text(" ", strip=True)) for cell in row.find_all("th")]
            if len(headers) < 5:
                continue
            mapped: dict[str, int] = {}
            for index, header in enumerate(headers[1:], start=0):
                field_name = self._classify_header(header)
                if field_name is not None and field_name not in mapped:
                    mapped[field_name] = index
            if {"open", "high", "low", "last"}.issubset(mapped):
                return mapped
        return None

    def _map_by_headers(self, price_cells: list[str], header_map: dict[str, int]) -> dict[str, float]:
        result: dict[str, float] = {}
        for field_name in ("open", "high", "low", "last"):
            index = header_map[field_name]
            if index >= len(price_cells):
                raise CollectorError(f"SGE Au99.99 row is missing field {field_name}.")
            value = self._parse_float(price_cells[index])
            if value is None:
                raise CollectorError(f"SGE Au99.99 row contains invalid numeric field {field_name}.")
            result[field_name] = value
        return result

    def _map_by_fallback_order(self, price_cells: list[str]) -> dict[str, float]:
        numeric_values = [self._parse_float(cell) for cell in price_cells]
        numeric_values = [value for value in numeric_values if value is not None]
        if len(numeric_values) < 4:
            raise CollectorError("SGE Au99.99 row matched symbol but numeric fields are incomplete.")

        fallback_order = self.selectors["fallback_header_order"]
        return {field_name: numeric_values[index] for index, field_name in enumerate(fallback_order[:4])}

    @staticmethod
    def _classify_header(header: str) -> str | None:
        normalized = header.lower()
        if any(token in normalized for token in ("今开", "开盘", "开", "open", "寮")):
            return "open"
        if any(token in normalized for token in ("最高", "高", "high", "楂")):
            return "high"
        if any(token in normalized for token in ("最低", "低", "low", "浣")):
            return "low"
        if any(token in normalized for token in ("最新", "last", "latest", "price", "鏂")):
            return "last"
        return None

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | list[Any] | None:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    def _find_symbol_node(self, payload: Any) -> dict[str, Any] | None:
        if isinstance(payload, dict):
            target = str(payload.get("symbol", payload.get("name", "")))
            if any(keyword in target for keyword in self.selectors["symbol_keywords"]):
                return payload
            for value in payload.values():
                node = self._find_symbol_node(value)
                if node is not None:
                    return node
        if isinstance(payload, list):
            for item in payload:
                node = self._find_symbol_node(item)
                if node is not None:
                    return node
        return None

    @staticmethod
    def _must_float(node: dict[str, Any], keys: list[str]) -> float:
        for key in keys:
            if key in node:
                return float(str(node[key]).replace(",", ""))
        raise CollectorError(f"Required numeric field missing from SGE payload: {keys}")

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _parse_float(value: str) -> float | None:
        match = re.search(r"(-?\d+(?:,\d{3})*(?:\.\d+)?)", value)
        if not match:
            return None
        return float(match.group(1).replace(",", ""))

    @staticmethod
    def _extract_datetime_from_text(text: str) -> datetime | None:
        patterns = [
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
            r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
            r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1).replace("/", "-")
                fmt = "%Y-%m-%d %H:%M:%S" if len(value) == 19 else "%Y-%m-%d %H:%M"
                return datetime.strptime(value, fmt)
        return None

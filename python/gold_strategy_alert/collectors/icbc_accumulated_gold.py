"""Primary collector for ICBC accumulated gold quotes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import re
import subprocess
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from models import MarketPriceQuote


LOGGER = logging.getLogger(__name__)


class CollectorError(RuntimeError):
    """Raised when a collector cannot produce a valid parsed result."""


@dataclass(slots=True)
class IcbcAccumulatedGoldCollector:
    """Collector for the dedicated ICBC accumulated gold quote page."""

    base_url: str = "https://mybank.icbc.com.cn/icbc/newperbank/perbank3/gold/goldaccrual_query_out.jsp"
    timeout_seconds: int = 10
    max_retries: int = 3
    headers: dict[str, str] = field(
        default_factory=lambda: {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            ),
            "Referer": "https://mybank.icbc.com.cn/",
        }
    )
    selectors: dict[str, Any] = field(
        default_factory=lambda: {
            "currency": "CNY",
            "id_prefixes": {
                "instrument_name": "prodnoo_",
                "current_price": "activeprice_",
                "low_price": "lowprice_",
                "high_price": "highprice_",
                "reference_price": "regprice_",
            },
        }
    )
    session: requests.Session = field(init=False)
    last_fetch_metadata: dict[str, Any] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.session = requests.Session()

    def close(self) -> None:
        self.session.close()

    def fetch_quote(self, now: datetime) -> MarketPriceQuote:
        fetch_result = self._get_html()
        self.last_fetch_metadata = fetch_result
        return self.parse_quote(
            fetch_result["html"],
            now=fetch_result["fetched_at"],
            page_url=fetch_result["final_url"],
            http_status=fetch_result["http_status"],
            fetched_at=fetch_result["fetched_at"],
        )

    def parse_quote(
        self,
        html: str,
        now: datetime,
        page_url: str | None = None,
        http_status: int | None = None,
        fetched_at: datetime | None = None,
    ) -> MarketPriceQuote:
        soup = BeautifulSoup(html, "html.parser")
        page_url = page_url or self.base_url
        fetched_at = fetched_at or now

        for parser in (
            self._parse_id_based_quote,
            self._parse_table_quote,
            self._parse_label_based_quote,
            self._parse_script_based_quote,
        ):
            result = parser(soup, fetched_at)
            if result is not None:
                result.raw_payload.setdefault("final_url", page_url)
                result.raw_payload.setdefault("http_status", http_status)
                return result

        raise CollectorError(f"Could not parse ICBC accumulated gold quote from {page_url}")

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
                LOGGER.warning("ICBC accumulated gold attempt %s failed: %s", attempt, exc)
                if attempt < self.max_retries:
                    time.sleep(float(attempt))

        curl_result = self._get_html_via_curl(self.base_url)
        if curl_result is not None:
            return curl_result
        raise CollectorError(f"Failed to fetch ICBC accumulated gold page: {last_error}") from last_error

    def _get_html_via_curl(self, url: str) -> dict[str, Any] | None:
        command = [
            "curl.exe",
            "-s",
            "-L",
            "-A",
            self.headers["User-Agent"],
            url,
            "--max-time",
            str(max(self.timeout_seconds, 20)),
            "-w",
            "\n__CODEX_HTTP_STATUS__:%{http_code}\n__CODEX_EFFECTIVE_URL__:%{url_effective}\n",
        ]
        try:
            completed = subprocess.run(command, capture_output=True, check=True, timeout=max(self.timeout_seconds, 25))
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("ICBC curl fallback failed for %s: %s", url, exc)
            return None

        stdout = completed.stdout.decode("gb18030", errors="ignore")
        status_match = re.search(r"\n__CODEX_HTTP_STATUS__:(\d{3})\n__CODEX_EFFECTIVE_URL__:(.+)\n?$", stdout, re.DOTALL)
        if not status_match:
            return None
        html = stdout[: status_match.start()]
        return {
            "html": html,
            "final_url": status_match.group(2).strip(),
            "http_status": int(status_match.group(1)),
            "fetched_at": datetime.now(),
        }

    def _parse_id_based_quote(self, soup: BeautifulSoup, fetched_at: datetime) -> MarketPriceQuote | None:
        prefixes = self.selectors["id_prefixes"]
        instrument_tag = soup.find(id=re.compile(rf"^{re.escape(prefixes['instrument_name'])}"))
        current_tag = soup.find(id=re.compile(rf"^{re.escape(prefixes['current_price'])}"))
        low_tag = soup.find(id=re.compile(rf"^{re.escape(prefixes['low_price'])}"))
        high_tag = soup.find(id=re.compile(rf"^{re.escape(prefixes['high_price'])}"))
        reference_tag = soup.find(id=re.compile(rf"^{re.escape(prefixes['reference_price'])}"))
        if instrument_tag is None or current_tag is None:
            return None

        instrument_name = self._normalize_text(instrument_tag.get_text(" ", strip=True))
        current_price = self._parse_float(current_tag.get_text(" ", strip=True))
        if not instrument_name or current_price is None:
            raise CollectorError("ICBC id-based parsing found matching ids but missing core fields.")

        all_text = soup.get_text(" ", strip=True)
        quote_time = self._extract_update_time(all_text) or self._extract_datetime_from_text(all_text)
        return MarketPriceQuote(
            current_price=current_price,
            instrument_name=instrument_name,
            quote_time=quote_time or fetched_at,
            quote_time_source="page_time" if quote_time is not None else "fetch_time",
            currency=self.selectors["currency"],
            source_name="ICBC Accumulated Gold Page",
            open_price=self._parse_float(reference_tag.get_text(" ", strip=True)) if reference_tag else None,
            high_price=self._parse_float(high_tag.get_text(" ", strip=True)) if high_tag else None,
            low_price=self._parse_float(low_tag.get_text(" ", strip=True)) if low_tag else None,
            raw_payload={
                "parser": "id_prefix",
                "id_rule_hit": True,
                "open_price_semantics": "reference_price_regprice",
            },
        )

    def _parse_table_quote(self, soup: BeautifulSoup, fetched_at: datetime) -> MarketPriceQuote | None:
        rows = soup.select("table tr")
        if not rows:
            return None

        instrument_name: str | None = None
        current_price: float | None = None
        open_price: float | None = None
        high_price: float | None = None
        low_price: float | None = None
        quote_time: datetime | None = None

        for row in rows:
            cells = [self._normalize_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            if not cells:
                continue

            if len(cells) >= 3 and current_price is None:
                row_price = self._parse_float(cells[1])
                row_time = self._extract_datetime_from_text(" ".join(cells))
                if row_price is not None and row_time is not None:
                    instrument_name = cells[0]
                    current_price = row_price
                    quote_time = row_time
                    continue

            if len(cells) >= 2:
                label = cells[0].lower()
                value = self._parse_float(cells[1])
                if value is None:
                    continue
                if any(token in label for token in ("开", "open", "reference", "reg", "寮")):
                    open_price = value
                elif any(token in label for token in ("高", "high", "楂")):
                    high_price = value
                elif any(token in label for token in ("低", "low", "浣")):
                    low_price = value

        if instrument_name is None and current_price is None:
            return None
        if instrument_name is None or current_price is None:
            raise CollectorError("ICBC table-based parsing found partial data but missing instrument_name/current_price.")

        return MarketPriceQuote(
            current_price=current_price,
            instrument_name=instrument_name,
            quote_time=quote_time or fetched_at,
            quote_time_source="page_time" if quote_time is not None else "fetch_time",
            currency=self.selectors["currency"],
            source_name="ICBC Accumulated Gold Page",
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            raw_payload={"parser": "table_fallback"},
        )

    def _parse_label_based_quote(self, soup: BeautifulSoup, fetched_at: datetime) -> MarketPriceQuote | None:
        text = self._normalize_text(soup.get_text(" ", strip=True))
        current_price = self._extract_labeled_value(
            text,
            labels=["当前价格", "最新价", "买入价", "实时主动积存价格", "褰撳墠浠锋牸", "鏈€鏂颁环", "涔板叆浠", "activeprice"],
        )
        if current_price is None:
            return None

        quote_time = self._extract_update_time(text) or self._extract_datetime_from_text(text)
        return MarketPriceQuote(
            current_price=current_price,
            instrument_name=self._extract_instrument_name_from_text(text),
            quote_time=quote_time or fetched_at,
            quote_time_source="page_time" if quote_time is not None else "fetch_time",
            currency=self.selectors["currency"],
            source_name="ICBC Accumulated Gold Page",
            open_price=self._extract_labeled_value(text, ["开盘价", "今开", "参考价格", "寮€鐩樹环", "鍙傝€冧环鏍"]),
            high_price=self._extract_labeled_value(text, ["最高价", "high", "鏈€楂樹环", "鏈€楂"]),
            low_price=self._extract_labeled_value(text, ["最低价", "low", "鏈€浣庝环", "鏈€浣"]),
            raw_payload={"parser": "label_fallback"},
        )

    def _parse_script_based_quote(self, soup: BeautifulSoup, fetched_at: datetime) -> MarketPriceQuote | None:
        for script in soup.find_all("script"):
            text = script.string or script.get_text(" ", strip=True)
            payload = self._extract_json_from_script(text)
            if payload is None:
                continue
            current_price = self._lookup_number(payload, ["currentPrice", "current_price", "price", "buyPrice"])
            if current_price is None:
                continue
            quote_time = self._extract_update_time(text) or self._extract_datetime_from_text(text)
            instrument_name = self._lookup_string(payload, ["name", "instrumentName"]) or "ICBC_ACCUMULATED_GOLD"
            return MarketPriceQuote(
                current_price=current_price,
                instrument_name=instrument_name,
                quote_time=quote_time or fetched_at,
                quote_time_source="page_time" if quote_time is not None else "fetch_time",
                currency=self._lookup_string(payload, ["currency"]) or self.selectors["currency"],
                source_name="ICBC Accumulated Gold Page",
                open_price=self._lookup_number(payload, ["open", "openPrice", "referencePrice"]),
                high_price=self._lookup_number(payload, ["high", "highPrice"]),
                low_price=self._lookup_number(payload, ["low", "lowPrice"]),
                raw_payload={"parser": "script_fallback", "payload": payload},
            )
        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _parse_float(value: str) -> float | None:
        match = re.search(r"(-?\d+(?:,\d{3})*(?:\.\d+)?)", value)
        if not match:
            return None
        return float(match.group(1).replace(",", ""))

    def _extract_labeled_value(self, text: str, labels: list[str]) -> float | None:
        for label in labels:
            match = re.search(
                rf"{re.escape(label)}[:：]?\s*(-?\d+(?:,\d{{3}})*(?:\.\d+)?)",
                text,
                re.IGNORECASE,
            )
            if match:
                return float(match.group(1).replace(",", ""))
        return None

    def _extract_instrument_name_from_text(self, text: str) -> str:
        candidates = [
            "工银积存金",
            "积存金",
            "宸ラ摱绉瓨閲",
            "绉瓨閲",
            "ICBC accumulated gold",
        ]
        for candidate in candidates:
            if candidate in text:
                return candidate
        return "ICBC_ACCUMULATED_GOLD"

    @staticmethod
    def _extract_update_time(text: str) -> datetime | None:
        match = re.search(
            r"(?:更新时间|鏇存柊鏃堕棿|update\s*time)[:：]?\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
            text,
            re.IGNORECASE,
        )
        if not match:
            return None
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")

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

    @staticmethod
    def _extract_json_from_script(text: str) -> dict[str, Any] | None:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _lookup_number(payload: dict[str, Any], keys: list[str]) -> float | None:
        for key in keys:
            value = payload.get(key)
            if value is None:
                continue
            try:
                return float(str(value).replace(",", ""))
            except ValueError:
                continue
        return None

    @staticmethod
    def _lookup_string(payload: dict[str, Any], keys: list[str]) -> str | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

"""Fallback collector for the ICBC online gold portal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import logging
import re
import subprocess
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from collectors.icbc_accumulated_gold import CollectorError, IcbcAccumulatedGoldCollector
from models import MarketPriceQuote


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class IcbcPortalFallbackCollector:
    """Fallback collector that discovers and follows quote links from the ICBC gold portal."""

    portal_url: str = "https://www.icbc.com.cn/ICBC/%E7%BD%91%E4%B8%8A%E9%BB%84%E9%87%91/"
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
            "candidate_keywords": [
                "积存金",
                "报价",
                "行情",
                "goldaccrual_query_out.jsp",
                "PBL200603",
                "frame_index.jsp?serviceId=PBL200603",
            ],
        }
    )
    session: requests.Session = field(init=False)
    embedded_parser: IcbcAccumulatedGoldCollector = field(init=False)
    last_resolution_trace: list[dict[str, Any]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.embedded_parser = IcbcAccumulatedGoldCollector()

    def close(self) -> None:
        self.session.close()
        self.embedded_parser.close()

    def fetch_quote(self, now: datetime) -> MarketPriceQuote:
        self.last_resolution_trace = []
        portal_result = self._get_html(self.portal_url)
        candidate_links = self.discover_candidate_links(portal_result["html"], base_url=portal_result["final_url"])

        for candidate in candidate_links:
            try:
                quote = self._resolve_candidate(candidate, now)
                quote.source_name = "ICBC Portal Fallback"
                quote.raw_payload.setdefault("resolution_trace", self.last_resolution_trace)
                return quote
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("ICBC portal candidate failed %s: %s", candidate, exc)
                self.last_resolution_trace.append(
                    {
                        "candidate_url": candidate,
                        "resolved_url": None,
                        "parse_success": False,
                        "error": str(exc),
                    }
                )
        raise CollectorError("ICBC portal fallback could not resolve a valid accumulated gold quote page.")

    def discover_candidate_links(self, html: str, base_url: str | None = None) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        candidates: list[str] = []
        keywords = self.selectors["candidate_keywords"]
        base_url = base_url or self.portal_url

        for anchor in soup.find_all("a", href=True):
            text = self._normalize_text(anchor.get_text(" ", strip=True))
            href = anchor["href"]
            joined = f"{text} {href}"
            if any(keyword in joined for keyword in keywords):
                candidates.append(urljoin(base_url, href))

        if self.embedded_parser.base_url not in candidates:
            candidates.append(self.embedded_parser.base_url)
        return list(dict.fromkeys(candidates))

    def _resolve_candidate(self, candidate_url: str, now: datetime) -> MarketPriceQuote:
        first_hop = self._get_html(candidate_url)
        resolved_candidates = [first_hop["final_url"]]

        try:
            quote = self.embedded_parser.parse_quote(
                first_hop["html"],
                now=first_hop["fetched_at"],
                page_url=first_hop["final_url"],
                http_status=first_hop["http_status"],
                fetched_at=first_hop["fetched_at"],
            )
            self.last_resolution_trace.append(
                {
                    "candidate_url": candidate_url,
                    "resolved_url": first_hop["final_url"],
                    "parse_success": True,
                }
            )
            return quote
        except Exception:
            nested_candidates = self.discover_candidate_links(first_hop["html"], base_url=first_hop["final_url"])
            for nested in nested_candidates:
                if nested not in resolved_candidates:
                    resolved_candidates.append(nested)
            if self.embedded_parser.base_url not in resolved_candidates:
                resolved_candidates.append(self.embedded_parser.base_url)

        for resolved_url in resolved_candidates[1:]:
            page = self._get_html(resolved_url)
            try:
                quote = self.embedded_parser.parse_quote(
                    page["html"],
                    now=page["fetched_at"],
                    page_url=page["final_url"],
                    http_status=page["http_status"],
                    fetched_at=page["fetched_at"],
                )
                self.last_resolution_trace.append(
                    {
                        "candidate_url": candidate_url,
                        "resolved_url": page["final_url"],
                        "parse_success": True,
                    }
                )
                return quote
            except Exception as exc:  # noqa: BLE001
                self.last_resolution_trace.append(
                    {
                        "candidate_url": candidate_url,
                        "resolved_url": page["final_url"],
                        "parse_success": False,
                        "error": str(exc),
                    }
                )
        raise CollectorError(f"Portal candidate could not be resolved into a quote page: {candidate_url}")

    def _get_html(self, url: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout_seconds)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or response.encoding or "utf-8"
                return {
                    "html": response.text,
                    "final_url": str(response.url),
                    "http_status": response.status_code,
                    "fetched_at": datetime.now(),
                }
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                LOGGER.warning("ICBC portal fetch attempt %s failed for %s: %s", attempt, url, exc)
                if attempt < self.max_retries:
                    time.sleep(float(attempt))
        curl_result = self._get_html_via_curl(url)
        if curl_result is not None:
            return curl_result
        raise CollectorError(f"Failed to fetch ICBC portal URL {url}: {last_error}") from last_error

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
            LOGGER.warning("ICBC portal curl fallback failed for %s: %s", url, exc)
            return None

        if "mybank.icbc.com.cn" in url:
            stdout = completed.stdout.decode("gb18030", errors="ignore")
        else:
            stdout = completed.stdout.decode("utf-8", errors="ignore")
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

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

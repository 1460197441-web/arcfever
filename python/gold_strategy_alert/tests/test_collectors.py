from __future__ import annotations

from datetime import datetime

import pytest

from collectors.icbc_accumulated_gold import CollectorError, IcbcAccumulatedGoldCollector
from collectors.icbc_portal_fallback import IcbcPortalFallbackCollector
from collectors.sge_au9999 import SgeAu9999Collector


def test_icbc_accumulated_gold_parser_extracts_quote_from_table_html() -> None:
    html = """
    <html>
      <body>
        <table>
          <tr><th>名称</th><th>银行买入价</th><th>更新时间</th></tr>
          <tr><td>工银积存金</td><td>812.34</td><td>2026-03-23 10:06:00</td></tr>
          <tr><td>开盘价</td><td>800.11</td></tr>
          <tr><td>最高价</td><td>815.00</td></tr>
          <tr><td>最低价</td><td>798.66</td></tr>
        </table>
      </body>
    </html>
    """
    collector = IcbcAccumulatedGoldCollector()
    quote = collector.parse_quote(html, now=datetime(2026, 3, 23, 10, 6, 0))
    assert quote.current_price == pytest.approx(812.34)
    assert quote.instrument_name == "工银积存金"
    assert quote.open_price == pytest.approx(800.11)
    assert quote.high_price == pytest.approx(815.00)
    assert quote.low_price == pytest.approx(798.66)


def test_icbc_accumulated_gold_parser_raises_on_missing_price() -> None:
    html = "<html><body><table><tr><td>工银积存金</td><td>--</td></tr></table></body></html>"
    collector = IcbcAccumulatedGoldCollector()
    with pytest.raises(CollectorError):
        collector.parse_quote(html, now=datetime(2026, 3, 23, 10, 6, 0))


def test_icbc_portal_fallback_discovers_candidate_links() -> None:
    html = """
    <html><body>
      <a href="/icbc/newperbank/perbank3/gold/goldaccrual_query_out.jsp">积存金行情</a>
      <a href="/foo">其他</a>
    </body></html>
    """
    collector = IcbcPortalFallbackCollector()
    links = collector.discover_candidate_links(html)
    assert any("goldaccrual_query_out.jsp" in link for link in links)


def test_sge_au9999_parser_extracts_row_values() -> None:
    html = """
    <html>
      <body>
        <table>
          <tr><th>品种</th><th>开盘</th><th>最高</th><th>最低</th><th>最新</th><th>时间</th></tr>
          <tr><td>Au99.99</td><td>578.10</td><td>582.50</td><td>576.00</td><td>581.20</td><td>2026-03-23 10:10:00</td></tr>
        </table>
      </body>
    </html>
    """
    collector = SgeAu9999Collector()
    quote = collector.parse_daily_quote(html, now=datetime(2026, 3, 23, 10, 10, 0))
    assert quote.symbol == "Au99.99"
    assert quote.open == pytest.approx(578.10)
    assert quote.high == pytest.approx(582.50)
    assert quote.low == pytest.approx(576.00)
    assert quote.last == pytest.approx(581.20)


def test_sge_au9999_parser_raises_when_required_fields_are_missing() -> None:
    html = "<html><body><table><tr><td>Au99.99</td><td>581.20</td></tr></table></body></html>"
    collector = SgeAu9999Collector()
    with pytest.raises(CollectorError):
        collector.parse_daily_quote(html, now=datetime(2026, 3, 23, 10, 10, 0))

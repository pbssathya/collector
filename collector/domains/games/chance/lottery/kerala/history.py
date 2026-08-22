"""Official Kerala Lottery historical source navigation.

The current result endpoint is addressed by ``drawserial``. Living Habitat evidence
shows that those identifiers are usually locally sequential but can contain large
historical discontinuities. The official older-draw page already publishes result
links grouped by lottery, so this module uses that existing source capability to
resolve the nearest published serial below a known serial.

This module discovers source addresses only. It does not interpret lottery results.
"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Iterable, Optional
from urllib.parse import parse_qs, urlparse

import requests


DETAILS_URL = "https://result.keralalotteries.com/detailsofdrawweb.php"


class _HistoryPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.options: list[tuple[str, str]] = []
        self.drawserials: set[int] = set()
        self._inside_lottery_select = False
        self._option_value: Optional[str] = None
        self._option_text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)

        if tag == "select" and values.get("name") == "lotterydet":
            self._inside_lottery_select = True
            return

        if tag == "option" and self._inside_lottery_select:
            self._option_value = values.get("value")
            self._option_text = []
            return

        if tag == "a" and values.get("href"):
            parsed = urlparse(values["href"])
            if parsed.path.endswith("viewlotisresult.php"):
                query = parse_qs(parsed.query)
                for raw in query.get("drawserial", []):
                    if raw.isdigit():
                        self.drawserials.add(int(raw))

    def handle_endtag(self, tag: str) -> None:
        if tag == "option" and self._option_value is not None:
            text = " ".join("".join(self._option_text).split())
            if self._option_value:
                self.options.append((self._option_value, text))
            self._option_value = None
            self._option_text = []
            return

        if tag == "select" and self._inside_lottery_select:
            self._inside_lottery_select = False

    def handle_data(self, data: str) -> None:
        if self._option_value is not None:
            self._option_text.append(data)


def parse_lottery_options(html: str) -> list[tuple[str, str]]:
    parser = _HistoryPageParser()
    parser.feed(html)
    return parser.options


def parse_drawserials(html: str) -> set[int]:
    parser = _HistoryPageParser()
    parser.feed(html)
    return parser.drawserials


def nearest_lower_source(before_source: int, candidates: Iterable[int]) -> Optional[int]:
    lower = [candidate for candidate in candidates if candidate < before_source]
    return max(lower) if lower else None


class OfficialHistoryResolver:
    """Resolve prior published drawserials through the official history page."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Collector/1.0 KeralaHistoryResolver"})

    def previous_source_id(self, before_source: int) -> Optional[int]:
        landing = self.session.get(DETAILS_URL, timeout=self.timeout)
        landing.raise_for_status()
        options = parse_lottery_options(landing.text)

        # De-duplicate option values while retaining source order.
        unique_options: list[tuple[str, str]] = []
        seen_values: set[str] = set()
        for value, label in options:
            if value in seen_values:
                continue
            seen_values.add(value)
            unique_options.append((value, label))

        candidates: set[int] = set()
        for value, _label in unique_options:
            response = self.session.post(
                DETAILS_URL,
                data={"lotterydet": value},
                timeout=self.timeout,
            )
            response.raise_for_status()
            candidates.update(parse_drawserials(response.text))

        return nearest_lower_source(before_source, candidates)

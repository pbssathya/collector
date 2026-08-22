"""Official Kerala legacy source addressing and navigation.

The older Kerala history index uses a different source namespace from modern
``drawserial`` results. Legacy rows are addressed by ``drawno`` and the result
endpoint returns a tiny JavaScript redirect to the actual PDF.

This module discovers and resolves those source addresses. It does not decide
which historical records an application needs.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Optional

import requests

from .history import DETAILS_URL, parse_lottery_options


LEGACY_REPORT_URL = (
    "https://result.keralalotteries.com/reports/resultentryeport1.php"
)


@dataclass(frozen=True)
class LegacySource:
    """One official legacy ``drawno`` row from a lottery family."""

    drawno: int
    sequence: Optional[int]
    text: str

    @property
    def source(self) -> str:
        return f"legacy:{self.drawno}"


@dataclass(frozen=True)
class LegacyFamily:
    """Legacy source rows published under one official lottery option."""

    option: str
    label: str
    sources: tuple[LegacySource, ...]


class _LegacyRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[LegacySource] = []
        self._in_row = False
        self._text: list[str] = []
        self._attrs: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self._in_row = True
            self._text = []
            self._attrs = []
            return

        if not self._in_row:
            return

        for key, value in attrs:
            if value:
                self._attrs.append((tag, key, value))

    def handle_data(self, data: str) -> None:
        if self._in_row:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "tr" or not self._in_row:
            return

        text = html.unescape(" ".join("".join(self._text).split()))
        drawnos: set[int] = set()

        for _tag, _key, value in self._attrs:
            for match in re.findall(
                r"loadserialno\s*\(\s*(\d+)\s*\)", value, flags=re.I
            ):
                drawnos.add(int(match))
            for match in re.findall(r"drawno1=(\d+)", value, flags=re.I):
                drawnos.add(int(match))

        if drawnos:
            sequence_match = re.search(
                r"-\s*(\d+)(?:st|nd|rd|th)?\b", text, flags=re.I
            )
            sequence = int(sequence_match.group(1)) if sequence_match else None

            # One official row may expose the same address through more than one
            # attribute. A row identifies one result, so retain one drawno.
            self.rows.append(
                LegacySource(
                    drawno=max(drawnos),
                    sequence=sequence,
                    text=text,
                )
            )

        self._in_row = False
        self._text = []
        self._attrs = []


def parse_legacy_rows(page_html: str) -> list[LegacySource]:
    """Extract legacy ``drawno`` rows from one official history page."""
    parser = _LegacyRowParser()
    parser.feed(page_html)
    return parser.rows


def script_location(raw: bytes) -> Optional[str]:
    """Return the JavaScript redirect target used by the legacy result endpoint."""
    text = raw.decode("utf-8", errors="replace")
    match = re.search(
        r"(?:document\.)?location\s*=\s*['\"]([^'\"]+)['\"]",
        text,
        flags=re.I,
    )
    return match.group(1) if match else None


class LegacyHistoryResolver:
    """Discover official legacy result-address groups without assuming chronology."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Collector/1.0 KeralaLegacyResolver"})

    def families(self) -> list[LegacyFamily]:
        """Return legacy rows grouped by their official lottery-family index."""
        landing = self.session.get(DETAILS_URL, timeout=self.timeout)
        landing.raise_for_status()
        options = parse_lottery_options(landing.text)

        unique_options: list[tuple[str, str]] = []
        seen_values: set[str] = set()
        for value, label in options:
            if value in seen_values:
                continue
            seen_values.add(value)
            unique_options.append((value, label))

        families: list[LegacyFamily] = []
        for value, label in unique_options:
            response = self.session.post(
                DETAILS_URL,
                data={"lotterydet": value},
                timeout=self.timeout,
            )
            response.raise_for_status()
            rows = parse_legacy_rows(response.text)
            if not rows:
                continue

            # The family-local visible draw number is the only published order
            # that has proved meaningful inside one legacy family. Cross-family
            # drawno values are explicitly NOT treated as chronological.
            ordered = sorted(
                rows,
                key=lambda row: (
                    row.sequence is not None,
                    int(row.sequence or -1),
                    row.drawno,
                ),
                reverse=True,
            )

            families.append(
                LegacyFamily(
                    option=value,
                    label=label,
                    sources=tuple(ordered),
                )
            )

        return families

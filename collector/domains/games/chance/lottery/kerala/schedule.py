"""Official Kerala Lottery upcoming-draw schedule collection.

This is factual source collection only. It does not rank dates or make
participation decisions; Nokku owns those decisions.
"""

from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
import re
from typing import Any

from collector.contracts.connector import Connector as BaseConnector
from collector.contracts.document import Document
from collector.core.fetcher import HTTPFetcher


SCHEDULE_URL = "https://www.lotteryagent.kerala.gov.in/"
SCHEDULE_SOURCE = "upcoming"


class _HTMLTableParser(HTMLParser):
    """Small dependency-free HTML table reader for the LOTIS schedule page."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._table_depth = 0
        self._rows: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._rows = []
        elif self._table_depth == 1 and tag == "tr":
            self._row = []
        elif self._table_depth == 1 and tag in {"td", "th"}:
            self._cell_parts = []
        elif self._cell_parts is not None and tag == "br":
            self._cell_parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._table_depth == 1 and tag in {"td", "th"}:
            if self._row is not None and self._cell_parts is not None:
                self._row.append(" ".join("".join(self._cell_parts).split()))
            self._cell_parts = None
        elif self._table_depth == 1 and tag == "tr":
            if self._rows is not None and self._row:
                self._rows.append(self._row)
            self._row = None
        elif tag == "table" and self._table_depth:
            if self._table_depth == 1 and self._rows is not None:
                self.tables.append(self._rows)
                self._rows = None
            self._table_depth -= 1


def _find_upcoming_table(tables: list[list[list[str]]]) -> tuple[list[list[str]], int] | None:
    for rows in tables:
        for index, row in enumerate(rows):
            normalized = {" ".join(cell.lower().split()) for cell in row}
            if "lottery" in normalized and any(
                cell.startswith("draw date and time") for cell in normalized
            ):
                return rows, index
    return None


def _parse_lottery_cell(value: str) -> tuple[str, str | None]:
    match = re.match(r"^(.*?)\s*\(([^()]]+)\)\s*$", value.strip())
    if not match:
        return value.strip(), None
    return match.group(1).strip(), match.group(2).strip()


def parse_upcoming_draws(content: bytes) -> dict[str, Any] | None:
    """Parse the official LOTIS upcoming-draw table into structured facts."""
    text = content.decode("utf-8", errors="replace")
    parser = _HTMLTableParser()
    parser.feed(text)

    found = _find_upcoming_table(parser.tables)
    if found is None:
        return None

    rows, header_index = found
    draws: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        cells = [" ".join(cell.split()) for cell in row if cell.strip()]
        if len(cells) < 3:
            continue

        if cells[0].isdigit() and len(cells) >= 4:
            lottery_cell, draw_datetime_text, venue = cells[1], cells[2], cells[3]
        else:
            lottery_cell, draw_datetime_text, venue = cells[0], cells[1], cells[2]

        try:
            draw_datetime = datetime.strptime(draw_datetime_text, "%d-%m-%Y %I:%M %p")
        except ValueError:
            continue

        lottery_name, draw_code = _parse_lottery_cell(lottery_cell)
        draws.append(
            {
                "lottery_name": lottery_name,
                "draw_code": draw_code,
                "draw_date": draw_datetime.date().isoformat(),
                "draw_time": draw_datetime.strftime("%H:%M"),
                "draw_venue": venue,
            }
        )

    if not draws:
        return None

    return {
        "source_kind": "official_upcoming_draw_schedule",
        "upcoming_draws": draws,
    }


class ScheduleConnector(BaseConnector):
    """Connector for the official LOTIS upcoming-draw schedule."""

    def __init__(self, **kwargs: Any) -> None:
        del kwargs
        self.fetcher = HTTPFetcher()

    def retrieve(self, source: str) -> Document:
        if not self.supports(source):
            raise ValueError(f"Unsupported Kerala schedule source: {source}")
        return self.fetcher.retrieve(SCHEDULE_URL)

    def parse(self, content: bytes) -> dict[str, Any] | None:
        return parse_upcoming_draws(content)

    def supports(self, source: str) -> bool:
        return str(source).strip().lower() == SCHEDULE_SOURCE

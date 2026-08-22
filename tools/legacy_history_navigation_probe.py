from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlparse

import requests


DETAILS_URL = "https://result.keralalotteries.com/detailsofdrawweb.php"
TARGET_BEFORE = 72014

# Weekly lotteries that can cover the pre-lockdown March 2020 period.
PROBE_OPTIONS = {
    "31": "WIN-WIN",
    "50": "KARUNYA",
    "52": "AKSHAYA",
    "57": "POURNAMI",
    "83": "KARUNYA PLUS",
    "102": "STHREE SAKTHI",
    "113": "NIRMAL",
}


class RowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, object]] = []
        self._in_row = False
        self._text: list[str] = []
        self._attrs: list[tuple[str, str, str]] = []
        self._links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "tr":
            self._in_row = True
            self._text = []
            self._attrs = []
            self._links = []
            return
        if not self._in_row:
            return

        for key, value in attrs:
            if value:
                self._attrs.append((tag, key, value))
        if tag == "a" and values.get("href"):
            self._links.append(urljoin(DETAILS_URL, values["href"]))

    def handle_data(self, data: str) -> None:
        if self._in_row:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "tr" or not self._in_row:
            return

        text = " ".join("".join(self._text).split())
        legacy_drawnos: set[int] = set()
        modern_serials: set[int] = set()

        for _tag, _key, value in self._attrs:
            for match in re.findall(r"loadserialno\s*\(\s*(\d+)\s*\)", value, flags=re.I):
                legacy_drawnos.add(int(match))
            for match in re.findall(r"drawno1=(\d+)", value, flags=re.I):
                legacy_drawnos.add(int(match))
            for match in re.findall(r"drawserial=(\d+)", value, flags=re.I):
                modern_serials.add(int(match))

        for link in self._links:
            parsed = urlparse(link)
            query = parse_qs(parsed.query)
            for raw in query.get("drawserial", []):
                if raw.isdigit():
                    modern_serials.add(int(raw))
            for raw in query.get("drawno1", []):
                if raw.isdigit():
                    legacy_drawnos.add(int(raw))

        if text or legacy_drawnos or modern_serials:
            self.rows.append(
                {
                    "text": html.unescape(text),
                    "legacy_drawnos": sorted(legacy_drawnos),
                    "modern_serials": sorted(modern_serials),
                }
            )

        self._in_row = False
        self._text = []
        self._attrs = []
        self._links = []


def main() -> int:
    print("=== KERALA LEGACY HISTORY NAVIGATION PROBE ===")
    print("official page:", DETAILS_URL)
    print("preservation: NO")
    print("known modern boundary: 72014 = 26/07/2020")
    print("purpose: inspect how the official history page represents older pre-72014 draws\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 LegacyHistoryProbe"})

    for option, label in PROBE_OPTIONS.items():
        response = session.post(DETAILS_URL, data={"lotterydet": option}, timeout=30)
        response.raise_for_status()

        parser = RowParser()
        parser.feed(response.text)

        interesting = [
            row
            for row in parser.rows
            if row["legacy_drawnos"] or row["modern_serials"]
        ]
        modern = sorted(
            {
                serial
                for row in interesting
                for serial in row["modern_serials"]
            }
        )
        legacy = sorted(
            {
                drawno
                for row in interesting
                for drawno in row["legacy_drawnos"]
            }
        )

        print(f"--- {label} (lotterydet={option}) ---")
        print("bytes:", len(response.content))
        print("rows with navigation:", len(interesting))
        print("modern drawserial count:", len(modern))
        if modern:
            print("modern range:", modern[0], "→", modern[-1])
            lower = [value for value in modern if value < TARGET_BEFORE]
            print("modern source below 72014:", max(lower) if lower else None)
        print("legacy drawno count:", len(legacy))
        if legacy:
            print("legacy drawno range:", legacy[0], "→", legacy[-1])

        # Show navigation rows around the modern/legacy boundary and rows mentioning 2020.
        samples = []
        for row in interesting:
            text = str(row["text"])
            modern_values = list(row["modern_serials"])
            legacy_values = list(row["legacy_drawnos"])
            if (
                any(value <= TARGET_BEFORE + 5 for value in modern_values)
                or legacy_values
                or "2020" in text
                or "2019" in text
            ):
                samples.append(row)

        print("sample navigation rows:")
        for row in samples[-15:]:
            print(
                "  ",
                {
                    "modern": row["modern_serials"],
                    "legacy": row["legacy_drawnos"],
                    "text": str(row["text"])[:220],
                },
            )
        print()

    print("No Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

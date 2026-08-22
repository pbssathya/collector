from __future__ import annotations

import html
import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from collector.domains.games.chance.lottery.kerala.parser import Parser


DETAILS_URL = "https://result.keralalotteries.com/detailsofdrawweb.php"
LEGACY_REPORT_URL = "https://result.keralalotteries.com/reports/resultentryeport1.php"

PROBE_OPTIONS = {
    "31": "WIN-WIN",
    "50": "KARUNYA",
    "52": "AKSHAYA",
    "57": "POURNAMI",
    "83": "KARUNYA PLUS",
    "102": "STHREE SAKTHI",
    "113": "NIRMAL",
}


class LegacyRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, object]] = []
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
            for match in re.findall(r"loadserialno\s*\(\s*(\d+)\s*\)", value, flags=re.I):
                drawnos.add(int(match))
            for match in re.findall(r"drawno1=(\d+)", value, flags=re.I):
                drawnos.add(int(match))

        if drawnos:
            self.rows.append({"text": text, "drawnos": sorted(drawnos)})

        self._in_row = False
        self._text = []
        self._attrs = []


def extract_script_location(raw: bytes) -> str | None:
    text = raw.decode("utf-8", errors="replace")
    match = re.search(
        r"(?:document\.)?location\s*=\s*['\"]([^'\"]+)['\"]",
        text,
        flags=re.I,
    )
    return match.group(1) if match else None


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%d/%m/%Y")


def main() -> int:
    print("=== KERALA LEGACY REDIRECTED PDF / PARSER PROBE ===")
    print("preservation: NO")
    print("purpose: verify repeated legacy drawno -> JS redirect -> official PDF -> Kerala parser behavior\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 LegacyPDFParseProbe"})
    kerala_parser = Parser()
    parsed_rows: list[tuple[datetime, int, str, str]] = []

    for option, label in PROBE_OPTIONS.items():
        history = session.post(DETAILS_URL, data={"lotterydet": option}, timeout=30)
        history.raise_for_status()

        rows_parser = LegacyRowParser()
        rows_parser.feed(history.text)
        candidates: list[tuple[int, str]] = []
        for row in rows_parser.rows:
            for drawno in row["drawnos"]:
                candidates.append((int(drawno), str(row["text"])))
        candidates.sort(reverse=True)

        print(f"--- {label} (lotterydet={option}) ---")
        if not candidates:
            print("no legacy drawno discovered\n")
            continue

        drawno, row_text = candidates[0]
        print("latest legacy drawno by numeric address:", drawno, "|", row_text)

        redirector = session.get(
            LEGACY_REPORT_URL,
            params={"drawno1": drawno, "drawno": drawno},
            timeout=30,
        )
        redirector.raise_for_status()
        location = extract_script_location(redirector.content)
        print("redirector bytes:", len(redirector.content))
        print("script location:", location)

        if not location:
            print("result: NO SCRIPT LOCATION\n")
            continue

        pdf_url = urljoin(redirector.url, location)
        pdf = session.get(pdf_url, timeout=30)
        pdf.raise_for_status()
        print("pdf url:", pdf.url)
        print("pdf content-type:", pdf.headers.get("Content-Type"))
        print("pdf bytes:", len(pdf.content))
        print("starts %PDF:", pdf.content.startswith(b"%PDF"))

        try:
            parsed = kerala_parser.parse(pdf.content)
        except Exception as exc:
            print("parser error:", repr(exc))
            print()
            continue

        if not parsed:
            print("parser result: NONE\n")
            continue

        print("parsed draw date:", parsed.draw_date)
        print("parsed lottery name:", " ".join(str(parsed.lottery_name).split()))
        print("parsed prize tiers:", len(parsed.prize_tiers))

        if parsed.draw_date and parsed.draw_date != "Unknown":
            parsed_rows.append(
                (
                    parse_date(parsed.draw_date),
                    drawno,
                    label,
                    " ".join(str(parsed.lottery_name).split()),
                )
            )
        print()

    print("--- CROSS-FAMILY DATE CHECK ---")
    if parsed_rows:
        parsed_rows.sort(reverse=True)
        for draw_date, drawno, label, name in parsed_rows:
            print(draw_date.date().isoformat(), "|", drawno, "|", label, "|", name)
        latest = parsed_rows[0]
        print(
            "latest parsed legacy event among probed families:",
            latest[0].date().isoformat(),
            "|",
            latest[1],
            "|",
            latest[2],
        )
    else:
        print("no usable parsed legacy dates")

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

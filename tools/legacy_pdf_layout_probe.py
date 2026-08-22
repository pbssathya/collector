from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from collector.extractors.pdf import extract_pdf_structure, iter_pdf_lines


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

DATEISH_RE = re.compile(
    r"(?:\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b|held|date|draw)",
    re.I,
)
PRIZEISH_RE = re.compile(r"\b(?:prize|rs\.?|consolation)\b", re.I)


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


def script_location(raw: bytes) -> str | None:
    text = raw.decode("utf-8", errors="replace")
    match = re.search(
        r"(?:document\.)?location\s*=\s*['\"]([^'\"]+)['\"]",
        text,
        flags=re.I,
    )
    return match.group(1) if match else None


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def latest_legacy(session: requests.Session, option: str) -> tuple[int, str] | None:
    history = session.post(DETAILS_URL, data={"lotterydet": option}, timeout=30)
    history.raise_for_status()
    parser = LegacyRowParser()
    parser.feed(history.text)
    candidates: list[tuple[int, str]] = []
    for row in parser.rows:
        for drawno in row["drawnos"]:
            candidates.append((int(drawno), str(row["text"])))
    return max(candidates) if candidates else None


def main() -> int:
    print("=== KERALA LEGACY PDF DATE / PRIZE LAYOUT PROBE ===")
    print("preservation: NO")
    print("purpose: inspect structured legacy PDF lines before changing Kerala parser semantics\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 LegacyPDFLayoutProbe"})

    for option, label in PROBE_OPTIONS.items():
        selected = latest_legacy(session, option)
        print(f"--- {label} (lotterydet={option}) ---")
        if not selected:
            print("no legacy draw discovered\n")
            continue

        drawno, row_text = selected
        redirector = session.get(
            LEGACY_REPORT_URL,
            params={"drawno1": drawno, "drawno": drawno},
            timeout=30,
        )
        redirector.raise_for_status()
        location = script_location(redirector.content)
        if not location:
            print("no script redirect for", drawno, "\n")
            continue

        pdf_url = urljoin(redirector.url, location)
        pdf = session.get(pdf_url, timeout=30)
        pdf.raise_for_status()

        structure = extract_pdf_structure(pdf.content)
        lines = [
            normalize(str(item.get("text", "")))
            for item in iter_pdf_lines(structure)
            if str(item.get("text", "")).strip()
        ]

        print("drawno:", drawno, "|", row_text)
        print("pdf bytes:", len(pdf.content), "| lines:", len(lines))

        print("header lines:")
        for index, line in enumerate(lines[:30], start=1):
            print(f"  {index:02d}: {line}")

        date_clues = [(i + 1, line) for i, line in enumerate(lines) if DATEISH_RE.search(line)]
        print("date/draw clues:")
        for index, line in date_clues[:30]:
            print(f"  {index:02d}: {line}")

        prize_clues = [(i + 1, line) for i, line in enumerate(lines) if PRIZEISH_RE.search(line)]
        print("prize-heading clues:")
        for index, line in prize_clues[:40]:
            print(f"  {index:02d}: {line}")
        print()

    print("No Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

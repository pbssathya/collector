from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from io import BytesIO
from urllib.parse import urljoin

import pymupdf
import requests


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


def flatten_html_text(raw: bytes, encoding: str | None) -> str:
    text = raw.decode(encoding or "utf-8", errors="replace")
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(" ".join(text.split()))


def extract_report_text(raw: bytes, content_type: str, encoding: str | None) -> tuple[str, str]:
    if raw.startswith(b"%PDF") or "pdf" in content_type.lower():
        with pymupdf.open(stream=BytesIO(raw), filetype="pdf") as doc:
            text = "\n".join(page.get_text("text") for page in doc)
        return "pdf", " ".join(text.split())

    return "html/text", flatten_html_text(raw, encoding)


def main() -> int:
    print("=== KERALA LEGACY RESULT FETCH PROBE ===")
    print("history page:", DETAILS_URL)
    print("legacy report:", LEGACY_REPORT_URL)
    print("preservation: NO")
    print("purpose: verify that official legacy drawno navigation still retrieves usable result content\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 LegacyResultFetchProbe"})

    for option, label in PROBE_OPTIONS.items():
        response = session.post(DETAILS_URL, data={"lotterydet": option}, timeout=30)
        response.raise_for_status()

        parser = LegacyRowParser()
        parser.feed(response.text)
        rows = parser.rows
        if not rows:
            print(f"--- {label} ---")
            print("no legacy rows found\n")
            continue

        candidates: list[tuple[int, str]] = []
        for row in rows:
            for drawno in row["drawnos"]:
                candidates.append((int(drawno), str(row["text"])))
        candidates.sort(reverse=True)

        drawno, row_text = candidates[0]
        print(f"--- {label} (lotterydet={option}) ---")
        print("latest legacy row by drawno:", drawno, "|", row_text)

        report = session.get(
            LEGACY_REPORT_URL,
            params={"drawno1": drawno, "drawno": drawno},
            timeout=30,
        )
        report.raise_for_status()
        content_type = report.headers.get("Content-Type", "")
        kind, text = extract_report_text(
            report.content,
            content_type,
            report.encoding,
        )

        print("status:", report.status_code)
        print("final url:", report.url)
        print("content-type:", content_type)
        print("bytes:", len(report.content))
        print("representation:", kind)
        print("text preview:", text[:800])
        print()

    print("No Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

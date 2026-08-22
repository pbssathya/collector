from __future__ import annotations

import html
import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from collector.domains.games.chance.lottery.kerala.history import (
    DETAILS_URL,
    parse_lottery_options,
)
from collector.domains.games.chance.lottery.kerala.parser import Parser


YEAR = 2020
LEGACY_REPORT_URL = "https://result.keralalotteries.com/reports/resultentryeport1.php"


class LegacyRowCatalogParser(HTMLParser):
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
            # The visible lottery draw number (e.g. W-574, KN-327, BR-78) is
            # the family-local sequence. Use it only to choose newest-to-oldest
            # inspection order within one official lottery family; never as the
            # cross-family source identity.
            seq_match = re.search(r"-\s*(\d+)(?:st|nd|rd|th)?\b", text, flags=re.I)
            sequence = int(seq_match.group(1)) if seq_match else None
            self.rows.append(
                {
                    "text": text,
                    "drawnos": sorted(drawnos),
                    "sequence": sequence,
                }
            )

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


def fetch_parsed_legacy(session: requests.Session, parser: Parser, drawno: int):
    redirector = session.get(
        LEGACY_REPORT_URL,
        params={"drawno1": drawno, "drawno": drawno},
        timeout=30,
    )
    redirector.raise_for_status()
    location = script_location(redirector.content)
    if not location:
        return None, None

    pdf_url = urljoin(redirector.url, location)
    pdf = session.get(pdf_url, timeout=30)
    pdf.raise_for_status()
    if not pdf.content.startswith(b"%PDF"):
        return None, pdf_url

    return parser.parse(pdf.content), pdf_url


def date_value(text: str):
    return datetime.strptime(text, "%d/%m/%Y").date()


def main() -> int:
    print("=== KERALA LEGACY YEAR SOURCE CATALOG PROBE ===")
    print("year:", YEAR)
    print("preservation: NO")
    print("purpose: establish the complete official legacy source set for the year before reusing numeric traversal assumptions\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 LegacyYearCatalogProbe"})
    parser = Parser()

    landing = session.get(DETAILS_URL, timeout=30)
    landing.raise_for_status()
    options = parse_lottery_options(landing.text)

    unique_options: list[tuple[str, str]] = []
    seen_options: set[str] = set()
    for value, label in options:
        if value in seen_options:
            continue
        seen_options.add(value)
        unique_options.append((value, label))

    print("official lottery options:", len(unique_options))

    target_records: list[dict[str, object]] = []
    pre_year_boundaries: list[dict[str, object]] = []
    failures: list[str] = []

    for option, label in unique_options:
        history = session.post(DETAILS_URL, data={"lotterydet": option}, timeout=30)
        history.raise_for_status()
        row_parser = LegacyRowCatalogParser()
        row_parser.feed(history.text)
        rows = row_parser.rows
        if not rows:
            continue

        # Within one lottery family the visible draw number is the most meaningful
        # published order available from the index. Rows without a visible sequence
        # are inspected after sequenced rows instead of being discarded.
        ordered = sorted(
            rows,
            key=lambda row: (
                row["sequence"] is not None,
                int(row["sequence"] or -1),
                max(int(x) for x in row["drawnos"]),
            ),
            reverse=True,
        )

        print(f"\n--- {label or option} (lotterydet={option}) ---")
        print("legacy rows:", len(ordered))

        seen_target = False
        inspected = 0
        family_target = 0

        for row in ordered:
            drawno = max(int(x) for x in row["drawnos"])
            parsed, pdf_url = fetch_parsed_legacy(session, parser, drawno)
            inspected += 1
            if not parsed or not parsed.draw_date or parsed.draw_date == "Unknown":
                failures.append(f"{option}:{drawno}:unusable")
                print("  unusable:", drawno, "|", row["text"])
                continue

            draw_date = date_value(parsed.draw_date)
            name = " ".join(str(parsed.lottery_name).split())

            if draw_date.year > YEAR:
                continue

            if draw_date.year == YEAR:
                seen_target = True
                family_target += 1
                target_records.append(
                    {
                        "source": drawno,
                        "date": draw_date,
                        "name": name,
                        "option": option,
                        "family": label,
                        "sequence": row["sequence"],
                        "pdf_url": pdf_url,
                    }
                )
                continue

            # The first older draw reached after this family's 2020 run is enough
            # to prove that family's lower calendar boundary. If the newest legacy
            # record is already older than 2020, this family contributes no 2020 row.
            pre_year_boundaries.append(
                {
                    "source": drawno,
                    "date": draw_date,
                    "name": name,
                    "option": option,
                    "family": label,
                }
            )
            print(
                "  inspected:", inspected,
                "| 2020 rows:", family_target,
                "| first pre-2020:", drawno, draw_date.isoformat(),
            )
            break

        else:
            print("  inspected:", inspected, "| 2020 rows:", family_target, "| no pre-2020 boundary found")

    # De-duplicate exact source IDs if the official index exposes the same row through
    # more than one option. Keep the first occurrence only for reporting.
    by_source: dict[int, dict[str, object]] = {}
    for item in target_records:
        by_source.setdefault(int(item["source"]), item)
    target_records = list(by_source.values())

    print("\n=== 2020 LEGACY CATALOG SUMMARY ===")
    print("unique 2020 legacy sources:", len(target_records))
    if target_records:
        by_date = sorted(target_records, key=lambda item: (item["date"], int(item["source"])))
        by_source_order = sorted(target_records, key=lambda item: int(item["source"]))
        source_values = [int(item["source"]) for item in target_records]
        print("legacy source-id range:", min(source_values), "→", max(source_values))
        print("calendar range:", by_date[0]["date"].isoformat(), "→", by_date[-1]["date"].isoformat())

        inversions = []
        previous = None
        for item in by_source_order:
            if previous is not None and item["date"] < previous["date"]:
                # Ascending source ID should not be assumed to imply ascending date;
                # record every observed counterexample.
                inversions.append((previous, item))
            previous = item

        print("source-id/date inversions observed:", len(inversions))
        for left, right in inversions[:20]:
            print(
                "  ",
                left["source"], left["date"].isoformat(),
                "→",
                right["source"], right["date"].isoformat(),
            )

        older_sources = [
            int(item["source"])
            for item in pre_year_boundaries
            if item["date"].year < YEAR
        ]
        if older_sources:
            separated = max(older_sources) < min(source_values)
            print("all sampled pre-2020 boundary IDs below all 2020 IDs:", "YES" if separated else "NO")
            print("highest sampled pre-2020 boundary source:", max(older_sources))
            print("lowest 2020 legacy source:", min(source_values))
        else:
            print("pre-2020 numeric separation: UNKNOWN (no boundaries)")

        print("\n2020 legacy events by date:")
        for item in by_date:
            print(
                "  ",
                item["date"].isoformat(),
                "|",
                item["source"],
                "|",
                item["name"],
            )

    print("\npre-2020 family boundaries found:", len(pre_year_boundaries))
    for item in sorted(pre_year_boundaries, key=lambda x: (x["date"], int(x["source"]))):
        print("  ", item["date"].isoformat(), "|", item["source"], "|", item["name"])

    print("\nunusable legacy rows encountered before family boundary:", len(failures))
    for item in failures[:50]:
        print("  ", item)

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

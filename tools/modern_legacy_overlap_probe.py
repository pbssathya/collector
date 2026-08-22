from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime

import requests

from collector.domains.games.chance.lottery.kerala.connector import Connector
from collector.domains.games.chance.lottery.kerala.history import DETAILS_URL, parse_lottery_options
from collector.domains.games.chance.lottery.kerala.parser import Parser
from legacy_year_catalog_probe import LegacyRowCatalogParser, fetch_parsed_legacy


MODERN_START = 72014
MODERN_END = 72040
LEGACY_RECENT_MIN_DRAWNO = 71300


def date_value(text: str):
    return datetime.strptime(text, "%d/%m/%Y").date()


def draw_code(name: str) -> str | None:
    match = re.search(r"LOTTERY\s+NO\.\s*([A-Z][A-Z0-9]*-\d+)", name, flags=re.I)
    return match.group(1).upper() if match else None


def main() -> int:
    print("=== KERALA MODERN / LEGACY NAMESPACE OVERLAP PROBE ===")
    print("preservation: NO")
    print("purpose: determine calendar overlap and exact-event duplication across modern drawserial and legacy drawno namespaces\n")

    session = requests.Session()
    session.headers.update({"User-Agent": "Collector/1.0 ModernLegacyOverlapProbe"})
    parser = Parser()

    # Collect only the recent legacy tail around the namespace transition.
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

    legacy_by_source: dict[int, dict[str, object]] = {}
    for option, label in unique_options:
        history = session.post(DETAILS_URL, data={"lotterydet": option}, timeout=30)
        history.raise_for_status()
        row_parser = LegacyRowCatalogParser()
        row_parser.feed(history.text)

        for row in row_parser.rows:
            drawno = max(int(x) for x in row["drawnos"])
            if drawno < LEGACY_RECENT_MIN_DRAWNO:
                continue

            parsed, pdf_url = fetch_parsed_legacy(session, parser, drawno)
            if not parsed or not parsed.draw_date or parsed.draw_date == "Unknown":
                continue

            name = " ".join(str(parsed.lottery_name).split())
            legacy_by_source.setdefault(
                drawno,
                {
                    "namespace": "legacy",
                    "source": drawno,
                    "date": date_value(parsed.draw_date),
                    "name": name,
                    "code": draw_code(name),
                    "family": label,
                    "pdf_url": pdf_url,
                },
            )

    legacy = sorted(legacy_by_source.values(), key=lambda item: (item["date"], int(item["source"])))

    # Probe a bounded early-modern window. Do not infer beyond directly fetched rows.
    connector = Connector()
    modern: list[dict[str, object]] = []
    failures: list[str] = []
    for serial in range(MODERN_START, MODERN_END + 1):
        doc = connector.retrieve(str(serial))
        if not doc or doc.error or not doc.content:
            failures.append(f"{serial}:fetch")
            continue
        parsed = connector.parse(doc.content)
        if not parsed:
            failures.append(f"{serial}:parse")
            continue
        draw_date = parsed.get("draw_date")
        if not draw_date or draw_date == "Unknown":
            failures.append(f"{serial}:date")
            continue
        name = " ".join(str(parsed.get("lottery_name", "")).split())
        modern.append(
            {
                "namespace": "modern",
                "source": serial,
                "date": date_value(draw_date),
                "name": name,
                "code": draw_code(name),
                "source_url": doc.source_url,
            }
        )

    modern.sort(key=lambda item: (item["date"], int(item["source"])))

    print("legacy recent usable rows:", len(legacy))
    if legacy:
        print("legacy calendar range:", legacy[0]["date"], "→", legacy[-1]["date"])
    print("modern usable rows:", len(modern), f"from serials {MODERN_START}→{MODERN_END}")
    if modern:
        print("modern calendar range:", modern[0]["date"], "→", modern[-1]["date"])
    if failures:
        print("modern failures:", ", ".join(failures))

    if legacy and modern:
        overlap_start = max(legacy[0]["date"], modern[0]["date"])
        overlap_end = min(legacy[-1]["date"], modern[-1]["date"])
        print("calendar overlap exists:", "YES" if overlap_start <= overlap_end else "NO")
        if overlap_start <= overlap_end:
            print("calendar overlap range:", overlap_start, "→", overlap_end)

    legacy_by_code = {item["code"]: item for item in legacy if item["code"]}
    modern_by_code = {item["code"]: item for item in modern if item["code"]}
    shared_codes = sorted(set(legacy_by_code) & set(modern_by_code))

    print("\nexact draw-code matches across namespaces:", len(shared_codes))
    for code in shared_codes:
        left = legacy_by_code[code]
        right = modern_by_code[code]
        print(
            "  ",
            code,
            "| legacy", left["source"], left["date"],
            "| modern", right["source"], right["date"],
            "| same date:", "YES" if left["date"] == right["date"] else "NO",
        )

    legacy_dates: defaultdict = defaultdict(list)
    modern_dates: defaultdict = defaultdict(list)
    for item in legacy:
        legacy_dates[item["date"]].append(item)
    for item in modern:
        modern_dates[item["date"]].append(item)

    shared_dates = sorted(set(legacy_dates) & set(modern_dates))
    print("\ncalendar dates represented in both namespaces:", len(shared_dates))
    for day in shared_dates:
        print("  ", day)
        for item in legacy_dates[day]:
            print("     legacy", item["source"], "|", item["code"] or "?", "|", item["name"])
        for item in modern_dates[day]:
            print("     modern", item["source"], "|", item["code"] or "?", "|", item["name"])

    print("\nlegacy recent events:")
    for item in legacy:
        print("  ", item["date"], "|", item["source"], "|", item["code"] or "?", "|", item["name"])

    print("\nmodern early events:")
    for item in modern:
        print("  ", item["date"], "|", item["source"], "|", item["code"] or "?", "|", item["name"])

    print("\nNo Collector result or Memory state was changed by this probe.")
    print("================================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

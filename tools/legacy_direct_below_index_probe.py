from __future__ import annotations

from collections import Counter
from datetime import datetime

from collector.domains.registry import DomainRegistry


DOMAIN = "games/chance/lottery/kerala"
TARGET_CUTOFF = datetime.strptime("23/08/2017", "%d/%m/%Y")
TARGET_MONTH = "2017-07"
TARGET_MONTH_RECORDS = 8
MAX_CONSECUTIVE_EMPTY = 100


def parse_date(value: str):
    return datetime.strptime(value, "%d/%m/%Y")


def main() -> int:
    print("=== KERALA LEGACY DIRECT-BELOW-INDEX CONTINUITY PROFILE ===")
    print("preservation: NO")
    print("purpose: characterize hidden official legacy transport below the published history cutoff")
    print(f"cross-month target: {TARGET_MONTH_RECORDS} verified records in {TARGET_MONTH}")
    print(f"stall safety: {MAX_CONSECUTIVE_EMPTY} consecutive unusable addresses\n")

    connector = DomainRegistry().get_connector(DOMAIN)
    assert connector is not None
    resolver = getattr(connector, "legacy_history_resolver", None)
    assert resolver is not None

    families = resolver.families()
    published_sources = {
        item.source
        for family in families
        for item in family.sources
    }

    boundary_rows = []
    for family in families:
        if not family.sources:
            continue
        item = family.sources[-1]
        doc = connector.retrieve(item.source)
        if doc.error or not doc.content:
            continue
        parsed = connector.parse(bytes(doc.content)) or {}
        draw_date_text = str(parsed.get("draw_date") or "")
        if not draw_date_text or draw_date_text == "Unknown":
            continue
        try:
            draw_date = parse_date(draw_date_text)
        except ValueError:
            continue
        boundary_rows.append(
            (
                draw_date,
                item.drawno,
                item.source,
                family.label or family.option,
                parsed.get("lottery_name") or "",
            )
        )

    if not boundary_rows:
        print("No usable published legacy boundary row could be established.")
        return 2

    boundary_rows.sort()
    boundary_date, boundary_drawno, boundary_source, boundary_family, boundary_name = boundary_rows[0]
    print("Observed earliest published family boundary:")
    print("   family:", boundary_family)
    print("   source:", boundary_source)
    print("   held date:", boundary_date.date().isoformat())
    print("   parsed name:", " ".join(str(boundary_name).split()))

    print("\nDirect legacy continuity profile")
    valid = []
    pre_cutoff = []
    target_month_records = []
    inspected = 0
    consecutive_empty = 0
    stop_reason = "address space exhausted"

    for drawno in range(boundary_drawno - 1, 0, -1):
        inspected += 1
        source = f"legacy:{drawno}"
        doc = connector.retrieve(source)
        if doc.error or not doc.content:
            consecutive_empty += 1
            if consecutive_empty >= MAX_CONSECUTIVE_EMPTY:
                stop_reason = f"stalled after {MAX_CONSECUTIVE_EMPTY} consecutive unusable addresses"
                break
            continue

        parsed = connector.parse(bytes(doc.content)) or {}
        draw_date_text = str(parsed.get("draw_date") or "")
        lottery_name = " ".join(str(parsed.get("lottery_name") or "").split())
        if not draw_date_text or draw_date_text == "Unknown" or not lottery_name:
            consecutive_empty += 1
            if consecutive_empty >= MAX_CONSECUTIVE_EMPTY:
                stop_reason = f"stalled after {MAX_CONSECUTIVE_EMPTY} consecutive unusable addresses"
                break
            continue

        try:
            draw_date = parse_date(draw_date_text)
        except ValueError:
            consecutive_empty += 1
            if consecutive_empty >= MAX_CONSECUTIVE_EMPTY:
                stop_reason = f"stalled after {MAX_CONSECUTIVE_EMPTY} consecutive unusable addresses"
                break
            continue

        consecutive_empty = 0
        indexed = source in published_sources
        item = (source, draw_date, lottery_name, indexed)
        valid.append(item)
        print(
            f"   VALID {source} | {draw_date.date().isoformat()} | "
            f"{'INDEXED' if indexed else 'UNINDEXED'} | {lottery_name}"
        )

        if draw_date < TARGET_CUTOFF:
            pre_cutoff.append(item)

        if draw_date.strftime("%Y-%m") == TARGET_MONTH:
            target_month_records.append(item)
            if len(target_month_records) >= TARGET_MONTH_RECORDS:
                stop_reason = (
                    f"cross-month target reached ({TARGET_MONTH_RECORDS} verified records in {TARGET_MONTH})"
                )
                break

    date_inversions = 0
    for previous, current in zip(valid, valid[1:]):
        if current[1] > previous[1]:
            date_inversions += 1

    print("\n=== DIRECT LEGACY CONTINUITY SUMMARY ===")
    print("boundary source:", boundary_source)
    print("boundary held date:", boundary_date.date().isoformat())
    print("addresses inspected:", inspected)
    print("valid legacy PDFs below published boundary:", len(valid))
    print("verified records held before 2017-08-23:", len(pre_cutoff))
    print("unindexed verified records:", sum(1 for item in valid if not item[3]))
    print("date inversions while addresses descended:", date_inversions)
    if valid:
        dates = [item[1] for item in valid]
        print("observed valid date span:", min(dates).date().isoformat(), "->", max(dates).date().isoformat())
        month_counts = Counter(d.strftime("%Y-%m") for d in dates)
        print(
            "months observed:",
            ", ".join(f"{month}={month_counts[month]}" for month in sorted(month_counts)),
        )
    print(f"verified records in target month {TARGET_MONTH}:", len(target_month_records))
    print("consecutive unusable addresses at stop:", consecutive_empty)
    print("stop reason:", stop_reason)
    print(
        "cross-month hidden transport continuity proven:",
        "YES" if target_month_records else "NOT PROVEN",
    )
    print(
        "direct legacy transport continues below published index cutoff:",
        "YES" if pre_cutoff else "NOT PROVEN",
    )
    print("No Collector result or Memory state was changed by this probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

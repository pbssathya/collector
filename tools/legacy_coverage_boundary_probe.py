from __future__ import annotations

from datetime import datetime

from collector.domains.registry import DomainRegistry


DOMAIN = "games/chance/lottery/kerala"


def parse_date(value: str):
    return datetime.strptime(value, "%d/%m/%Y").date()


def main() -> int:
    print("=== KERALA LEGACY OFFICIAL COVERAGE BOUNDARY PROBE ===")
    print("preservation: NO")
    print("purpose: distinguish source-history exhaustion from genuine no-draw dates\n")

    connector = DomainRegistry().get_connector(DOMAIN)
    assert connector is not None

    resolver = getattr(connector, "legacy_history_resolver", None)
    assert resolver is not None

    families = resolver.families()
    print("legacy families with published rows:", len(families))

    oldest_seen = []
    failures = []

    for family in families:
        if not family.sources:
            continue

        # family.sources is newest->oldest in the published family-local sequence.
        item = family.sources[-1]
        source = item.source
        doc = connector.retrieve(source)
        if doc.error or not doc.content:
            failures.append(f"{family.option}:{source}:fetch:{doc.error}")
            print(f"{family.label or family.option}: {source} | FETCH FAILED | {doc.error}")
            continue

        parsed = connector.parse(bytes(doc.content)) or {}
        draw_date_text = parsed.get("draw_date")
        name = " ".join(str(parsed.get("lottery_name") or "").split())
        if not draw_date_text or draw_date_text == "Unknown":
            failures.append(f"{family.option}:{source}:date")
            print(f"{family.label or family.option}: {source} | DATE UNKNOWN | {name}")
            continue

        draw_date = parse_date(str(draw_date_text))
        oldest_seen.append((draw_date, source, family.option, family.label, name, item.sequence))
        print(
            f"{family.label or family.option}: {source} | {draw_date.isoformat()} | "
            f"sequence={item.sequence} | {name}"
        )

    print("\n=== COVERAGE SUMMARY ===")
    if oldest_seen:
        oldest_seen.sort()
        print("earliest oldest-family row:", oldest_seen[0][0].isoformat(), oldest_seen[0][1])
        print("latest oldest-family row:", oldest_seen[-1][0].isoformat(), oldest_seen[-1][1])
        pre_2017 = [item for item in oldest_seen if item[0].year < 2017]
        print("families whose published legacy history reaches pre-2017:", len(pre_2017))
        print("families whose oldest published row is in 2017:", sum(item[0].year == 2017 for item in oldest_seen))

    print("failures:", len(failures))
    for failure in failures:
        print("  ", failure)

    print("\nNo Collector result or Memory state was changed by this probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

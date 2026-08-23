from __future__ import annotations

from datetime import datetime

from collector.domains.registry import DomainRegistry


DOMAIN = "games/chance/lottery/kerala"
PROBE_DEPTH = 40
TARGET_CUTOFF = datetime.strptime("23/08/2017", "%d/%m/%Y")


def parse_date(value: str):
    return datetime.strptime(value, "%d/%m/%Y")


def main() -> int:
    print("=== KERALA LEGACY DIRECT-BELOW-INDEX PROBE ===")
    print("preservation: NO")
    print("purpose: test whether the already-proven direct legacy transport continues below the published history index cutoff")
    print(f"bounded probe depth: {PROBE_DEPTH} addresses below one observed boundary source\n")

    connector = DomainRegistry().get_connector(DOMAIN)
    assert connector is not None
    resolver = getattr(connector, "legacy_history_resolver", None)
    assert resolver is not None

    boundary_rows = []
    for family in resolver.families():
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
        boundary_rows.append((draw_date, item.drawno, item.source, family.label or family.option, parsed.get("lottery_name") or ""))

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

    print("\nDirect legacy transport probe")
    valid = []
    pre_cutoff = []
    empties = 0

    for drawno in range(boundary_drawno - 1, max(0, boundary_drawno - PROBE_DEPTH - 1), -1):
        source = f"legacy:{drawno}"
        doc = connector.retrieve(source)
        if doc.error or not doc.content:
            empties += 1
            continue

        parsed = connector.parse(bytes(doc.content)) or {}
        draw_date_text = str(parsed.get("draw_date") or "")
        lottery_name = " ".join(str(parsed.get("lottery_name") or "").split())
        if not draw_date_text or draw_date_text == "Unknown" or not lottery_name:
            empties += 1
            continue

        try:
            draw_date = parse_date(draw_date_text)
        except ValueError:
            empties += 1
            continue

        item = (source, draw_date, lottery_name)
        valid.append(item)
        print(f"   VALID {source} | {draw_date.date().isoformat()} | {lottery_name}")

        if draw_date < TARGET_CUTOFF:
            pre_cutoff.append(item)
            if len(pre_cutoff) >= 3:
                break

    print("\n=== DIRECT LEGACY CONTINUITY SUMMARY ===")
    print("boundary source:", boundary_source)
    print("boundary held date:", boundary_date.date().isoformat())
    print("addresses inspected:", min(PROBE_DEPTH, max(0, boundary_drawno - 1) - max(0, boundary_drawno - PROBE_DEPTH - 1)))
    print("valid legacy PDFs below published boundary:", len(valid))
    print("verified records held before 2017-08-23:", len(pre_cutoff))
    for source, draw_date, lottery_name in pre_cutoff:
        print("   ", source, "|", draw_date.date().isoformat(), "|", lottery_name)
    print("direct legacy transport continues below published index cutoff:", "YES" if pre_cutoff else "NOT PROVEN IN THIS BOUNDED WINDOW")
    print("No Collector result or Memory state was changed by this probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

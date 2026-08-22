from __future__ import annotations

import sys

from collector.collect import collect


DOMAIN = "games/chance/lottery/kerala"
DEFAULT_SOURCES = ["75357", "74290", "75170"]


def main() -> int:
    sources = sys.argv[1:] or DEFAULT_SOURCES
    failures = []

    print("=== STRUCTURED KERALA PARSER VALIDATION ===")
    for source in sources:
        report = collect(DOMAIN, source, store=False, requester="living-habitat")
        parsed = (report.get("data") or {}).get("parsed") or {}
        status = (report.get("execution") or {}).get("status")
        name = parsed.get("lottery_name")
        draw_date = parsed.get("draw_date")
        first_prize = parsed.get("first_prize")
        tiers = parsed.get("prize_tiers") or []

        ok = (
            status in ("success", "partial")
            and name not in (None, "", "Unknown")
            and draw_date not in (None, "", "Unknown")
            and first_prize not in (None, "", "Unknown")
            and len(tiers) > 0
        )

        mark = "✅" if ok else "❌"
        print(
            f"{mark} {source} | {status} | {draw_date} | {name} | "
            f"first={first_prize} | tiers={len(tiers)}"
        )
        if not ok:
            failures.append(source)

    print("\nresult:", "PASSED" if not failures else "FAILED")
    if failures:
        print("failed sources:", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

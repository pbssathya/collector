from __future__ import annotations

from datetime import datetime

from collector.domains.registry import DomainRegistry


DOMAIN = "games/chance/lottery/kerala"
STALL_LAST_DRAWNO = 56538
WINDOW_SIZE = 100
MAX_WINDOWS = 10
EVIDENCE_TARGET = 3


def main() -> int:
    print("=== KERALA HIDDEN LEGACY ADDRESS-DESERT PROBE ===")
    print("preservation: NO")
    print("purpose: characterize the unresolved address desert below the 2017 recovery stall")
    print("production stall safety remains unchanged: 100 consecutive unusable addresses")
    print("last address already inspected by production scan:", f"legacy:{STALL_LAST_DRAWNO}")
    print("diagnostic window size:", WINDOW_SIZE)
    print("maximum diagnostic windows:", MAX_WINDOWS)
    print("evidence target:", EVIDENCE_TARGET, "verified records")

    connector = DomainRegistry().get_connector(DOMAIN)
    assert connector is not None

    inspected = 0
    valid: list[tuple[str, datetime, str]] = []
    stop_reason = f"bounded diagnostic exhausted ({MAX_WINDOWS} windows)"

    next_drawno = STALL_LAST_DRAWNO - 1

    for window_number in range(1, MAX_WINDOWS + 1):
        window_start = next_drawno
        window_end = max(1, window_start - WINDOW_SIZE + 1)
        window_valid_before = len(valid)
        window_inspected_before = inspected

        print(
            f"\nWINDOW {window_number:02d}: "
            f"legacy:{window_start} -> legacy:{window_end}"
        )

        for drawno in range(window_start, window_end - 1, -1):
            inspected += 1
            source = f"legacy:{drawno}"
            doc = connector.retrieve(source)
            if doc.error or not doc.content:
                continue

            parsed = connector.parse(bytes(doc.content)) or {}
            draw_date_text = str(parsed.get("draw_date") or "")
            lottery_name = " ".join(str(parsed.get("lottery_name") or "").split())
            if not draw_date_text or draw_date_text == "Unknown" or not lottery_name:
                continue

            try:
                draw_date = datetime.strptime(draw_date_text, "%d/%m/%Y")
            except ValueError:
                continue

            valid.append((source, draw_date, lottery_name))
            print(
                f"   VALID {source} | {draw_date.date().isoformat()} | {lottery_name}"
            )

            if len(valid) >= EVIDENCE_TARGET:
                stop_reason = f"evidence target reached ({EVIDENCE_TARGET} verified records)"
                break

        found_this_window = len(valid) - window_valid_before
        inspected_this_window = inspected - window_inspected_before
        print(
            f"   window summary: {inspected_this_window} inspected | "
            f"{found_this_window} valid"
        )

        if len(valid) >= EVIDENCE_TARGET or window_end <= 1:
            break

        next_drawno = window_end - 1

    print("\n=== ADDRESS-DESERT PROBE SUMMARY ===")
    print("addresses inspected:", inspected)
    print("verified records found:", len(valid))
    if valid:
        dates = [item[1] for item in valid]
        print("observed valid date span:", min(dates).date().isoformat(), "->", max(dates).date().isoformat())
        print("first verified continuation source:", valid[0][0])
        print("address gap from production stall:", STALL_LAST_DRAWNO - int(valid[0][0].split(":", 1)[1]))
        for source, draw_date, lottery_name in valid:
            print("   ", source, "|", draw_date.date().isoformat(), "|", lottery_name)
    else:
        print("first verified continuation source: NOT FOUND")
    print("stop reason:", stop_reason)
    print("production safety threshold changed: NO")
    print("source coverage proven: NO")
    print("No Collector result or Memory state was changed by this probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

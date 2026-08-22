from collector.collect import collect
from collector.domains.registry import DomainRegistry


DOMAIN = "games/chance/lottery/kerala"
KNOWN_CURRENT = "73635"
EXPECTED_PREVIOUS = "73081"


def main() -> int:
    print("=== KERALA OFFICIAL HISTORY RESOLVER VALIDATION ===")
    print("current source:", KNOWN_CURRENT)
    print("expected previous published source:", EXPECTED_PREVIOUS)
    print("preservation: NO\n")

    connector = DomainRegistry().get_connector(DOMAIN)
    if connector is None or not hasattr(connector, "previous_source"):
        print("❌ connector does not expose previous_source")
        return 1

    previous = connector.previous_source(KNOWN_CURRENT)
    print("resolved previous source:", previous)
    if previous != EXPECTED_PREVIOUS:
        print("❌ resolver did not discover the proven 2022 transition")
        return 1

    report = collect(DOMAIN, previous, store=False, requester="history-resolver-validation")
    parsed = (report.get("data") or {}).get("parsed") or {}
    status = (report.get("execution") or {}).get("status")
    draw_date = parsed.get("draw_date")
    lottery_name = " ".join(str(parsed.get("lottery_name", "")).split())

    print("resolved source status:", status)
    print("resolved source date:", draw_date)
    print("resolved source name:", lottery_name)

    passed = (
        status in ("success", "partial")
        and draw_date == "23/03/2022"
        and "AK-541" in lottery_name
    )

    print("\nresult:", "PASSED" if passed else "FAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

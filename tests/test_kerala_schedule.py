from collector.domains.games.chance.lottery.kerala.schedule import (
    ScheduleConnector,
    parse_upcoming_draws,
)
from collector.domains.registry import DomainRegistry


SAMPLE_HTML = b"""
<html><body>
<table>
  <tr><th>Sl No</th><th>Lottery</th><th>Draw Date and Time</th><th>Draw Venue</th></tr>
  <tr><td>1</td><td>STHREE-SAKTHI-10/11/2025 (SS-534)</td><td>25-08-2026 3:00 PM</td><td>GORKY BHAVAN</td></tr>
  <tr><td>2</td><td>KARUNYA PLUS-10/11/2025 (KN-638)</td><td>27-08-2026 3:00 PM</td><td>GORKY BHAVAN</td></tr>
  <tr><td>3</td><td>SUVARNA KERALAM-10/11/2025 (SK-67)</td><td>28-08-2026 3:00 PM</td><td>GORKY BHAVAN</td></tr>
</table>
</body></html>
"""


def test_upcoming_schedule_parser_returns_only_listed_draw_dates():
    parsed = parse_upcoming_draws(SAMPLE_HTML)

    assert parsed is not None
    assert parsed["source_kind"] == "official_upcoming_draw_schedule"
    draws = parsed["upcoming_draws"]
    assert [item["draw_date"] for item in draws] == [
        "2026-08-25",
        "2026-08-27",
        "2026-08-28",
    ]
    assert "2026-08-26" not in {item["draw_date"] for item in draws}


def test_upcoming_schedule_parser_extracts_draw_code_and_time():
    parsed = parse_upcoming_draws(SAMPLE_HTML)

    first = parsed["upcoming_draws"][0]
    assert first["draw_code"] == "SS-534"
    assert first["draw_time"] == "15:00"
    assert first["lottery_name"] == "STHREE-SAKTHI-10/11/2025"


def test_schedule_connector_has_one_explicit_source():
    connector = ScheduleConnector()

    assert connector.supports("upcoming")
    assert not connector.supports("75360")


def test_schedule_domain_is_registered():
    connector = DomainRegistry().get_connector(
        "games/chance/lottery/kerala/schedule"
    )

    assert isinstance(connector, ScheduleConnector)

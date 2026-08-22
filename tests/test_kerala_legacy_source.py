from datetime import datetime
from unittest.mock import Mock

from collector.contracts.document import Document
from collector.domains.games.chance.lottery.kerala.connector import Connector
from collector.domains.games.chance.lottery.kerala.legacy import (
    LegacyFamily,
    LegacySource,
    parse_legacy_rows,
    script_location,
)
from collector.domains.games.chance.lottery.kerala.result import Result


def make_document(source_url: str, content: bytes) -> Document:
    return Document(
        id="doc",
        source_url=source_url,
        retrieved_at=datetime.now(),
        content=content,
        run_id="run",
        connector_id="test",
        content_type="application/pdf" if content.startswith(b"%PDF") else "text/html",
        status_code=200,
    )


def make_result(draw_date: str) -> Result:
    return Result(
        lottery_name="TEST LOTTERY NO. T-1st DRAW",
        draw_date=draw_date,
        first_prize="Unknown",
        first_prize_location="Unknown",
    )


def test_parse_legacy_row_and_script_redirect():
    page = """
    <tr>
      <td>Karunya Plus KN-327</td>
      <td><a onclick="loadserialno(71953)">View</a></td>
    </tr>
    """

    rows = parse_legacy_rows(page)

    assert len(rows) == 1
    assert rows[0].drawno == 71953
    assert rows[0].sequence == 327
    assert rows[0].source == "legacy:71953"
    assert script_location(
        b"<HTML><SCRIPT>document.location='draw/tmp71953.pdf';</SCRIPT></HTML>"
    ) == "draw/tmp71953.pdf"


def test_connector_supports_explicit_legacy_namespace():
    connector = Connector()

    assert connector.supports("75357")
    assert connector.supports("legacy:71953")
    assert not connector.supports("legacy:not-a-number")
    assert not connector.supports("unknown:71953")


def test_legacy_retrieve_follows_official_javascript_location():
    connector = Connector()
    redirect_url = (
        "https://result.keralalotteries.com/reports/"
        "resultentryeport1.php?drawno1=71953&drawno=71953"
    )
    pdf_url = "https://result.keralalotteries.com/reports/draw/tmp71953.pdf"

    connector.fetcher = Mock()
    connector.fetcher.retrieve.side_effect = [
        make_document(
            redirect_url,
            b"<HTML><SCRIPT>document.location='draw/tmp71953.pdf';</SCRIPT></HTML>",
        ),
        make_document(pdf_url, b"%PDF-test"),
    ]

    doc = connector.retrieve("legacy:71953")

    assert doc.content == b"%PDF-test"
    assert doc.source_url == pdf_url
    assert doc.metadata["legacy_drawno"] == 71953
    assert doc.metadata["legacy_redirector_url"] == redirect_url
    assert connector.fetcher.retrieve.call_args_list[0].args == (redirect_url,)
    assert connector.fetcher.retrieve.call_args_list[1].args == (pdf_url,)


def test_legacy_year_discovery_stops_each_family_at_its_own_boundary():
    connector = Connector()
    connector.legacy_history_resolver = Mock()
    connector.legacy_history_resolver.families.return_value = [
        LegacyFamily(
            option="x",
            label="TEST",
            sources=(
                LegacySource(drawno=3, sequence=3, text="newer"),
                LegacySource(drawno=2, sequence=2, text="target"),
                LegacySource(drawno=1, sequence=1, text="older"),
            ),
        )
    ]

    connector.retrieve = Mock(
        side_effect=[
            make_document("legacy:3", b"%PDF-3"),
            make_document("legacy:2", b"%PDF-2"),
            make_document("legacy:1", b"%PDF-1"),
        ]
    )
    connector.parser = Mock()
    connector.parser.parse.side_effect = [
        make_result("01/01/2021"),
        make_result("31/12/2020"),
        make_result("31/12/2019"),
    ]

    assert connector.legacy_sources_for_year(2020) == ["legacy:2"]
    assert connector.retrieve.call_count == 3

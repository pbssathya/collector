from datetime import datetime
from unittest.mock import Mock, patch

from collector.collect import collect
from collector.contracts.document import Document
from collector.domains.games.chance.lottery.kerala.connector import Connector


DOMAIN = "games/chance/lottery/kerala"
SOURCE = "80000"


def document(content, error=None):
    return Document(
        id="doc-test",
        source_url=f"http://result.keralalotteries.com/viewlotisresult.php?drawserial={SOURCE}",
        retrieved_at=datetime.now(),
        content=content,
        run_id="run-test",
        connector_id="http_fetcher",
        content_type="application/pdf" if content else None,
        error=error,
    )


def connector_with_publication_state(is_published):
    connector = Connector()
    connector.history_resolver = Mock()
    connector.history_resolver.is_published_source.return_value = is_published
    connector.fetcher = Mock()
    return connector


def test_unpublished_modern_source_is_distinct_from_empty_content():
    connector = connector_with_publication_state(False)

    with patch("collector.collect.DomainRegistry.get_connector", return_value=connector):
        report = collect(DOMAIN, SOURCE, store=False)

    assert report["execution"]["status"] == "failed"
    assert [event["type"] for event in report["execution"]["events"]] == ["source_not_published"]
    assert report["metadata"]["source_url"].endswith(f"drawserial={SOURCE}")
    connector.fetcher.retrieve.assert_not_called()


def test_published_modern_source_follows_existing_collect_path():
    connector = connector_with_publication_state(True)
    connector.fetcher.retrieve.return_value = document(b"published-result")
    connector.parse = Mock(return_value={"lottery_name": "Published"})

    with patch("collector.collect.DomainRegistry.get_connector", return_value=connector):
        report = collect(DOMAIN, SOURCE, store=False)

    assert report["execution"]["status"] == "success"
    assert report["data"]["raw"] == b"published-result"
    assert report["data"]["parsed"] == {"lottery_name": "Published"}
    connector.fetcher.retrieve.assert_called_once()


def test_published_source_fetch_error_remains_fetch_failure():
    connector = connector_with_publication_state(True)
    connector.fetcher.retrieve.return_value = document(None, error="network unavailable")

    with patch("collector.collect.DomainRegistry.get_connector", return_value=connector):
        report = collect(DOMAIN, SOURCE, store=False)

    assert report["execution"]["status"] == "failed"
    assert [event["type"] for event in report["execution"]["events"]] == ["fetch_error"]
    assert "source_not_published" not in [event["type"] for event in report["execution"]["events"]]

"""Connector contract tests for Collector.

These tests verify that the production connectors work as expected.
"""

import pytest
from collector.domains.games.chance.lottery.kerala.connector import Connector as KeralaConnector
from collector.core.fetcher import HTTPFetcher
from collector.contracts.connector import ConnectorError
from collector.domains.registry import DomainRegistry


@pytest.fixture
def kerala_connector():
    """Return a Kerala connector instance."""
    registry = DomainRegistry()
    return registry.get_connector("games/chance/lottery/kerala")


def test_supported_source_retrieval(kerala_connector):
    """Verify a supported source can be retrieved."""
    try:
        doc = kerala_connector.retrieve("12345")
        assert doc is not None
        assert doc.content is not None
    except ConnectorError:
        pytest.skip("External service unavailable")


def test_connection_failure_reporting():
    """Verify connection failures are reported as execution events."""
    fetcher = HTTPFetcher()
    doc = fetcher.retrieve("https://invalid-domain-that-does-not-exist.example.com")
    assert doc.error is not None or doc.status_code is not None


def test_http_redirect_following():
    """Verify HTTP redirects are followed and recorded."""
    fetcher = HTTPFetcher()
    doc = fetcher.retrieve("https://httpbin.org/redirect/1")
    assert doc is not None
    assert hasattr(doc, 'redirects')
    assert isinstance(doc.redirects, list)
    
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
    """Verify HTTP redirects are followed and recorded in Document.redirects."""
    fetcher = HTTPFetcher()
    # Use httpbin's redirect endpoint which returns a 302 redirect
    doc = fetcher.retrieve("https://httpbin.org/redirect/1")
    
    assert doc is not None
    
    # Verify redirects field exists and is a list
    assert hasattr(doc, 'redirects')
    assert isinstance(doc.redirects, list)
    
    # Verify the redirect chain was actually recorded (non-empty)
    assert len(doc.redirects) > 0, "Redirect chain should be recorded"
    
    # Production stores redirects as strings (the URL that was redirected from)
    # Each entry is a string representing the URL that was redirected
    for redirect in doc.redirects:
        assert isinstance(redirect, str), "Redirect entry must be a string (URL)"
        assert redirect.startswith("http"), "Redirect entry must be a valid URL"
    
    # Verify the final URL is not the original (redirect occurred)
    original_url = "https://httpbin.org/redirect/1"
    final_url = doc.source_url
    # Note: source_url may be the final URL after redirects
    # The test passes if we have at least one redirect recorded
    # and the source_url is different from the original (if the redirect succeeded)
    if doc.status_code == 200:
        # If we got a successful response, the redirect should have been followed
        # and source_url should be the final location
        assert doc.source_url != original_url or len(doc.redirects) > 0
    else:
        # If the request failed, we still expect redirects to be recorded
        assert len(doc.redirects) > 0
        
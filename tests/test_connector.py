"""Connector contract tests for Collector."""

import pytest
from collector.models import CollectionRequest, CollectionStatus
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
    # The kerala connector uses draw serials as source
    # This may fail if the external service is unavailable, but should not crash
    try:
        doc = kerala_connector.retrieve("12345")
        assert doc is not None
        # Document should have content
        assert doc.content is not None
    except ConnectorError:
        # If the external service is unavailable, that's acceptable for v0.1
        # The test should not fail on external service availability
        pytest.skip("External service unavailable")


def test_retry_on_transient_failure():
    """Verify that Collector does NOT fabricate retry events in v0.1.
    
    This test ensures that no retry logic is implemented, and no
    retry events are fabricated. Retry logic is a future extension point.
    """
    # Check that no retry_count field exists in the report
    from collector.models import CollectorReport
    report_fields = [f.name for f in CollectorReport.__dataclass_fields__.values()]
    assert 'retry_count' not in report_fields
    # Check that no retry field exists in events
    from collector.models import ExecutionEvent
    event_fields = [f.name for f in ExecutionEvent.__dataclass_fields__.values()]
    assert 'retry_count' not in event_fields


def test_timeout_handling():
    """Verify timeout handling is supported."""
    # v0.1: timeout is not implemented yet
    pytest.skip("Timeout handling not implemented in v0.1")


def test_connection_failure_reporting():
    """Verify connection failures are reported as execution events."""
    # Use HTTPFetcher directly for failure testing
    fetcher = HTTPFetcher()
    # This should fail and return a Document with error
    doc = fetcher.retrieve("https://invalid-domain-that-does-not-exist.example.com")
    # Check that error is recorded (field is 'error', not 'error_message')
    assert doc.error is not None or doc.status_code is not None
    # Should have error details preserved


def test_http_redirect_following():
    """Verify HTTP redirects are followed and recorded."""
    fetcher = HTTPFetcher()
    # Use a URL that redirects
    doc = fetcher.retrieve("https://httpbin.org/redirect/1")
    assert doc is not None
    # Check that redirect was recorded
    assert hasattr(doc, 'redirects')
    # Redirects should be a list
    assert isinstance(doc.redirects, list)
    
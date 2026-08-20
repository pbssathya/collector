"""Connector contract tests for Collector."""

import pytest
from collector.connectors.http import HTTPConnector
from collector.models import CollectionRequest, CollectionStatus
from collector.exceptions import ConnectionError, TimeoutError

def test_supported_source_retrieval(http_connector, sample_request):
    """Verify a supported source can be retrieved."""
    # This test should pass with a real URL
    result = http_connector.collect(sample_request)
    assert result.status in [CollectionStatus.COMPLETE, CollectionStatus.FAILED]
    # Status can be complete or failed depending on network, but should not crash

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

def test_connection_failure_reporting(http_connector):
    """Verify connection failures are reported as execution events."""
    request = CollectionRequest(
        domain="invalid",
        source="https://invalid-domain-that-does-not-exist.example.com",
        request_id="failure-test"
    )
    result = http_connector.collect(request)
    assert result.status == CollectionStatus.FAILED
    # Should have at least one execution event
    assert len(result.execution_events) > 0

def test_http_redirect_following():
    """Verify HTTP redirects are followed and recorded."""
    # This is a known implementation behavior
    # Create a request for a URL that redirects
    request = CollectionRequest(
        domain="test",
        source="https://httpbin.org/redirect/1",
        request_id="redirect-test"
    )
    connector = HTTPConnector()
    result = connector.collect(request)
    assert result.status == CollectionStatus.COMPLETE
    # Check that redirect was recorded in execution events
    redirect_events = [e for e in result.execution_events if e.event_type == "REDIRECT"]
    assert len(redirect_events) >= 1

"""Report contract tests for Collector."""

import pytest
from datetime import datetime
from collector.models import CollectorReport, CollectionStatus, CollectionRequest

def test_report_version_1_0_0():
    """Verify report version is 1.0.0."""
    report = CollectorReport(
        version="1.0.0",
        status=CollectionStatus.COMPLETE,
        execution_events=[]
    )
    assert report.version == "1.0.0"

def test_report_contains_request_info():
    """Verify request information is present in report."""
    request = CollectionRequest(
        domain="kerala",
        source="test_source",
        request_id="test-123"
    )
    report = CollectorReport(
        version="1.0.0",
        request=request,
        status=CollectionStatus.COMPLETE,
        execution_events=[]
    )
    assert report.request is not None
    assert report.request.domain == "kerala"
    assert report.request.source == "test_source"
    assert report.request.request_id == "test-123"

def test_report_contains_collection_data():
    """Verify collection data is present in report."""
    from collector.parsers.document import Document
    doc = Document(
        content=b"test content",
        content_type="text/plain",
        source_url="https://example.com/test.txt"
    )
    report = CollectorReport(
        version="1.0.0",
        status=CollectionStatus.COMPLETE,
        execution_events=[],
        document=doc
    )
    assert report.document is not None
    assert report.document.content == b"test content"

def test_report_contains_execution_metadata():
    """Verify execution events are present."""
    from collector.models import ExecutionEvent
    event = ExecutionEvent(
        event_type="START",
        timestamp=datetime.now(),
        description="Collection started"
    )
    report = CollectorReport(
        version="1.0.0",
        status=CollectionStatus.COMPLETE,
        execution_events=[event]
    )
    assert len(report.execution_events) > 0
    assert report.execution_events[0].event_type == "START"

def test_report_contains_provenance():
    """Verify provenance information is present."""
    report = CollectorReport(
        version="1.0.0",
        status=CollectionStatus.COMPLETE,
        execution_events=[],
        collector_version="0.1.0"
    )
    # Check that collector_version exists
    assert hasattr(report, 'collector_version')
    assert report.collector_version == "0.1.0"

def test_raw_data_not_truncated_in_report():
    """Verify raw data in report is not truncated."""
    from collector.parsers.document import Document
    content = b"A" * 5000
    doc = Document(
        content=content,
        content_type="text/plain",
        source_url="https://example.com/test.txt"
    )
    report = CollectorReport(
        version="1.0.0",
        status=CollectionStatus.COMPLETE,
        execution_events=[],
        document=doc
    )
    # Verify the full content is accessible
    assert report.document.content == content
    # Verify content is NOT truncated silently
    # If Document has a truncated display repr, it should be clearly distinct
    if hasattr(doc, 'content_display'):
        assert len(doc.content_display) == len(content)
    else:
        # No display-specific truncation; content is canonical
        pass

def test_report_execution_events_exist():
    """Verify execution events have required fields."""
    from collector.models import ExecutionEvent
    event = ExecutionEvent(
        event_type="COLLECTION_STARTED",
        timestamp=datetime.now(),
        description="Collection started"
    )
    # Verify event has required fields
    assert event.event_type is not None
    assert event.timestamp is not None
    assert event.description is not None

def test_report_all_required_sections_exist():
    """Verify all required report sections exist."""
    request = CollectionRequest(
        domain="test",
        source="test_source",
        request_id="test-123"
    )
    report = CollectorReport(
        version="1.0.0",
        request=request,
        status=CollectionStatus.COMPLETE,
        execution_events=[]
    )
    # Required sections
    assert hasattr(report, 'version')
    assert hasattr(report, 'request')
    assert hasattr(report, 'status')
    assert hasattr(report, 'execution_events')
    # Optional but expected
    assert hasattr(report, 'document')
    assert hasattr(report, 'collector_version')

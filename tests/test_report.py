"""Report contract tests for Collector.

These tests verify that the standardized CollectorReport contract:
- Preserves complete canonical raw data
- Contains all required sections
- Does not contain analysis, decisions, or recommendations
- Includes provenance and execution metadata
"""

import pytest
from datetime import datetime
from collector.models import (
    CollectorReport,
    CollectionStatus,
    CollectionRequest,
    ExecutionEvent,
    Document,
)


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
    """Verify collection data (Document) is present in report with complete content."""
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
    # Verify COMPLETE canonical content is preserved
    assert report.document.content == b"test content"


def test_report_contains_execution_metadata():
    """Verify execution events are present with timestamps."""
    event = ExecutionEvent(
        event_type="COLLECTION_STARTED",
        timestamp=datetime.now(),
        description="Collection started"
    )
    report = CollectorReport(
        version="1.0.0",
        status=CollectionStatus.COMPLETE,
        execution_events=[event]
    )
    assert len(report.execution_events) > 0
    assert report.execution_events[0].event_type == "COLLECTION_STARTED"
    assert report.execution_events[0].timestamp is not None


def test_report_contains_provenance():
    """Verify provenance information (collector_version) is present."""
    report = CollectorReport(
        version="1.0.0",
        status=CollectionStatus.COMPLETE,
        execution_events=[],
        collector_version="0.1.0"
    )
    # Check that collector_version exists and is set
    assert hasattr(report, 'collector_version')
    assert report.collector_version == "0.1.0"


def test_raw_data_not_truncated_in_report():
    """Verify raw data in report's Document is NOT truncated."""
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
    # Verify the COMPLETE content is accessible via the Document
    assert report.document.content == content
    # Verify the content is NOT truncated (full length preserved)
    assert len(report.document.content) == 5000


def test_report_execution_events_have_timestamps():
    """Verify all execution events have timestamps."""
    event1 = ExecutionEvent(
        event_type="COLLECTION_STARTED",
        timestamp=datetime.now(),
        description="Collection started"
    )
    event2 = ExecutionEvent(
        event_type="COLLECTION_COMPLETED",
        timestamp=datetime.now(),
        description="Collection completed"
    )
    report = CollectorReport(
        version="1.0.0",
        status=CollectionStatus.COMPLETE,
        execution_events=[event1, event2]
    )
    for event in report.execution_events:
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)


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


def test_report_does_not_contain_analysis_or_decisions():
    """Verify the report has no analysis, recommendation, or decision fields."""
    report_fields = [f.name for f in CollectorReport.__dataclass_fields__.values()]
    # No analysis fields
    assert 'analysis' not in report_fields
    assert 'insights' not in report_fields
    # No recommendation fields
    assert 'recommendation' not in report_fields
    assert 'recommended_action' not in report_fields
    # No decision fields
    assert 'decision' not in report_fields
    assert 'verdict' not in report_fields
    # No severity fields
    assert 'severity' not in report_fields
    assert 'severity_level' not in report_fields
    
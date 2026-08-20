"""Report contract tests for Collector.

These tests verify that the production report dictionary
returned by collect() conforms to the expected contract.
"""

from unittest.mock import patch

from collector.collect import collect
from collector.contracts.document import Document


def test_report_version_1_0_0():
    """Verify report version is 1.0.0."""
    result = collect("games/chance/lottery/kerala", "invalid_source", store=False)
    assert result is not None
    assert result.get("report_version") == "1.0.0"


def test_report_contains_request_info():
    """Verify request information is present in report."""
    result = collect("games/chance/lottery/kerala", "invalid_source", store=False)
    assert result is not None
    assert "request" in result
    request = result["request"]
    assert "domain_path" in request
    assert "source" in request
    assert "requested_at" in request


def test_report_contains_execution_metadata():
    """Verify execution metadata is present in report."""
    result = collect("games/chance/lottery/kerala", "invalid_source", store=False)
    assert result is not None
    assert "execution" in result
    execution = result["execution"]
    assert "status" in execution
    assert "duration_ms" in execution
    assert "events" in execution


def test_report_contains_provenance():
    """Verify provenance information is present in report."""
    result = collect("games/chance/lottery/kerala", "invalid_source", store=False)
    assert result is not None
    assert "provenance" in result
    provenance = result["provenance"]
    assert "run_id" in provenance
    assert "collector_version" in provenance


def test_raw_data_not_truncated_in_report():
    """Verify the report preserves the complete raw material."""
    raw = bytes(range(256)) * 4
    document = Document(
        id="doc-test",
        source_url="https://example.test/raw",
        retrieved_at=__import__("datetime").datetime.now(),
        content=raw,
        run_id="run-test",
        connector_id="test-connector",
        content_type="application/octet-stream",
    )

    class TestConnector:
        def retrieve(self, source):
            return document

        def parse(self, content):
            return {"size": len(content)}

    with patch("collector.collect.DomainRegistry.get_connector", return_value=TestConnector()):
        result = collect("test/domain", "test-source", store=False)

    assert result is not None
    assert result["data"]["raw"] == raw
    assert len(result["data"]["raw"]) == len(raw)
    assert result["metadata"]["size_bytes"] == len(raw)


def test_report_statuses_are_strings():
    """Verify report uses string statuses, not enums."""
    result = collect("games/chance/lottery/kerala", "invalid_source", store=False)
    assert result is not None
    status = result["execution"]["status"]
    assert isinstance(status, str)
    # Production uses lowercase status values
    assert status in ["complete", "failed", "partial"]


def test_report_does_not_contain_analysis_or_decisions():
    """Verify the report has no analysis, recommendation, or decision fields."""
    result = collect("games/chance/lottery/kerala", "invalid_source", store=False)
    assert result is not None

    def collect_keys(obj, prefix=""):
        keys = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.add(full_key)
                keys.update(collect_keys(v, full_key))
        elif isinstance(obj, list):
            for item in obj:
                keys.update(collect_keys(item, prefix))
        return keys

    report_keys = collect_keys(result)

    # No analysis-related keys
    assert not any("analysis" in k.lower() for k in report_keys)
    assert not any("recommend" in k.lower() for k in report_keys)
    assert not any("decision" in k.lower() for k in report_keys)
    assert not any("severity" in k.lower() for k in report_keys)
    assert not any("insight" in k.lower() for k in report_keys)
    assert not any("verdict" in k.lower() for k in report_keys)


def test_event_events_are_dicts_not_objects():
    """Verify execution events are plain dictionaries with production keys."""
    result = collect("games/chance/lottery/kerala", "invalid_source", store=False)
    assert result is not None
    events = result["execution"]["events"]
    assert isinstance(events, list)
    if events:
        event = events[0]
        assert isinstance(event, dict)
        # Production uses 'type' and 'message' keys, not 'event_type'
        # Accept either format
        has_event_type = "event_type" in event or "type" in event
        assert has_event_type
        assert "timestamp" in event
        # Either 'description' or 'message' is present
        has_description = "description" in event or "message" in event
        assert has_description

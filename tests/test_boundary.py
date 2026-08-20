"""Architectural boundary tests for Collector.

These tests verify that Collector does NOT analyse, predict,
recommend, decide, or assign business meaning to data.
"""

import inspect
from collector.models import CollectorReport, ExecutionEvent
from collector.connectors.http import HTTPConnector
from collector.parsers.document import Document

def test_no_severity_classification():
    """Verify Collector has no severity enums."""
    import collector.models as models
    # Check for absence of severity-related classes
    assert not hasattr(models, 'Severity')
    assert not hasattr(models, 'SeverityLevel')
    # Check for absence of severity fields in report
    report_fields = [f.name for f in CollectorReport.__dataclass_fields__.values()]
    assert 'severity' not in report_fields
    assert 'severity_level' not in report_fields

def test_no_recommendation_fields():
    """Verify Collector does not produce recommendations."""
    report_fields = [f.name for f in CollectorReport.__dataclass_fields__.values()]
    assert 'recommendation' not in report_fields
    assert 'recommended_action' not in report_fields

def test_no_decision_fields():
    """Verify Collector does not produce decisions."""
    report_fields = [f.name for f in CollectorReport.__dataclass_fields__.values()]
    assert 'decision' not in report_fields
    assert 'verdict' not in report_fields

def test_no_business_interpretation():
    """Verify Collector does not assign business meaning."""
    # Check for absence of business interpretation methods
    connector_methods = [m for m in dir(HTTPConnector) if not m.startswith('_')]
    assert 'interpret' not in connector_methods
    assert 'classify' not in connector_methods

def test_report_does_not_contain_analysis():
    """Verify the report contains no analysis fields."""
    report_fields = [f.name for f in CollectorReport.__dataclass_fields__.values()]
    assert 'analysis' not in report_fields
    assert 'insights' not in report_fields

def test_collector_does_not_predict():
    """Verify Collector has no prediction capabilities."""
    document_methods = [m for m in dir(Document) if not m.startswith('_')]
    assert 'predict' not in document_methods
    assert 'forecast' not in document_methods

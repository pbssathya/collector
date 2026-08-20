"""Architectural boundary tests for Collector.

These tests verify that Collector does NOT analyse, predict,
recommend, decide, or assign business meaning to data.
"""

import inspect
from collector.models import CollectorReport, ExecutionEvent
from collector.core.fetcher import HTTPFetcher
from collector.contracts.document import Document


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
    fetcher_methods = [m for m in dir(HTTPFetcher) if not m.startswith('_')]
    assert 'interpret' not in fetcher_methods
    assert 'classify' not in fetcher_methods
    assert 'analyse' not in fetcher_methods


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


def test_no_connector_analysis_methods():
    """Verify connectors have no analysis methods."""
    from collector.domains.games.chance.lottery.kerala.connector import Connector as KeralaConnector
    connector = KeralaConnector()
    connector_methods = [m for m in dir(connector) if not m.startswith('_')]
    # Connector should only have retrieve, supports, parse
    assert 'retrieve' in connector_methods
    assert 'supports' in connector_methods
    assert 'parse' in connector_methods
    # No analysis methods
    assert 'analyse' not in connector_methods
    assert 'predict' not in connector_methods
    assert 'recommend' not in connector_methods
    assert 'decide' not in connector_methods
    
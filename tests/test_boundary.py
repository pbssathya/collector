"""Architectural boundary tests for Collector.

These tests verify that Collector does NOT analyse, predict,
recommend, decide, or assign business meaning to data.
They inspect the real production structures and code.
"""

from collector.core.fetcher import HTTPFetcher
from collector.contracts.document import Document
from collector.contracts.connector import Connector


def test_no_severity_classification():
    """Verify Collector has no severity enums or fields."""
    # Check that no severity-related classes exist in contracts
    assert not hasattr(Document, 'severity')
    assert not hasattr(Document, 'severity_level')
    # Check that no severity fields exist in the production report dict
    # The report is a plain dict returned by collect()
    import collector.collect as collect_module
    # Inspect the collect() function's return structure
    # It returns a dict with specific keys - none should be severity-related
    import inspect
    source = inspect.getsource(collect_module.collect)
    assert 'severity' not in source.lower()


def test_no_recommendation_fields():
    """Verify Collector does not produce recommendations."""
    import collector.collect as collect_module
    import inspect
    source = inspect.getsource(collect_module.collect)
    assert 'recommendation' not in source.lower()
    assert 'recommended_action' not in source.lower()


def test_no_decision_fields():
    """Verify Collector does not produce decisions."""
    import collector.collect as collect_module
    import inspect
    source = inspect.getsource(collect_module.collect)
    assert 'decision' not in source.lower()
    assert 'verdict' not in source.lower()


def test_no_business_interpretation():
    """Verify Collector does not assign business meaning."""
    # Check HTTPFetcher for interpretation methods
    fetcher_methods = [m for m in dir(HTTPFetcher) if not m.startswith('_')]
    assert 'interpret' not in fetcher_methods
    assert 'classify' not in fetcher_methods
    assert 'analyse' not in fetcher_methods


def test_report_does_not_contain_analysis():
    """Verify the report contains no analysis fields."""
    import collector.collect as collect_module
    import inspect
    source = inspect.getsource(collect_module.collect)
    assert 'analysis' not in source.lower()
    assert 'insights' not in source.lower()


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
    # Connector should have retrieve, supports, parse
    assert 'retrieve' in connector_methods
    assert 'supports' in connector_methods
    assert 'parse' in connector_methods
    # No analysis methods
    assert 'analyse' not in connector_methods
    assert 'predict' not in connector_methods
    assert 'recommend' not in connector_methods
    assert 'decide' not in connector_methods


def test_connector_contract_has_no_analysis():
    """Verify the base Connector contract has no analysis methods."""
    connector_methods = [m for m in dir(Connector) if not m.startswith('_')]
    # Abstract methods: retrieve, supports
    assert 'retrieve' in connector_methods
    assert 'supports' in connector_methods
    # No analysis methods
    assert 'analyse' not in connector_methods
    assert 'predict' not in connector_methods
    assert 'recommend' not in connector_methods
    assert 'decide' not in connector_methods
    
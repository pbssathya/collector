"""Pytest fixtures for Collector tests."""

import pytest
from collector.models import CollectionRequest, CollectionStatus
from collector.connectors.http import HTTPConnector
from collector.registry import DomainRegistry

@pytest.fixture
def sample_request():
    """Return a sample collection request."""
    return CollectionRequest(
        domain="kerala",
        source="https://www.keralalotteries.com/result",
        request_id="test-123"
    )

@pytest.fixture
def registry():
    """Return a domain registry with kerala registered."""
    reg = DomainRegistry()
    reg.register("kerala", HTTPConnector())
    return reg

@pytest.fixture
def http_connector():
    """Return an HTTP connector instance."""
    return HTTPConnector()

"""Pytest fixtures for Collector tests."""

import pytest
from collector.models import CollectionRequest
from collector.domains.registry import DomainRegistry


@pytest.fixture
def sample_request():
    """Return a sample collection request."""
    return CollectionRequest(
        domain="games/chance/lottery/kerala",
        source="12345",  # draw serial number
        request_id="test-123"
    )


@pytest.fixture
def registry():
    """Return a domain registry instance."""
    # DomainRegistry is a singleton with auto-registered domains
    return DomainRegistry()


@pytest.fixture
def kerala_connector():
    """Return a Kerala connector instance."""
    registry = DomainRegistry()
    return registry.get_connector("games/chance/lottery/kerala")

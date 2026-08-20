"""Pytest fixtures for Collector tests."""

import pytest
from collector.domains.registry import DomainRegistry


@pytest.fixture
def registry():
    """Return a domain registry instance."""
    return DomainRegistry()


@pytest.fixture
def kerala_connector():
    """Return a Kerala connector instance."""
    registry = DomainRegistry()
    return registry.get_connector("games/chance/lottery/kerala")

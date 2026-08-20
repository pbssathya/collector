"""Domain registry tests for Collector.

These tests verify that the production DomainRegistry works correctly.
"""

import pytest
from collector.domains.registry import DomainRegistry


def test_known_domain_resolves():
    """Verify known domain resolves to a handler."""
    registry = DomainRegistry()
    connector = registry.get_connector("games/chance/lottery/kerala")
    assert connector is not None
    assert hasattr(connector, 'retrieve')


def test_unknown_domain_handling():
    """Verify unknown domain returns None."""
    registry = DomainRegistry()
    connector = registry.get_connector("non_existent_domain")
    assert connector is None


def test_domain_registration():
    """Verify domain registration works through the registry."""
    registry = DomainRegistry()
    connector = registry.get_connector("games/chance/lottery/kerala")
    assert connector is not None
    assert hasattr(connector, 'retrieve')


def test_registry_does_not_crash_on_invalid():
    """Verify registry handles invalid input gracefully."""
    registry = DomainRegistry()
    connector = registry.get_connector("")
    assert connector is None
    connector = registry.get_connector(None)
    assert connector is None


def test_list_domains():
    """Verify registry can list all domains."""
    registry = DomainRegistry()
    domains = registry.list_domains()
    assert "games/chance/lottery/kerala" in domains


def test_list_domains_with_info():
    """Verify registry can list domains with info."""
    registry = DomainRegistry()
    domains = registry.list_domains_with_info()
    assert "games/chance/lottery/kerala" in domains
    assert "class" in domains["games/chance/lottery/kerala"]
    
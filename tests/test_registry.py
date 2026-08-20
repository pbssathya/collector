"""Domain registry tests for Collector."""

import pytest
from collector.domains.registry import DomainRegistry


def test_known_domain_resolves(registry):
    """Verify known domain resolves to a handler."""
    connector = registry.get_connector("games/chance/lottery/kerala")
    assert connector is not None
    # Should be a connector with retrieve method
    assert hasattr(connector, 'retrieve')


def test_unknown_domain_handling():
    """Verify unknown domain returns None."""
    registry = DomainRegistry()
    connector = registry.get_connector("non_existent_domain")
    assert connector is None


def test_domain_registration():
    """Verify domain registration works through the registry."""
    registry = DomainRegistry()
    # The registry auto-registers domains on initialization
    # We can check that the kerala domain is available
    connector = registry.get_connector("games/chance/lottery/kerala")
    assert connector is not None
    assert hasattr(connector, 'retrieve')


def test_registry_does_not_crash_on_invalid():
    """Verify registry handles invalid input gracefully."""
    registry = DomainRegistry()
    # Invalid domain should return None, not crash
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
    
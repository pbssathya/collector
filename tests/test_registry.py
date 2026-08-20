"""Domain registry tests for Collector."""

import pytest
from collector.registry import DomainRegistry
from collector.exceptions import DomainNotFoundError

def test_known_domain_resolves(registry):
    """Verify known domain resolves to a handler."""
    handler = registry.get("kerala")
    assert handler is not None
    # Should be a callable or connector
    assert callable(handler.collect) or hasattr(handler, 'collect')

def test_unknown_domain_handling(registry):
    """Verify unknown domain raises appropriate error."""
    with pytest.raises(DomainNotFoundError):
        registry.get("non_existent_domain_xyz")

def test_domain_registration():
    """Verify new domains can be registered."""
    registry = DomainRegistry()
    # Create a dummy handler
    class DummyHandler:
        def collect(self, request):
            return None
    registry.register("dummy", DummyHandler())
    handler = registry.get("dummy")
    assert handler is not None

def test_registry_does_not_crash_on_invalid():
    """Verify registry handles invalid input gracefully."""
    registry = DomainRegistry()
    # Invalid domain should raise error, not crash
    with pytest.raises(DomainNotFoundError):
        registry.get("")
    with pytest.raises(DomainNotFoundError):
        registry.get(None)

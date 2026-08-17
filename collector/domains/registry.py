"""
Domain Registry

Manages domain connectors using hierarchical paths.
"""

from typing import Dict, Type, Optional

from collector.contracts.connector import Connector


class DomainRegistry:
    """Registry for domain connectors."""

    _instance = None
    _connectors: Dict[str, Type[Connector]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._register_domains()
        return cls._instance

    def _register_domains(self):
        """Register all available domains."""
        try:
            from collector.domains.games.chance.lottery.kerala import Connector as KeralaConnector
            self._connectors["games/chance/lottery/kerala"] = KeralaConnector
        except ImportError as e:
            print(f"Warning: Could not load kerala domain: {e}")

    def get_connector(self, domain_path: str, **kwargs) -> Optional[Connector]:
        """
        Get a connector for a domain path.
        """
        connector_class = self._connectors.get(domain_path)
        if connector_class:
            try:
                return connector_class(**kwargs)
            except Exception as e:
                print(f"Error creating connector for {domain_path}: {e}")
                return None
        return None

    def list_domains(self) -> list:
        """List all available domain paths."""
        return list(self._connectors.keys())

    def list_domains_with_info(self) -> dict:
        """List all available domains with their info."""
        result = {}
        for path, cls in self._connectors.items():
            result[path] = {
                "class": cls.__name__,
                "module": cls.__module__,
                "doc": cls.__doc__ or "No documentation",
            }
        return result

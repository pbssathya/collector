"""Custom exceptions for Collector."""


class CollectorError(Exception):
    """Base exception for Collector errors."""
    pass


class DomainNotFoundError(CollectorError):
    """Raised when a domain is not found in the registry."""
    pass


class ConnectionError(CollectorError):
    """Raised when a connection fails."""
    pass


class TimeoutError(CollectorError):
    """Raised when a timeout occurs."""
    pass


class ParseError(CollectorError):
    """Raised when parsing fails."""
    pass


class ValidationError(CollectorError):
    """Raised when validation fails."""
    pass

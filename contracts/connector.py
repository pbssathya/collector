"""
Connector — The Interface to a Source

A Connector establishes communication with a Source
and retrieves a Document.

It does not interpret, analyse, or decide.
It simply connects and retrieves.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .document import Document


class Connector(ABC):
    """
    A Connector establishes communication with a Source
    and retrieves a Document.

    A Connector does not know:
    - What the Source means
    - What the Document contains
    - Who is consuming the Document
    - Whether the Document is "correct"

    It only knows how to connect and retrieve.
    """

    @abstractmethod
    def retrieve(self, source_url: str) -> Document:
        """
        Retrieve a Document from the given Source.

        Args:
            source_url: The URL or identifier of the Source.

        Returns:
            A Document containing the retrieved material
            and execution observations.

        Raises:
            ConnectorError: If retrieval fails.
        """
        pass

    @abstractmethod
    def supports(self, source_url: str) -> bool:
        """
        Check whether this Connector can handle the given Source.

        This allows the cell to select the appropriate Connector
        for a given Source without knowing anything about the Source.

        Args:
            source_url: The URL or identifier of the Source.

        Returns:
            True if this Connector can retrieve from the Source,
            False otherwise.
        """
        pass


class ConnectorError(Exception):
    """Raised when a Connector fails to retrieve a Document."""
    
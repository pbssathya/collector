"""
Knowledge Store

A persistent storage layer for collected knowledge.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any
from datetime import datetime


class KnowledgeRecord:
    """A record stored in the Knowledge Store."""

    def __init__(
        self,
        source: str,
        collected_at: datetime,
        raw_data: Any,
        parsed_data: Optional[Any] = None,
        metadata: Optional[dict] = None,
    ):
        self.source = source
        self.collected_at = collected_at
        self.raw_data = raw_data
        self.parsed_data = parsed_data
        self.metadata = metadata or {}
        self.id = None  # Will be assigned by the store


class KnowledgeStore(ABC):
    """Abstract interface for a Knowledge Store."""

    @abstractmethod
    def save(self, record: KnowledgeRecord) -> str:
        """
        Save a KnowledgeRecord and return its ID.
        """
        pass

    @abstractmethod
    def get(self, record_id: str) -> Optional[KnowledgeRecord]:
        """
        Retrieve a KnowledgeRecord by ID.
        """
        pass

    @abstractmethod
    def query(self, source: Optional[str] = None, limit: int = 100) -> List[KnowledgeRecord]:
        """
        Query records by source.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Return the total number of records.
        """
        pass

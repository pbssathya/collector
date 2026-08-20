"""Data models for Collector.

This module defines the core data structures used throughout the Collector,
including requests, responses, documents, and execution events.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class CollectionStatus(str, Enum):
    """Status of a collection operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class EventType(str, Enum):
    """Types of execution events that can occur during collection."""

    COLLECTION_STARTED = "collection_started"
    COLLECTION_COMPLETED = "collection_completed"
    COLLECTION_FAILED = "collection_failed"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_FAILED = "connection_failed"
    REDIRECT = "redirect"
    RETRY = "retry"
    PARSING_STARTED = "parsing_started"
    PARSING_COMPLETED = "parsing_completed"
    PARSING_FAILED = "parsing_failed"
    VALIDATION_STARTED = "validation_started"
    VALIDATION_COMPLETED = "validation_completed"
    VALIDATION_FAILED = "validation_failed"


@dataclass
class CollectionRequest:
    """Request to collect data from a source."""

    domain: str
    source: str
    request_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now())


@dataclass
class ExecutionEvent:
    """An event that occurred during collection execution."""

    event_type: str
    timestamp: datetime
    description: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """A collected document with its metadata.

    This Document preserves the COMPLETE canonical raw content in `content`.
    The `content` field is the source of truth — it is NEVER truncated.

    Display representations (like __repr__) are for human readability only
    and are clearly marked as such. They should never be used as the
    canonical source of the raw payload.
    """

    content: bytes
    """COMPLETE canonical raw content — NEVER truncated."""

    content_type: str
    """MIME type or format indicator."""

    source_url: str
    """Original source URL or identifier."""

    content_hash: Optional[str] = None
    """SHA-256 hash of the complete content (auto-computed if not provided)."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the document."""

    redirects: List[Dict[str, str]] = field(default_factory=list)
    """List of redirects encountered during retrieval."""

    status_code: Optional[int] = None
    """HTTP status code if applicable."""

    error_message: Optional[str] = None
    """Error message if collection failed."""

    def __post_init__(self):
        """Compute content hash if not provided."""
        if self.content_hash is None and self.content:
            import hashlib
            self.content_hash = hashlib.sha256(self.content).hexdigest()

    def __repr__(self) -> str:
        """Human-readable display representation.

        IMPORTANT: This is a DISPLAY representation only.
        It truncates the content preview for readability.
        The COMPLETE canonical raw data is ALWAYS preserved in `self.content`.
        """
        content_preview = self.content.hex()[:50] + "..." if len(self.content) > 25 else self.content.hex()
        return (
            f"Document(source_url={self.source_url!r}, "
            f"content_type={self.content_type!r}, "
            f"size={len(self.content)} bytes, "
            f"hash={self.content_hash[:16] if self.content_hash else 'None'}..., "
            f"content_preview(hex)={content_preview})"
        )


@dataclass
class CollectorReport:
    """Standardized report produced by Collector.

    The report contains the complete canonical Document (with full raw content)
    along with execution metadata. It does NOT contain analysis, recommendations,
    decisions, or business interpretations.
    """

    version: str = "1.0.0"
    status: CollectionStatus = CollectionStatus.PENDING
    execution_events: List[ExecutionEvent] = field(default_factory=list)
    request: Optional[CollectionRequest] = None
    document: Optional[Document] = None
    collector_version: str = "0.1.0"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
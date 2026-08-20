"""
Document — The Raw Unit of Collection

A Document is what Collector retrieves from a Source.
It does not interpret, analyse, or transform.

It simply preserves what was encountered.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Document:
    """
    The raw unit of collected information.

    A Document preserves the material retrieved from a Source
    along with the execution context that produced it.

    It does not know about:
    - Domains (lottery, weather, finance, etc.)
    - Consumers (Nokku, RealReel, etc.)
    - Interpretation (what the data means)
    - Validation (whether the data is "correct")

    It only knows what was encountered.

    The `content` field preserves the COMPLETE raw material.
    It is NEVER truncated. Display representations (like __repr__)
    are for human readability only and are clearly marked as such.
    """

    # ─── REQUIRED FIELDS (no defaults) ────────────────────────────
    id: str
    """Unique identifier for this Document."""

    source_url: str
    """The URL or identifier of the Source."""

    retrieved_at: datetime
    """When the Document was retrieved."""

    content: Any
    """The COMPLETE raw material retrieved (bytes, text, JSON, etc.)."""

    run_id: str
    """The execution Run that produced this Document."""

    connector_id: str
    """The Connector that retrieved this Document."""

    # ─── OPTIONAL FIELDS (with defaults) ──────────────────────────
    content_type: Optional[str] = None
    """MIME type or format indicator (e.g., 'text/html', 'application/json')."""

    encoding: Optional[str] = None
    """Character encoding if applicable (e.g., 'utf-8')."""

    redirects: list[str] = field(default_factory=list)
    """Any redirects encountered during retrieval."""

    status_code: Optional[int] = None
    """HTTP status code or equivalent."""

    duration_ms: Optional[float] = None
    """Retrieval duration in milliseconds."""

    error: Optional[str] = None
    """Any error encountered during retrieval."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional observations not covered by other fields."""

    def __repr__(self) -> str:
        """Human-readable display representation.

        IMPORTANT: This is a DISPLAY representation only.
        It truncates the content preview for readability.
        The COMPLETE canonical raw data is ALWAYS preserved in `self.content`.
        """
        content_preview = str(self.content)[:100] + "..." if len(str(self.content)) > 100 else str(self.content)
        return (
            f"Document(id={self.id!r}, "
            f"source_url={self.source_url!r}, "
            f"retrieved_at={self.retrieved_at!r}, "
            f"content_type={self.content_type!r}, "
            f"size={len(str(self.content))} chars, "
            f"content_preview={content_preview!r})"
        )
    
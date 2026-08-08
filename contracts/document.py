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
    """

    # ─── Identity ────────────────────────────────────────────────
    id: str
    """Unique identifier for this Document."""

    # ─── Source ──────────────────────────────────────────────────
    source_url: str
    """The URL or identifier of the Source."""

    retrieved_at: datetime
    """When the Document was retrieved."""

    # ─── Content ─────────────────────────────────────────────────
    content: Any
    """The raw material retrieved (bytes, text, JSON, etc.)."""

    content_type: Optional[str] = None
    """MIME type or format indicator (e.g., 'text/html', 'application/json')."""

    encoding: Optional[str] = None
    """Character encoding if applicable (e.g., 'utf-8')."""

    # ─── Provenance ──────────────────────────────────────────────
    run_id: str
    """The execution Run that produced this Document."""

    connector_id: str
    """The Connector that retrieved this Document."""

    # ─── Execution Observations ──────────────────────────────────
    redirects: list[str] = field(default_factory=list)
    """Any redirects encountered during retrieval."""

    status_code: Optional[int] = None
    """HTTP status code or equivalent."""

    duration_ms: Optional[float] = None
    """Retrieval duration in milliseconds."""

    error: Optional[str] = None
    """Any error encountered during retrieval."""

    # ─── Metadata ─────────────────────────────────────────────────
    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional observations not covered by other fields."""

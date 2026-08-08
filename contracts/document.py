# collector/contracts/document.py

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Document:
    """
    The raw unit of collected information.

    A Document is what Collector retrieves from a Source.
    It does not interpret, analyse, or transform.

    It simply preserves what was encountered.
    """

    # Identity
    id: str

    # Source
    source_url: str
    retrieved_at: datetime

    # Content
    content: Any  # Raw bytes, text, JSON, etc.
    content_type: Optional[str] = None
    encoding: Optional[str] = None

    # Provenance
    run_id: str
    connector_id: str

    # Observations
    redirects: list[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
  

"""Document preservation tests for Collector.

These tests verify that the COMPLETE canonical raw data is preserved
without silent truncation or information loss. They distinguish between
the canonical content (source of truth) and display representations
(for human readability only).
"""

import pytest
from collector.models import Document


def test_raw_payload_preservation():
    """Verify complete raw payload is preserved in the canonical field."""
    content = b"Hello, world! This is a test document."
    doc = Document(
        content=content,
        content_type="text/plain",
        source_url="https://example.com/test.txt"
    )
    # Verify COMPLETE raw content is preserved (canonical)
    assert doc.content == content
    # Verify complete hex representation is available
    assert doc.content.hex() == content.hex()


def test_no_silent_truncation():
    """Verify no silent truncation of canonical raw data."""
    content = b"A" * 5000  # 5KB of data
    doc = Document(
        content=content,
        content_type="text/plain",
        source_url="https://example.com/large.txt"
    )
    # Verify the COMPLETE content is preserved (canonical)
    assert len(doc.content) == 5000
    assert doc.content == content
    # Verify the hash is computed from the complete content
    import hashlib
    expected_hash = hashlib.sha256(content).hexdigest()
    assert doc.content_hash == expected_hash


def test_redirects_preserved():
    """Verify redirect chain is preserved in document."""
    doc = Document(
        content=b"final content",
        content_type="text/html",
        source_url="https://example.com/redirected",
        redirects=[
            {"from": "https://example.com/old", "to": "https://example.com/new"},
            {"from": "https://example.com/new", "to": "https://example.com/redirected"}
        ]
    )
    # Verify redirect chain exists and is complete
    assert doc.redirects is not None
    assert len(doc.redirects) == 2
    assert doc.redirects[0]["from"] == "https://example.com/old"


def test_metadata_preserved():
    """Verify metadata is preserved in document."""
    doc = Document(
        content=b"test content",
        content_type="application/json",
        source_url="https://example.com/data.json",
        metadata={
            "size": 1024,
            "encoding": "utf-8",
            "last_modified": "2024-01-01"
        }
    )
    # Verify metadata is preserved
    assert doc.metadata is not None
    assert doc.metadata["size"] == 1024
    assert doc.metadata["encoding"] == "utf-8"
    assert doc.metadata["last_modified"] == "2024-01-01"


def test_error_response_preserved():
    """Verify error responses are preserved."""
    doc = Document(
        content=b"404 Not Found",
        content_type="text/html",
        source_url="https://example.com/notfound",
        status_code=404,
        error="Resource not found"  # Changed from error_message to error
    )
    # Verify error details are preserved
    assert doc.status_code == 404
    assert doc.error == "Resource not found"


def test_content_hash_integrity():
    """Verify content hash is computed and matches complete content."""
    content = b"Test content for hashing"
    doc = Document(
        content=content,
        content_type="text/plain",
        source_url="https://example.com/test.txt"
    )
    # Verify hash exists and matches content
    assert doc.content_hash is not None
    import hashlib
    expected_hash = hashlib.sha256(content).hexdigest()
    assert doc.content_hash == expected_hash


def test_display_repr_does_not_truncate_canonical():
    """Verify __repr__ is display-only and does NOT affect canonical data."""
    content = b"X" * 1000
    doc = Document(
        content=content,
        content_type="text/plain",
        source_url="https://example.com/large.txt"
    )
    # Verify the canonical content remains complete
    assert len(doc.content) == 1000
    # Verify __repr__ exists and returns a string (display only)
    repr_str = repr(doc)
    assert isinstance(repr_str, str)
    assert "content_preview" in repr_str or "source_url" in repr_str
    # The display repr may truncate, but that's acceptable for readability
    # The canonical data is preserved in doc.content
    
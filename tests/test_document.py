"""Document preservation tests for Collector."""

import pytest
from collector.parsers.document import Document
from collector.models import CollectionRequest

def test_raw_payload_preservation():
    """Verify raw payload is preserved completely."""
    # Create a document with known content
    content = b"Hello, world! This is a test document."
    doc = Document(
        content=content,
        content_type="text/plain",
        source_url="https://example.com/test.txt"
    )
    # Verify complete raw content is preserved
    assert doc.content == content
    # Verify hex representation is complete
    assert doc.content.hex() == content.hex()

def test_no_silent_truncation():
    """Verify no silent truncation of canonical raw data."""
    content = b"A" * 5000  # 5KB of data
    doc = Document(
        content=content,
        content_type="text/plain",
        source_url="https://example.com/large.txt"
    )
    # Check that content is NOT truncated
    assert len(doc.content) == 5000
    # Verify the full content is preserved, not just a display
    # repr might truncate for display, but that's separate
    assert doc.content == content

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

def test_error_response_preserved():
    """Verify error responses are preserved."""
    doc = Document(
        content=b"404 Not Found",
        content_type="text/html",
        source_url="https://example.com/notfound",
        status_code=404,
        error_message="Resource not found"
    )
    # Verify error details are preserved
    assert doc.status_code == 404
    assert doc.error_message == "Resource not found"

def test_content_hash_integrity():
    """Verify content hash is computed and preserved."""
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

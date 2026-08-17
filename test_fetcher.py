"""
Test the HTTPFetcher.

This is a simple test to verify that the cell can
connect, retrieve, and return a Document.
"""

from core.fetcher import HTTPFetcher

# Create a fetcher
fetcher = HTTPFetcher()

# Retrieve a Document
doc = fetcher.retrieve("https://example.com")

# Print what happened
print(f"Document ID: {doc.id}")
print(f"Source URL: {doc.source_url}")
print(f"Retrieved at: {doc.retrieved_at}")
print(f"Content Type: {doc.content_type}")
print(f"Status Code: {doc.status_code}")
print(f"Duration: {doc.duration_ms:.2f}ms")
print(f"Content Length: {len(doc.content) if doc.content else 0} bytes")
print(f"Error: {doc.error if doc.error else 'None'}")

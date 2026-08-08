"""
Fetcher — The First Implementation of a Connector

A Fetcher retrieves a Document from a URL using HTTP.
It does not interpret, analyse, or decide.

It simply connects, retrieves, and returns a Document.
"""

import time
from datetime import datetime
from typing import Optional
import uuid

import requests

from collector.contracts.connector import Connector, ConnectorError
from collector.contracts.document import Document


class HTTPFetcher(Connector):
    """
    A Fetcher that retrieves a Document from a URL using HTTP.

    It does not know:
    - What the URL means
    - What the Document contains
    - Who is consuming the Document

    It only knows how to connect and retrieve.
    """

    def __init__(self, timeout: int = 30, max_redirects: int = 5):
        """
        Args:
            timeout: Request timeout in seconds.
            max_redirects: Maximum number of redirects to follow.
        """
        self.timeout = timeout
        self.max_redirects = max_redirects

    def retrieve(self, source_url: str) -> Document:
        """
        Retrieve a Document from the given URL.

        Args:
            source_url: The URL to retrieve.

        Returns:
            A Document containing the retrieved material
            and execution observations.

        Raises:
            ConnectorError: If retrieval fails.
        """
        start_time = time.time()
        run_id = str(uuid.uuid4())

        try:
            response = requests.get(
                source_url,
                timeout=self.timeout,
                max_redirects=self.max_redirects,
                allow_redirects=True,
            )

            duration_ms = (time.time() - start_time) * 1000

            # Determine content type and encoding
            content_type = response.headers.get("content-type")
            encoding = response.encoding or "utf-8"

            # Capture any redirects
            redirects = []
            if response.history:
                redirects = [r.url for r in response.history]

            # Create the Document
            return Document(
                id=str(uuid.uuid4()),
                source_url=source_url,
                retrieved_at=datetime.now(),
                content=response.content,
                content_type=content_type,
                encoding=encoding,
                run_id=run_id,
                connector_id="http_fetcher",
                redirects=redirects,
                status_code=response.status_code,
                duration_ms=duration_ms,
                error=None,
            )

        except requests.exceptions.RequestException as e:
            duration_ms = (time.time() - start_time) * 1000

            # Even on failure, return a Document with the error recorded
            return Document(
                id=str(uuid.uuid4()),
                source_url=source_url,
                retrieved_at=datetime.now(),
                content=None,
                content_type=None,
                encoding=None,
                run_id=run_id,
                connector_id="http_fetcher",
                redirects=[],
                status_code=None,
                duration_ms=duration_ms,
                error=str(e),
            )

    def supports(self, source_url: str) -> bool:
        """
        Check whether this Fetcher can handle the given URL.

        For HTTPFetcher, any URL with http:// or https:// is supported.

        Args:
            source_url: The URL to check.

        Returns:
            True if the URL uses http or https, False otherwise.
        """
        return source_url.startswith(("http://", "https://"))
    
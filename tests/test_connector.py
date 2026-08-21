"""Connector contract tests for Collector.

These tests verify connector behaviour without making the core contract depend
on the availability or behaviour of an unrelated external test service.
"""

from unittest.mock import patch

import pytest
import requests

from collector.contracts.connector import ConnectorError
from collector.core.fetcher import HTTPFetcher
from collector.domains.registry import DomainRegistry


@pytest.fixture
def kerala_connector():
    """Return a Kerala connector instance."""
    registry = DomainRegistry()
    return registry.get_connector("games/chance/lottery/kerala")


def test_supported_source_retrieval(kerala_connector):
    """Verify a supported source can be retrieved."""
    try:
        doc = kerala_connector.retrieve("12345")
        assert doc is not None
        assert doc.content is not None
    except ConnectorError:
        pytest.skip("External service unavailable")


def test_connection_failure_reporting():
    """Verify connection failures are reported as execution events."""
    fetcher = HTTPFetcher()
    doc = fetcher.retrieve("https://invalid-domain-that-does-not-exist.example.com")
    assert doc.error is not None or doc.status_code is not None


def test_http_redirect_following():
    """Verify HTTP redirects are followed and recorded deterministically."""
    original_url = "https://example.test/start"
    final_url = "https://example.test/final"

    redirect_response = requests.Response()
    redirect_response.status_code = 302
    redirect_response.url = original_url
    redirect_response.headers["Location"] = final_url

    final_response = requests.Response()
    final_response.status_code = 200
    final_response.url = final_url
    final_response._content = b"collected material"
    final_response.headers["content-type"] = "text/plain"
    final_response.encoding = "utf-8"
    final_response.history = [redirect_response]

    with patch("requests.Session.get", return_value=final_response):
        doc = HTTPFetcher().retrieve(original_url)

    assert doc.error is None
    assert doc.status_code == 200
    assert doc.content == b"collected material"
    assert doc.redirects == [original_url]
    assert all(isinstance(redirect, str) for redirect in doc.redirects)

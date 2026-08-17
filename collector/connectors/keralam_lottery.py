"""
Keralam Lottery Connector

Retrieves lottery results from the official Keralam Lottery website.
"""

from typing import Optional

from collector.core.fetcher import HTTPFetcher
from collector.contracts.document import Document


class KeralamLotteryConnector:
    """
    A Connector for Keralam Lottery results.

    Uses the drawserial pattern to fetch results.
    """

    RESULT_BASE = "http://result.keralalotteries.com/viewlotisresult.php"

    def __init__(self):
        self.fetcher = HTTPFetcher()

    def fetch_draw(self, serial: int) -> Document:
        """
        Fetch a specific draw by serial number.
        """
        url = f"{self.RESULT_BASE}?drawserial={serial}"
        return self.fetcher.retrieve(url)

"""
Keralam Lottery Connector

Retrieves lottery results from the official Keralam Lottery website.
"""

import re
from typing import Optional

from collector.core.fetcher import HTTPFetcher
from collector.contracts.document import Document


class KeralamLotteryConnector:
    """
    A Connector for Keralam Lottery results.

    Uses the drawserial pattern to fetch results.
    """

    INDEX_URL = "https://statelottery.kerala.gov.in/English/index.php/lottery-result-view"
    RESULT_BASE = "http://result.keralalotteries.com/viewlotisresult.php"

    def __init__(self):
        self.fetcher = HTTPFetcher()

    def get_latest_serial(self) -> Optional[int]:
        """
        Fetch the index page and extract the latest draw serial.

        Returns:
            The latest draw serial number, or None if not found.
        """
        doc = self.fetcher.retrieve(self.INDEX_URL)
        if doc.error or not doc.content:
            return None

        content = doc.content.decode("utf-8", errors="ignore")

        # Look for the first result link in the table
        pattern = r'viewlotisresult\.php\?drawserial=(\d+)'
        matches = re.findall(pattern, content)

        if matches:
            return int(matches[0])  # First match is the latest

        return None

    def fetch_latest(self) -> Optional[Document]:
        """
        Fetch the latest draw result.

        Returns:
            A Document containing the result page, or None if not found.
        """
        serial = self.get_latest_serial()
        if serial is None:
            return None

        url = f"{self.RESULT_BASE}?drawserial={serial}"
        return self.fetcher.retrieve(url)

    def fetch_draw(self, serial: int) -> Document:
        """
        Fetch a specific draw by serial number.

        Args:
            serial: The draw serial number.

        Returns:
            A Document containing the result page.
        """
        url = f"{self.RESULT_BASE}?drawserial={serial}"
        return self.fetcher.retrieve(url)

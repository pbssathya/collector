"""
Kerala Lottery Connector
"""

from typing import Optional, Dict, Any

from collector.core.fetcher import HTTPFetcher
from collector.contracts.connector import Connector as BaseConnector
from collector.contracts.document import Document
from .history import OfficialHistoryResolver
from .parser import Parser


class Connector(BaseConnector):
    """
    A Connector for Kerala Lottery results.

    Uses the drawserial pattern to fetch results. When historical drawserials contain
    a large discontinuity, ``previous_source`` can ask the official older-draw
    resolver for the nearest published serial below the current one.
    """

    RESULT_BASE = "http://result.keralalotteries.com/viewlotisresult.php"

    def __init__(self, **kwargs):
        self.fetcher = HTTPFetcher()
        self.parser = Parser()
        self.history_resolver = OfficialHistoryResolver()

    def retrieve(self, source: str) -> Document:
        """
        Retrieve a draw by serial number.

        Args:
            source: The draw serial number (as string or int).

        Returns:
            A Document containing the result page.
        """
        url = f"{self.RESULT_BASE}?drawserial={source}"
        return self.fetcher.retrieve(url)

    def parse(self, content: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse the PDF content.

        Args:
            content: The PDF content as bytes.

        Returns:
            A dictionary with the parsed data, or None if parsing fails.
        """
        result = self.parser.parse(content)
        if not result:
            return None

        return {
            "lottery_name": result.lottery_name,
            "draw_date": result.draw_date,
            "first_prize": result.first_prize,
            "first_prize_location": result.first_prize_location,
            "second_prize": result.second_prize,
            "second_prize_location": result.second_prize_location,
            "third_prize": result.third_prize,
            "third_prize_location": result.third_prize_location,
            "consolation_prizes": result.consolation_prizes,
            "prize_tiers": result.prize_tiers,
            "fourth_prize_numbers": result.fourth_prize_numbers,
            "fifth_prize_numbers": result.fifth_prize_numbers,
            "sixth_prize_numbers": result.sixth_prize_numbers,
            "seventh_prize_numbers": result.seventh_prize_numbers,
            "eighth_prize_numbers": result.eighth_prize_numbers,
            "ninth_prize_numbers": result.ninth_prize_numbers,
        }

    def previous_source(self, source: str) -> Optional[str]:
        """Return the nearest earlier published drawserial, if discoverable."""
        try:
            before_source = int(source)
        except ValueError:
            return None

        previous = self.history_resolver.previous_source_id(before_source)
        return str(previous) if previous is not None else None

    def supports(self, source: str) -> bool:
        """Check if this connector supports the given source."""
        try:
            int(source)
            return True
        except ValueError:
            return False

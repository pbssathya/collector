"""
Kerala Lottery Parser
"""

import re
from io import BytesIO
from typing import Optional

from pypdf import PdfReader

from .result import Result


class Parser:
    """Parses a Kerala Lottery result PDF."""

    def parse(self, content: bytes) -> Optional[Result]:
        """
        Parse the PDF content.
        """
        try:
            pdf_file = BytesIO(content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None

        # Extract lottery name
        name_match = re.search(
            r'([A-Z\s]+LOTTERY\s+NO\.[A-Z]+-\d+[a-z]+\s+DRAW)',
            text,
            re.IGNORECASE
        )
        lottery_name = name_match.group(1) if name_match else "Unknown"

        # Extract draw date
        date_match = re.search(
            r'held on:-\s*(\d{2}/\d{2}/\d{4})',
            text,
            re.IGNORECASE
        )
        draw_date = date_match.group(1) if date_match else "Unknown"

        # Extract 1st Prize
        first_match = re.search(
            r'1st Prize\s*Rs\s*:?\s*[\d,]+\s*/\s*-?\s*1\)\s*([A-Z]+\s+\d+)\s*\(([^)]+)\)',
            text,
            re.IGNORECASE
        )
        if first_match:
            first_prize = first_match.group(1)
            first_location = first_match.group(2)
        else:
            first_prize = "Unknown"
            first_location = "Unknown"

        return Result(
            lottery_name=lottery_name,
            draw_date=draw_date,
            first_prize=first_prize,
            first_prize_location=first_location,
        )

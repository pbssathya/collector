"""
Keralam Lottery Result Parser

Extracts structured data from a Keralam Lottery result PDF.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List
from io import BytesIO

from pypdf import PdfReader


@dataclass
class KeralamResult:
    """Structured Keralam Lottery result."""

    lottery_name: str
    draw_date: str
    first_prize: str
    first_prize_location: str
    consolation_prizes: List[str] = field(default_factory=list)
    second_prize: str = ""
    second_prize_location: str = ""
    third_prize: str = ""
    third_prize_location: str = ""
    fourth_prize_numbers: List[str] = field(default_factory=list)
    fifth_prize_numbers: List[str] = field(default_factory=list)
    sixth_prize_numbers: List[str] = field(default_factory=list)
    seventh_prize_numbers: List[str] = field(default_factory=list)
    eighth_prize_numbers: List[str] = field(default_factory=list)
    ninth_prize_numbers: List[str] = field(default_factory=list)


class KeralamResultParser:
    """Parses a Keralam Lottery result PDF."""

    def parse(self, content: bytes) -> Optional[KeralamResult]:
        """
        Parse the PDF content.

        Args:
            content: The PDF content as bytes.

        Returns:
            A KeralamResult object, or None if parsing fails.
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

        # Extract Consolation Prizes
        consolation = []
        cons_match = re.search(
            r'Cons Prize-Rs\s*:?\s*[\d,]+\s*/\s*-?\s*(.*?)(?=2nd Prize)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if cons_match:
            cons_text = cons_match.group(1)
            consolation = re.findall(r'([A-Z]+\s+\d+)', cons_text)

        # Extract 2nd Prize
        second_match = re.search(
            r'2nd Prize\s*Rs\s*:?\s*[\d,]+\s*/\s*-?\s*1\)\s*([A-Z]+\s+\d+)\s*\(([^)]+)\)',
            text,
            re.IGNORECASE
        )
        if second_match:
            second_prize = second_match.group(1)
            second_location = second_match.group(2)
        else:
            second_prize = "Unknown"
            second_location = "Unknown"

        # Extract 3rd Prize
        third_match = re.search(
            r'3rd Prize\s*Rs\s*:?\s*[\d,]+\s*/\s*-?\s*1\)\s*([A-Z]+\s+\d+)\s*\(([^)]+)\)',
            text,
            re.IGNORECASE
        )
        if third_match:
            third_prize = third_match.group(1)
            third_location = third_match.group(2)
        else:
            third_prize = "Unknown"
            third_location = "Unknown"

        # Extract 4th Prize numbers
        fourth = self._extract_prize_list(text, r'4th Prize-Rs\s*:?\s*[\d,]+', r'5th Prize')
        
        # Extract 5th Prize numbers
        fifth = self._extract_prize_list(text, r'5th Prize-Rs\s*:?\s*[\d,]+', r'6th Prize')
        
        # Extract 6th Prize numbers
        sixth = self._extract_prize_list(text, r'6th Prize-Rs\s*:?\s*[\d,]+', r'7th Prize')
        
        # Extract 7th Prize numbers
        seventh = self._extract_prize_list(text, r'7th Prize-Rs\s*:?\s*[\d,]+', r'8th Prize')
        
        # Extract 8th Prize numbers
        eighth = self._extract_prize_list(text, r'8th Prize-Rs\s*:?\s*[\d,]+', r'9th Prize')
        
        # Extract 9th Prize numbers
        ninth = self._extract_prize_list(text, r'9th Prize-Rs\s*:?\s*[\d,]+', r'Next')

        return KeralamResult(
            lottery_name=lottery_name,
            draw_date=draw_date,
            first_prize=first_prize,
            first_prize_location=first_location,
            consolation_prizes=consolation,
            second_prize=second_prize,
            second_prize_location=second_location,
            third_prize=third_prize,
            third_prize_location=third_location,
            fourth_prize_numbers=fourth,
            fifth_prize_numbers=fifth,
            sixth_prize_numbers=sixth,
            seventh_prize_numbers=seventh,
            eighth_prize_numbers=eighth,
            ninth_prize_numbers=ninth,
        )

    def _extract_prize_list(self, text: str, start_pattern: str, end_pattern: str) -> List[str]:
        """
        Extract a list of prize numbers between two patterns.
        """
        pattern = f'{start_pattern}.*?(?={end_pattern})'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if not match:
            return []
        
        # Extract all 4-digit numbers
        numbers = re.findall(r'\b(\d{4})\b', match.group(0))
        return numbers

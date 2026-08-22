"""
Kerala Lottery Parser
"""

import re
from io import BytesIO
from typing import Dict, List, Optional

from pypdf import PdfReader

from .result import Result


class Parser:
    """Parses a Kerala Lottery result PDF."""

    LOTTERY_NAME_RE = re.compile(
        r"(?im)^[ \t]*(?:in[ \t]+)?"
        r"([A-Z][A-Z0-9 \t-]*?LOTTERY(?:[ \t]+LOTTERY)?[ \t]+"
        r"NO\.[A-Z]+-\d+(?:st|nd|rd|th)[ \t]+DRAW)"
        r"(?=[ \t]+held[ \t]+on:-|[ \t]*$)"
    )

    PRIZE_HEADING_RE = re.compile(
        r"(?P<label>(?:Cons(?:olation)?|\d+(?:st|nd|rd|th)|[A-Za-z][A-Za-z ]*?)\s+Prize)\s*-?\s*Rs\s*:?\s*(?P<amount>[\d,]+)\s*/\s*-?",
        re.IGNORECASE,
    )

    def parse(self, content: bytes) -> Optional[Result]:
        """Parse the PDF content."""
        try:
            pdf_file = BytesIO(content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None

        lottery_name = self._extract_lottery_name(text)

        date_match = re.search(
            r"held on:-\s*(\d{2}/\d{2}/\d{4})",
            text,
            re.IGNORECASE,
        )
        draw_date = date_match.group(1) if date_match else "Unknown"

        first_match = re.search(
            r"1st Prize\s*Rs\s*:?\s*[\d,]+\s*/\s*-?\s*1\)\s*([A-Z]+\s+\d+)\s*\(([^)]+)\)",
            text,
            re.IGNORECASE,
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
            prize_tiers=self._extract_prize_tiers(text),
        )

    def _extract_lottery_name(self, text: str) -> str:
        """Extract the draw heading without absorbing neighbouring PDF text."""
        match = self.LOTTERY_NAME_RE.search(text)
        if not match:
            return "Unknown"
        return re.sub(r"\s+", " ", match.group(1)).strip()

    def _extract_prize_tiers(self, text: str) -> List[Dict[str, object]]:
        """Preserve every prize section encountered, without assuming a max tier."""
        matches = list(self.PRIZE_HEADING_RE.finditer(text))
        tiers: List[Dict[str, object]] = []

        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = text[start:end]

            entries = []
            for line in section.splitlines():
                cleaned = line.strip()
                if not cleaned:
                    continue
                if cleaned.startswith("FOR THE TICKETS ENDING"):
                    continue
                if cleaned.startswith("Page "):
                    continue
                if cleaned.startswith("Modernization & IT Software Division"):
                    continue
                if re.match(r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}$", cleaned):
                    continue
                entries.append(cleaned)

            tiers.append(
                {
                    "label": re.sub(r"\s+", " ", match.group("label")).strip(),
                    "amount": match.group("amount").replace(",", ""),
                    "entries": entries,
                }
            )

        return tiers

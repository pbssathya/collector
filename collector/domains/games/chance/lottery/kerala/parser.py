"""Kerala Lottery Parser."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

from collector.extractors.pdf import extract_pdf_structure, iter_pdf_lines

from .result import Result


class Parser:
    """Map structured Kerala Lottery PDF content into result semantics."""

    PRIZE_HEADING_RE = re.compile(
        r"^(?P<label>(?:Cons(?:olation)?|\d+(?:st|nd|rd|th)|[A-Za-z][A-Za-z ]*?)\s+Prize)"
        r"\s*-?\s*Rs\.?\s*:?\s*(?P<amount>[\d,]+)\s*/\s*-?",
        re.IGNORECASE,
    )
    HELD_DATE_RE = re.compile(
        r"\bheld\s+on\s*:?-?\s*(\d{2}/\d{2}/\d{4})\b",
        re.IGNORECASE,
    )
    FIRST_PRIZE_ENTRY_RE = re.compile(
        r"^\s*\d+\)\s*([A-Z]+\s+\d+)\s*\(([^)]+)\)",
        re.IGNORECASE,
    )

    def parse(self, content: bytes) -> Optional[Result]:
        """Parse Kerala result semantics from structured PDF lines."""
        try:
            structure = extract_pdf_structure(content)
            lines = [
                self._normalize(str(item.get("text", "")))
                for item in iter_pdf_lines(structure)
                if str(item.get("text", "")).strip()
            ]
        except Exception as exc:
            print(f"Error reading PDF: {exc}")
            return None

        lottery_name = self._extract_lottery_name(lines)
        draw_date = self._extract_draw_date(lines)
        prize_tiers = self._extract_prize_tiers(lines)
        first_prize, first_location = self._extract_first_prize(prize_tiers)

        return Result(
            lottery_name=lottery_name,
            draw_date=draw_date,
            first_prize=first_prize,
            first_prize_location=first_location,
            prize_tiers=prize_tiers,
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _coerce_lines(self, value: str | Iterable[str]) -> list[str]:
        if isinstance(value, str):
            return [self._normalize(line) for line in value.splitlines() if line.strip()]
        return [self._normalize(str(line)) for line in value if str(line).strip()]

    def _extract_lottery_name(self, value: str | Iterable[str]) -> str:
        """Find the draw-heading line and keep only the heading through DRAW."""
        for line in self._coerce_lines(value):
            upper = line.upper()
            if "LOTTERY NO." not in upper or "DRAW" not in upper:
                continue

            draw_match = re.search(r"\bDRAW\b", line, re.IGNORECASE)
            if not draw_match:
                continue

            heading = line[: draw_match.end()].strip()
            if heading.lower().startswith("in "):
                heading = heading[3:].lstrip()
            return self._normalize(heading)

        return "Unknown"

    def _extract_draw_date(self, value: str | Iterable[str]) -> str:
        """Read the actual held date, independent of surrounding schedule text."""
        for line in self._coerce_lines(value):
            lower = line.lower()
            if lower.startswith("next ") or " will be held on " in lower:
                continue
            match = self.HELD_DATE_RE.search(line)
            if match:
                return match.group(1)
        return "Unknown"

    def _extract_first_prize(
        self, prize_tiers: List[Dict[str, object]]
    ) -> tuple[str, str]:
        for tier in prize_tiers:
            if str(tier.get("label", "")).lower() != "1st prize":
                continue
            for entry in tier.get("entries", []):
                match = self.FIRST_PRIZE_ENTRY_RE.match(str(entry))
                if match:
                    return match.group(1), match.group(2)
        return "Unknown", "Unknown"

    def _extract_prize_tiers(
        self, value: str | Iterable[str]
    ) -> List[Dict[str, object]]:
        """Preserve prize sections from ordered PDF lines without a tier cap."""
        lines = self._coerce_lines(value)
        tiers: List[Dict[str, object]] = []
        current: Optional[Dict[str, object]] = None

        for line in lines:
            match = self.PRIZE_HEADING_RE.match(line)
            if match:
                if current is not None:
                    tiers.append(current)

                current = {
                    "label": self._normalize(match.group("label")),
                    "amount": match.group("amount").replace(",", ""),
                    "entries": [],
                }

                trailing = line[match.end() :].strip()
                if trailing:
                    current["entries"].append(trailing)
                continue

            if current is None:
                continue

            if self._is_non_prize_line(line):
                continue

            current["entries"].append(line)

        if current is not None:
            tiers.append(current)

        return tiers

    @staticmethod
    def _is_non_prize_line(line: str) -> bool:
        lower = line.lower()
        if lower.startswith("for the tickets ending"):
            return True
        if lower.startswith("page "):
            return True
        if lower.startswith("modernization & it software division"):
            return True
        if lower.startswith("www.statelottery.kerala.gov.in"):
            return True
        if lower.startswith("the prize winners are advised"):
            return True
        if lower.startswith("next ") and " draw will be held on " in lower:
            return True
        if re.match(r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}$", line):
            return True
        return False

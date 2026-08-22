"""
Kerala Lottery Result
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Result:
    """Structured Kerala Lottery result."""

    lottery_name: str
    draw_date: str
    first_prize: str
    first_prize_location: str
    consolation_prizes: List[str] = field(default_factory=list)
    second_prize: str = ""
    second_prize_location: str = ""
    third_prize: str = ""
    third_prize_location: str = ""

    # Dynamic source-facing representation of every prize tier encountered.
    # Each item preserves the tier label, announced amount, and section entries.
    # This allows new legitimate tiers (10th, 11th, special, etc.) to flow
    # through without changing the Result schema again.
    prize_tiers: List[Dict[str, object]] = field(default_factory=list)

    # Legacy fields retained for compatibility with existing consumers.
    fourth_prize_numbers: List[str] = field(default_factory=list)
    fifth_prize_numbers: List[str] = field(default_factory=list)
    sixth_prize_numbers: List[str] = field(default_factory=list)
    seventh_prize_numbers: List[str] = field(default_factory=list)
    eighth_prize_numbers: List[str] = field(default_factory=list)
    ninth_prize_numbers: List[str] = field(default_factory=list)

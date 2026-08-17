"""
Kerala Lottery Result
"""

from dataclasses import dataclass, field
from typing import List


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
    fourth_prize_numbers: List[str] = field(default_factory=list)
    fifth_prize_numbers: List[str] = field(default_factory=list)
    sixth_prize_numbers: List[str] = field(default_factory=list)
    seventh_prize_numbers: List[str] = field(default_factory=list)
    eighth_prize_numbers: List[str] = field(default_factory=list)
    ninth_prize_numbers: List[str] = field(default_factory=list)

from collector.domains.games.chance.lottery.kerala.parser import Parser


def test_extracts_regular_lottery_heading_without_neighbouring_text():
    text = """
in
KARUNYA LOTTERY NO.KR-636th DRAW
held on:- 13/01/2024,2:00 PM
"""

    assert Parser()._extract_lottery_name(text) == "KARUNYA LOTTERY NO.KR-636th DRAW"


def test_extracts_2023_bumper_heading_with_year():
    text = """
VISHU BUMPER 2023   LOTTERY NO.BR-91st DRAW
held on:- 24/05/2023,2:00 PM
"""

    assert Parser()._extract_lottery_name(text) == "VISHU BUMPER 2023 LOTTERY NO.BR-91st DRAW"


def test_extracts_2023_bumper_heading_with_hyphenated_year():
    text = """
THIRUVONAM BUMPER -2023   LOTTERY NO.BR-93rd DRAW
held on:- 20/09/2023,2:00 PM
"""

    assert Parser()._extract_lottery_name(text) == "THIRUVONAM BUMPER -2023 LOTTERY NO.BR-93rd DRAW"

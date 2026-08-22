from collector.domains.games.chance.lottery.kerala.parser import Parser


def test_extracts_regular_lottery_heading_without_neighbouring_text():
    text = """
in
KARUNYA LOTTERY NO.KR-636th DRAW
held on:- 13/01/2024,2:00 PM
"""

    assert Parser()._extract_lottery_name(text) == "KARUNYA LOTTERY NO.KR-636th DRAW"


def test_extracts_regular_heading_when_in_is_on_same_line():
    text = """
in KARUNYA LOTTERY NO.KR-636th DRAW held on:- 13/01/2024,2:00 PM
"""

    assert Parser()._extract_lottery_name(text) == "KARUNYA LOTTERY NO.KR-636th DRAW"


def test_extracts_heading_when_draw_is_followed_by_scheduled_on_text():
    text = """
KARUNYA PLUS LOTTERY NO.KN-610th DRAW scheduled on 12/02/2026 at 3:00 PM,
and held on:- 13/02/2026,1:30 PM
"""

    assert Parser()._extract_lottery_name(text) == "KARUNYA PLUS LOTTERY NO.KN-610th DRAW"


def test_extracts_2023_bumper_heading_with_year_from_real_pdf_shape():
    text = """
SUMMER BUMPER 2023 LOTTERY NO.BR-90th DRAW held on:- 19/03/2023,2:00 PM
"""

    assert Parser()._extract_lottery_name(text) == "SUMMER BUMPER 2023 LOTTERY NO.BR-90th DRAW"


def test_extracts_2023_bumper_heading_with_year():
    text = """
VISHU BUMPER 2023   LOTTERY NO.BR-91st DRAW
held on:- 24/05/2023,2:00 PM
"""

    assert Parser()._extract_lottery_name(text) == "VISHU BUMPER 2023 LOTTERY NO.BR-91st DRAW"


def test_extracts_2023_bumper_heading_with_hyphenated_year():
    text = """
THIRUVONAM BUMPER -2023   LOTTERY NO.BR-93rd DRAW held on:- 20/09/2023,2:00 PM
"""

    assert Parser()._extract_lottery_name(text) == "THIRUVONAM BUMPER -2023 LOTTERY NO.BR-93rd DRAW"

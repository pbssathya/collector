from collector.domains.games.chance.lottery.kerala.parser import Parser


def test_legacy_heading_held_on_without_colon_is_a_draw_date():
    text = """
WIN-WIN LOTTERY NO. W-574th DRAW held on 20/07/2020 AT GORKY BHAVAN
Next WIN-WIN Lottery Draw will be held on 03/08/2020 at GORKY
"""

    assert Parser()._extract_draw_date(text) == "20/07/2020"


def test_legacy_scheduled_and_held_line_uses_held_date():
    text = """
POURNAMI LOTTERY NO. RN-436th DRAW scheduled on 22/06/2020 at 03:00 PM and held on 23/06/2020,
"""

    assert Parser()._extract_draw_date(text) == "23/06/2020"


def test_next_draw_schedule_is_not_mistaken_for_actual_draw_date():
    text = """
Next NIRMAL WEEKLY LOTTERY Lottery Draw will be held on 07/08/2020 at GORKY BHAVAN
"""

    assert Parser()._extract_draw_date(text) == "Unknown"


def test_legacy_rs_dot_prize_headings_and_inline_consolation_are_preserved():
    text = """
1st Prize- Rs :7,500,000/-
WM 187835 (KOLLAM)
Consolation Prize- Rs. 8,000/- WA 187835
WB 187835
2nd Prize- Rs :500,000/-
WA 197245 (KOLLAM)
3rd Prize- Rs :100,000/-
WA 483732 (KOLLAM)
4th Prize- Rs. 5,000/-
1111
5th Prize- Rs. 2,000/-
2222
6th Prize- Rs. 1,000/-
3333
7th Prize- Rs. 500/-
4444
8th Prize- Rs. 100/-
5555
"""

    tiers = Parser()._extract_prize_tiers(text)

    assert [tier["label"] for tier in tiers] == [
        "1st Prize",
        "Consolation Prize",
        "2nd Prize",
        "3rd Prize",
        "4th Prize",
        "5th Prize",
        "6th Prize",
        "7th Prize",
        "8th Prize",
    ]
    assert tiers[1]["amount"] == "8000"
    assert tiers[1]["entries"][:2] == ["WA 187835", "WB 187835"]
    assert tiers[-1]["amount"] == "100"

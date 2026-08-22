from collector.domains.games.chance.lottery.kerala.parser import Parser


def test_prize_tiers_are_not_capped_at_ninth():
    text = """
1st Prize Rs :10000000/-
1) DW 809210 (ERNAKULAM)
9th Prize-Rs :100/-
0072
0254
10th Prize-Rs :50/-
1111
2222
Special Prize-Rs :25/-
SP 123456
"""

    tiers = Parser()._extract_prize_tiers(text)

    assert [tier["label"] for tier in tiers] == [
        "1st Prize",
        "9th Prize",
        "10th Prize",
        "Special Prize",
    ]
    assert tiers[2]["amount"] == "50"
    assert tiers[2]["entries"] == ["1111", "2222"]
    assert tiers[3]["entries"] == ["SP 123456"]


def test_current_ninth_prize_shape_is_preserved():
    text = """
8th Prize-Rs :200/-
0089
0356
9th Prize-Rs :100/-
0072
0254
0277
Page 3
Modernization & IT Software Division : Department of State Lotteries
18/02/2026 16:36:50
"""

    tiers = Parser()._extract_prize_tiers(text)

    assert tiers[-1] == {
        "label": "9th Prize",
        "amount": "100",
        "entries": ["0072", "0254", "0277"],
    }

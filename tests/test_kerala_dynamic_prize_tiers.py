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


def test_government_footer_terminates_final_prize_tier_without_losing_prizes():
    text = """
1st Prize Rs :10000000/-
1) DW 809210 (ERNAKULAM)
2nd Prize Rs :3000000/-
1) DO 503175 (PALAKKAD)
8th Prize-Rs :200/-
0089
0356
9th Prize-Rs :100/-
0072
0254
0277
The prize winners are advised to verify the winning numbers with the results published in the Kerala
Government Gazette and surrender the winning tickets within 90 days.
Sd/-
DEPUTY DIRECTOR NAME
Directorate Of State Lotteries ,Thiruvananthapuram
GORKY BHAVAN, NEAR BAKERY JUNCTION, THIRUVANANTHAPURAM
Digitally signed by STATE LOTTERIES
Verify authenticity at official portal
Next KARUNYA draw will be held on 05/09/2026 at GORKY BHAVAN
"""

    tiers = Parser()._extract_prize_tiers(text)

    assert [tier["label"] for tier in tiers] == [
        "1st Prize",
        "2nd Prize",
        "8th Prize",
        "9th Prize",
    ]
    assert tiers[0]["entries"] == ["1) DW 809210 (ERNAKULAM)"]
    assert tiers[1]["entries"] == ["1) DO 503175 (PALAKKAD)"]
    assert tiers[-1]["entries"] == ["0072", "0254", "0277"]

    all_entries = "\n".join(
        str(entry) for tier in tiers for entry in tier["entries"]
    ).lower()
    for forbidden in (
        "government gazette",
        "sd/-",
        "deputy director",
        "gorky bhavan",
        "directorate of state lotteries",
        "digitally signed",
        "authenticity",
        "next karunya draw",
    ):
        assert forbidden not in all_entries


def test_next_draw_heading_is_also_a_structural_prize_boundary():
    text = """
9th Prize-Rs :100/-
1001
1002
Next STHREE-SAKTHI draw will be held on 08/09/2026 at 3:00 PM
AT GORKY BHAVAN, NEAR BAKERY JUNCTION, THIRUVANANTHAPURAM
"""

    tiers = Parser()._extract_prize_tiers(text)

    assert tiers == [
        {"label": "9th Prize", "amount": "100", "entries": ["1001", "1002"]}
    ]

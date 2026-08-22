from collector.domains.games.chance.lottery.kerala.history import (
    nearest_lower_source,
    parse_drawserials,
    parse_lottery_options,
)


def test_parses_official_lottery_options():
    html = """
    <select name="lotterydet" id="lotterydet">
      <option value="52">AKSHAYA</option>
      <option value="50">KARUNYA</option>
    </select>
    """

    assert parse_lottery_options(html) == [("52", "AKSHAYA"), ("50", "KARUNYA")]


def test_parses_drawserial_links_from_official_shape():
    html = """
    <a href="viewlotisresult.php?drawserial=74885">View</a>
    <a href="https://result.keralalotteries.com/viewlotisresult.php?drawserial=73081">View</a>
    <a href="reports/resultentryeport1.php?drawno1=123">Old report</a>
    """

    assert parse_drawserials(html) == {74885, 73081}


def test_selects_nearest_published_source_below_current():
    assert nearest_lower_source(73635, {74885, 73635, 73081, 73080}) == 73081
    assert nearest_lower_source(73075, {74885, 73081}) is None

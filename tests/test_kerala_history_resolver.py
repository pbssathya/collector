from unittest.mock import Mock

from collector.domains.games.chance.lottery.kerala.history import (
    CURRENT_RESULTS_URL,
    DETAILS_URL,
    OfficialHistoryResolver,
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


def response(text):
    result = Mock()
    result.text = text
    result.raise_for_status = Mock()
    return result


def test_current_result_listing_prevents_false_unpublished_frontier():
    resolver = OfficialHistoryResolver()
    resolver.session = Mock()
    current_html = '<a href="viewlotisresult.php?drawserial=75370">View</a>'

    def get(url, **_kwargs):
        if url == CURRENT_RESULTS_URL:
            return response(current_html)
        raise AssertionError(f"historical lookup should not be needed for {url}")

    resolver.session.get.side_effect = get

    assert resolver.is_published_source(75370) is True
    resolver.session.post.assert_not_called()


def test_unpublished_source_remains_rejected_after_current_and_history_checks():
    resolver = OfficialHistoryResolver()
    resolver.session = Mock()

    current_html = '<a href="viewlotisresult.php?drawserial=75370">View</a>'
    history_landing = """
    <select name="lotterydet">
      <option value="50">KARUNYA</option>
    </select>
    """
    history_results = '<a href="viewlotisresult.php?drawserial=75363">View</a>'

    def get(url, **_kwargs):
        if url == CURRENT_RESULTS_URL:
            return response(current_html)
        if url == DETAILS_URL:
            return response(history_landing)
        raise AssertionError(f"unexpected URL: {url}")

    resolver.session.get.side_effect = get
    resolver.session.post.return_value = response(history_results)

    assert resolver.is_published_source(75371) is False
    resolver.session.post.assert_called_once_with(
        DETAILS_URL,
        data={"lotterydet": "50"},
        timeout=resolver.timeout,
    )

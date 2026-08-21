"""Collector release version contract."""

from importlib.metadata import version

from collector.collect import collect


def test_collector_version_is_1_0_0():
    """Package metadata and report provenance must agree for v1.0.0."""
    report = collect("unknown/domain", "release-check", store=False)

    assert version("collector") == "1.0.0"
    assert report is not None
    assert report["provenance"]["collector_version"] == "1.0.0"

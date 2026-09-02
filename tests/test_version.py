from importlib.metadata import version

import collector


def test_package_version_matches_project_metadata():
    assert collector.__version__ == version("collector")

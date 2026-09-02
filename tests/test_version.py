from pathlib import Path
import tomllib

import collector


def test_package_version_matches_project_metadata():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    assert collector.__version__ == pyproject["project"]["version"]

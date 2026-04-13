"""Regression tests for packaging metadata in pyproject.toml."""

from pathlib import Path
import tomllib


def _load_optional_dependencies():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        project = tomllib.load(handle)["project"]
    return project["optional-dependencies"]


def test_matrix_extra_removed_from_optional_dependencies():
    """Matrix support was removed in the simplification phase.

    Ensure stale ``[matrix]`` optional dependencies are not reintroduced.
    """
    optional_dependencies = _load_optional_dependencies()

    assert "matrix" not in optional_dependencies
    assert "hermes-agent[matrix]" not in optional_dependencies["all"]
    # Must be present with a Linux platform marker.
    linux_gated = [
        dep for dep in optional_dependencies["all"]
        if "matrix" in dep and "linux" in dep
    ]
    assert linux_gated, "expected hermes-agent[matrix] with sys_platform=='linux' marker in [all]"

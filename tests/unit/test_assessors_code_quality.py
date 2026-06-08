"""Tests for TypeAnnotationsAssessor — Python test file/function skipping (#385)."""

import subprocess

import pytest

from agentready.assessors.code_quality import TypeAnnotationsAssessor
from agentready.models.repository import Repository


def _make_py_repo(tmp_path, languages=None):
    """Create a test Python repository with git init."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    return Repository(
        path=tmp_path,
        name="test-py-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=languages or {"Python": 20},
        total_files=30,
        total_lines=5000,
    )


def _git_add(tmp_path, *files):
    """Stage files in git so git ls-files finds them."""
    for f in files:
        subprocess.run(
            ["git", "add", str(f)],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )


class TestIsTestFile:
    """Unit tests for _is_python_test_file static method."""

    @pytest.mark.parametrize(
        "path",
        [
            "tests/test_foo.py",
            "test/test_bar.py",
            "tests/unit/test_baz.py",
            "src/tests/test_helpers.py",
            "test_something.py",
            "foo_test.py",
            "conftest.py",
            "tests/conftest.py",
        ],
    )
    def test_identifies_test_files(self, path):
        assert TypeAnnotationsAssessor._is_python_test_file(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "src/app.py",
            "src/utils/helpers.py",
            "main.py",
            "lib/testing_utils.py",
        ],
    )
    def test_identifies_non_test_files(self, path):
        assert TypeAnnotationsAssessor._is_python_test_file(path) is False


class TestPythonTypeAnnotationsSkipTests:
    """Integration tests: test files and test functions are excluded from scoring."""

    def test_test_files_excluded_from_scoring(self, tmp_path):
        """Test files in tests/ should not affect type annotation scoring."""
        repo = _make_py_repo(tmp_path)

        # Source file: fully typed
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text("def greet(name: str) -> str:\n    return name\n")

        # Test file: untyped (should be excluded)
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_app.py").write_text("def test_greet():\n    assert True\n")

        _git_add(tmp_path, src / "app.py", tests / "test_app.py")

        assessor = TypeAnnotationsAssessor()
        finding = assessor._assess_python_types(repo)

        assert finding.status == "pass"
        assert "1/1" in finding.evidence[0]

    def test_test_functions_excluded_in_source_files(self, tmp_path):
        """Test functions (test_*) inside source files should be excluded."""
        repo = _make_py_repo(tmp_path)

        (tmp_path / "app.py").write_text(
            "def greet(name: str) -> str:\n"
            "    return name\n"
            "\n"
            "def test_greet():\n"
            "    assert greet('hi') == 'hi'\n"
        )

        _git_add(tmp_path, tmp_path / "app.py")

        assessor = TypeAnnotationsAssessor()
        finding = assessor._assess_python_types(repo)

        assert finding.status == "pass"
        assert "1/1" in finding.evidence[0]

    def test_untyped_source_still_fails(self, tmp_path):
        """Non-test source without annotations should still fail."""
        repo = _make_py_repo(tmp_path)

        (tmp_path / "app.py").write_text("def greet(name):\n    return name\n")

        _git_add(tmp_path, tmp_path / "app.py")

        assessor = TypeAnnotationsAssessor()
        finding = assessor._assess_python_types(repo)

        assert finding.status == "fail"

    def test_only_test_files_returns_not_applicable(self, tmp_path):
        """Repo with only test files should return not_applicable."""
        repo = _make_py_repo(tmp_path)

        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_foo.py").write_text("def test_foo():\n    assert True\n")

        _git_add(tmp_path, tests / "test_foo.py")

        assessor = TypeAnnotationsAssessor()
        finding = assessor._assess_python_types(repo)

        assert finding.status == "not_applicable"

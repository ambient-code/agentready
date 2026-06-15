"""Tests for code quality assessors."""

import json
import subprocess
from unittest.mock import patch

from agentready.assessors.code_quality import (
    CyclomaticComplexityAssessor,
    TypeAnnotationsAssessor,
)
from agentready.models.repository import Repository


def _make_python_repo(tmp_path, **kwargs):
    """Create a test Python repository with git init and typed functions."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

    # Create a Python file with typed functions for a passing coverage score
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").touch()
    (src_dir / "main.py").write_text(
        "def greet(name: str) -> str:\n"
        "    return f'Hello {name}'\n\n"
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n\n"
        "def multiply(x: float, y: float) -> float:\n"
        "    return x * y\n"
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)

    return Repository(
        path=tmp_path,
        name="test-python-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=kwargs.get("languages", {"Python": 100}),
        total_files=kwargs.get("total_files", 10),
        total_lines=kwargs.get("total_lines", 1000),
    )


def _make_python_repo_low_coverage(tmp_path, **kwargs):
    """Create a test Python repository with low type annotation coverage."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").touch()
    (src_dir / "main.py").write_text(
        "def greet(name):\n"
        "    return f'Hello {name}'\n\n"
        "def add(a, b):\n"
        "    return a + b\n\n"
        "def multiply(x, y):\n"
        "    return x * y\n\n"
        "def typed_func(x: int) -> int:\n"
        "    return x\n"
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)

    return Repository(
        path=tmp_path,
        name="test-python-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=kwargs.get("languages", {"Python": 100}),
        total_files=kwargs.get("total_files", 10),
        total_lines=kwargs.get("total_lines", 1000),
    )


class TestPythonStrictModeDetection:
    """Test Python type checker strict mode detection (ADR A.6)."""

    def test_mypy_ini_strict_bonus(self, tmp_path):
        """mypy.ini with strict = true adds 15 bonus points."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "mypy.ini").write_text("[mypy]\nstrict = true\n")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("mypy strict mode" in e for e in finding.evidence)
        assert any("mypy.ini" in e for e in finding.evidence)

    def test_dot_mypy_ini_strict_bonus(self, tmp_path):
        """`.mypy.ini` with strict = true adds bonus."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / ".mypy.ini").write_text("[mypy]\nstrict = true\n")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("mypy strict mode" in e for e in finding.evidence)
        assert any(".mypy.ini" in e for e in finding.evidence)

    def test_setup_cfg_mypy_strict_bonus(self, tmp_path):
        """setup.cfg [mypy] with strict = true adds bonus."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "setup.cfg").write_text("[mypy]\nstrict = true\n")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("mypy strict mode" in e for e in finding.evidence)
        assert any("setup.cfg" in e for e in finding.evidence)

    def test_mypy_disallow_untyped_defs_bonus(self, tmp_path):
        """mypy.ini with disallow_untyped_defs = true triggers bonus."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "mypy.ini").write_text("[mypy]\ndisallow_untyped_defs = true\n")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("mypy strict mode" in e for e in finding.evidence)

    def test_pyproject_mypy_strict_bonus(self, tmp_path):
        """pyproject.toml [tool.mypy] strict = true adds bonus."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[tool.mypy]\nstrict = true\n")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("mypy strict mode" in e for e in finding.evidence)
        assert any("pyproject.toml" in e for e in finding.evidence)

    def test_pyproject_pyright_strict_bonus(self, tmp_path):
        """pyproject.toml [tool.pyright] typeCheckingMode = 'strict' adds bonus."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[tool.pyright]\ntypeCheckingMode = "strict"\n'
        )

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("pyright strict mode" in e for e in finding.evidence)
        assert any("pyproject.toml" in e for e in finding.evidence)

    def test_pyrightconfig_json_strict_bonus(self, tmp_path):
        """pyrightconfig.json with typeCheckingMode: strict adds bonus."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "pyrightconfig.json").write_text(
            json.dumps({"typeCheckingMode": "strict"})
        )

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("pyright strict mode" in e for e in finding.evidence)
        assert any("pyrightconfig.json" in e for e in finding.evidence)

    def test_pyrightconfig_json_with_comments(self, tmp_path):
        """pyrightconfig.json with JSONC comments is parsed correctly."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "pyrightconfig.json").write_text(
            '{\n  // strict type checking\n  "typeCheckingMode": "strict"\n}\n'
        )

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("pyright strict mode" in e for e in finding.evidence)

    def test_no_strict_config_no_bonus(self, tmp_path):
        """No type checker config means no strict mode bonus."""
        repo = _make_python_repo(tmp_path)

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert not any("strict mode" in e for e in finding.evidence)

    def test_mypy_ini_without_strict_no_bonus(self, tmp_path):
        """mypy.ini without strict settings gives no bonus."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "mypy.ini").write_text("[mypy]\nwarn_return_any = true\n")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert not any("strict mode" in e for e in finding.evidence)

    def test_strict_mode_capped_at_100(self, tmp_path):
        """High coverage + strict mode doesn't exceed 100."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "mypy.ini").write_text("[mypy]\nstrict = true\n")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.score <= 100.0

    def test_strict_mode_improves_low_coverage_score(self, tmp_path):
        """Strict mode adds 15 pts to a low-coverage repo's score."""
        no_strict_dir = tmp_path / "no_strict"
        no_strict_dir.mkdir()
        repo_no_strict = _make_python_repo_low_coverage(no_strict_dir)
        assessor = TypeAnnotationsAssessor()
        baseline = assessor.assess(repo_no_strict)

        with_strict_dir = tmp_path / "with_strict"
        with_strict_dir.mkdir()
        repo_with_strict = _make_python_repo_low_coverage(with_strict_dir)
        (with_strict_dir / "mypy.ini").write_text("[mypy]\nstrict = true\n")
        with_strict = assessor.assess(repo_with_strict)

        assert with_strict.score == baseline.score + 15.0

    def test_pyproject_mypy_disallow_untyped_defs_bonus(self, tmp_path):
        """pyproject.toml [tool.mypy] disallow_untyped_defs = true triggers bonus."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mypy]\ndisallow_untyped_defs = true\n"
        )

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert any("mypy strict mode" in e for e in finding.evidence)

    def test_malformed_pyproject_no_crash(self, tmp_path):
        """Malformed pyproject.toml doesn't crash the strict mode check."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text("not valid toml {{{")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status in ("pass", "fail")
        assert not any("strict mode" in e for e in finding.evidence)

    def test_malformed_pyrightconfig_no_crash(self, tmp_path):
        """Malformed pyrightconfig.json doesn't crash the strict mode check."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "pyrightconfig.json").write_text("not valid json !!!")

        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)

        assert finding.status in ("pass", "fail")
        assert not any("strict mode" in e for e in finding.evidence)


# =============================================================================
# CyclomaticComplexityAssessor — lizard library path
# =============================================================================


class _FakeFunc:
    """Minimal stand-in for lizard.FunctionInfo."""

    def __init__(self, ccn):
        self.cyclomatic_complexity = ccn


class _FakeFileInfo:
    """Minimal stand-in for lizard.FileInformation."""

    def __init__(self, funcs):
        self.function_list = [_FakeFunc(ccn) for ccn in funcs]


def _make_js_repo(tmp_path, **kwargs):
    """Create a test JavaScript repository."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    return Repository(
        path=tmp_path,
        name="test-js-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=kwargs.get("languages", {"JavaScript": 100}),
        total_files=10,
        total_lines=1000,
    )


class TestCyclomaticComplexityLizard:
    """Test _assess_with_lizard using the lizard library API."""

    def test_low_complexity_passes(self, tmp_path):
        """Average CCN below threshold produces a pass finding."""
        repo = _make_js_repo(tmp_path)
        assessor = CyclomaticComplexityAssessor()

        fake_results = [_FakeFileInfo([2, 3]), _FakeFileInfo([1, 4])]
        with patch(
            "agentready.assessors.code_quality.lizard.analyze",
            return_value=fake_results,
        ):
            finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score > 0
        assert "lizard" in finding.evidence[0]
        assert "2.5" in finding.measured_value

    def test_high_complexity_fails(self, tmp_path):
        """Average CCN above threshold produces a fail finding."""
        repo = _make_js_repo(tmp_path)
        assessor = CyclomaticComplexityAssessor()

        fake_results = [_FakeFileInfo([15, 20, 18])]
        with patch(
            "agentready.assessors.code_quality.lizard.analyze",
            return_value=fake_results,
        ):
            finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.remediation is not None

    def test_no_functions_returns_not_applicable(self, tmp_path):
        """No functions found produces a not_applicable finding."""
        repo = _make_js_repo(tmp_path)
        assessor = CyclomaticComplexityAssessor()

        with patch("agentready.assessors.code_quality.lizard.analyze", return_value=[]):
            finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_empty_function_lists_returns_not_applicable(self, tmp_path):
        """Files with no functions produce a not_applicable finding."""
        repo = _make_js_repo(tmp_path)
        assessor = CyclomaticComplexityAssessor()

        fake_results = [_FakeFileInfo([]), _FakeFileInfo([])]
        with patch(
            "agentready.assessors.code_quality.lizard.analyze",
            return_value=fake_results,
        ):
            finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_analyze_exception_returns_error(self, tmp_path):
        """Exception from lizard.analyze produces an error finding."""
        repo = _make_js_repo(tmp_path)
        assessor = CyclomaticComplexityAssessor()

        with patch(
            "agentready.assessors.code_quality.lizard.analyze",
            side_effect=RuntimeError("lizard crashed"),
        ):
            finding = assessor.assess(repo)

        assert finding.status == "error"
        assert "lizard crashed" in finding.error_message


# =============================================================================
# CyclomaticComplexityAssessor — radon library path
# =============================================================================


class TestCyclomaticComplexityRadon:
    """Test _assess_python_complexity using the radon library API."""

    def test_low_complexity_passes(self, tmp_path):
        """Average complexity below threshold produces a pass finding."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        (tmp_path / "main.py").write_text(
            "def foo(x):\n    if x:\n        return 1\n    return 0\n"
        )
        repo = _make_python_repo(tmp_path)

        assessor = CyclomaticComplexityAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score > 0
        assert "Average cyclomatic complexity" in finding.evidence[0]

    def test_no_python_files_returns_not_applicable(self, tmp_path):
        """No Python files produces a not_applicable finding."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        repo = Repository(
            path=tmp_path,
            name="test-empty-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=0,
            total_lines=0,
        )

        assessor = CyclomaticComplexityAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"

    def test_syntax_error_files_skipped(self, tmp_path):
        """Files with syntax errors are skipped, not crash the assessor."""
        repo = _make_python_repo(tmp_path)
        (tmp_path / "bad.py").write_text("def broken(\n")

        assessor = CyclomaticComplexityAssessor()
        finding = assessor.assess(repo)

        assert finding.status in ("pass", "fail", "not_applicable")

    def test_radon_exception_returns_error(self, tmp_path):
        """Unexpected exception produces an error finding."""
        repo = _make_python_repo(tmp_path)
        assessor = CyclomaticComplexityAssessor()

        with patch(
            "agentready.assessors.code_quality.radon.complexity.cc_visit",
            side_effect=RuntimeError("radon crashed"),
        ):
            finding = assessor.assess(repo)

        assert finding.status == "error"
        assert "radon crashed" in finding.error_message

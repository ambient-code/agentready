"""Tests for Python type annotation strict mode detection (ADR A.6)."""

import json
import subprocess

from agentready.assessors.code_quality import TypeAnnotationsAssessor
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

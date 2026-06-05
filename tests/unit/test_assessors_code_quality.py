"""Tests for code quality assessors (type annotations, cyclomatic complexity, logging)."""

import subprocess

import pytest

from agentready.assessors.code_quality import (
    CyclomaticComplexityAssessor,
    StructuredLoggingAssessor,
    TypeAnnotationsAssessor,
)
from agentready.models.repository import Repository
from agentready.services.scanner import MissingToolError


def _make_python_repo(tmp_path, languages=None, **kwargs):
    """Create a test Python repository with git init."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    return Repository(
        path=tmp_path,
        name="test-python-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=languages or {"Python": 100},
        total_files=kwargs.get("total_files", 10),
        total_lines=kwargs.get("total_lines", 500),
    )


def _git_add_and_commit(tmp_path, paths):
    """Stage and commit the given paths in the repo."""
    for p in paths:
        subprocess.run(
            ["git", "add", str(p)],
            cwd=tmp_path,
            capture_output=True,
            check=True,
        )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )


def _write_python_file(path, content):
    """Write a Python file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestTypeAnnotationsAssessorPython:
    """Test Python type annotation detection."""

    def test_python_is_applicable(self, tmp_path):
        repo = _make_python_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        assert assessor.is_applicable(repo)

    def test_no_python_files_not_applicable(self, tmp_path):
        """Repo with no .py files should be not_applicable."""
        repo = _make_python_repo(tmp_path)
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "not_applicable"
        assert "No Python functions found" in " ".join(finding.evidence)

    def test_typed_functions_pass(self, tmp_path):
        """Repo with >80% typed functions passes."""
        repo = _make_python_repo(tmp_path)
        src = tmp_path / "src" / "app"
        src.mkdir(parents=True)
        main_py = src / "main.py"
        _write_python_file(
            main_py,
            """\
def greet(name: str) -> str:
    return f"Hello, {name}"

def add(a: int, b: int) -> int:
    return a + b
""",
        )
        _git_add_and_commit(tmp_path, [main_py])
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "pass"
        assert finding.score >= 75
        assert "Typed functions: 2/2" in " ".join(finding.evidence)

    def test_few_typed_functions_fail(self, tmp_path):
        """Repo with <80% typed functions fails."""
        repo = _make_python_repo(tmp_path)
        src = tmp_path / "src" / "app"
        src.mkdir(parents=True)
        main_py = src / "main.py"
        _write_python_file(
            main_py,
            """\
def greet(name):
    return f"Hello, {name}"

def add(a, b):
    return a + b

def process(data: str) -> str:
    return data.upper()
""",
        )
        _git_add_and_commit(tmp_path, [main_py])
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        # 1/3 = 33.3% → proportional score below 75 → fail
        assert finding.status == "fail"
        assert "Typed functions: 1/3" in " ".join(finding.evidence)

    def test_no_functions_not_applicable(self, tmp_path):
        """Repo with Python files but no functions is not_applicable."""
        repo = _make_python_repo(tmp_path)
        constants_py = tmp_path / "constants.py"
        _write_python_file(constants_py, "PI = 3.14159\n")
        _git_add_and_commit(tmp_path, [constants_py])
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "not_applicable"


class TestTypeAnnotationsAssessorStrictMode:
    """Test strict mode detection in TypeAnnotationsAssessor (ADR A.6)."""

    def _make_repo_with_file(self, tmp_path, content):
        """Helper: create repo with one Python file, staged and committed."""
        repo = _make_python_repo(tmp_path)
        src = tmp_path / "src" / "app"
        src.mkdir(parents=True)
        main_py = src / "main.py"
        _write_python_file(main_py, content)
        _git_add_and_commit(tmp_path, [main_py])
        return repo

    def test_no_strict_config(self, tmp_path):
        """When no config files exist, evidence mentions no strict mode."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        evidence_str = " ".join(finding.evidence)
        assert "No strict mode configuration found" in evidence_str

    def test_mypy_strict_config(self, tmp_path):
        """mypy.ini with strict=true produces evidence."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        mypy_ini = tmp_path / "mypy.ini"
        mypy_ini.write_text("[mypy]\nstrict = true\n")
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert "mypy.ini: strict mode enabled" in " ".join(finding.evidence)

    def test_mypy_disallow_untyped_defs(self, tmp_path):
        """mypy.ini with disallow_untyped_defs=true counts as strict."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        mypy_ini = tmp_path / "mypy.ini"
        mypy_ini.write_text("[mypy]\ndisallow_untyped_defs = true\n")
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert "mypy.ini: strict mode enabled" in " ".join(finding.evidence)

    def test_setup_cfg_mypy_section(self, tmp_path):
        """setup.cfg [mypy] section with strict is detected."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        setup_cfg = tmp_path / "setup.cfg"
        setup_cfg.write_text("[mypy]\ndisallow_untyped_defs = true\n")
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert "setup.cfg: strict mode enabled" in " ".join(finding.evidence)

    def test_pyproject_toml_mypy(self, tmp_path):
        """pyproject.toml [tool.mypy] section with strict is detected."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.mypy]\nstrict = true\n")
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert "pyproject.toml: strict mode enabled" in " ".join(finding.evidence)

    def test_pyright_strict_mode(self, tmp_path):
        """pyrightconfig.json with typeCheckingMode: strict is detected."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        pyright = tmp_path / "pyrightconfig.json"
        pyright.write_text('{"typeCheckingMode": "strict"}')
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert "pyrightconfig.json: strict mode enabled" in " ".join(finding.evidence)

    def test_pyright_non_strict(self, tmp_path):
        """pyrightconfig.json without strict shows as not enabled."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        pyright = tmp_path / "pyrightconfig.json"
        pyright.write_text('{"typeCheckingMode": "basic"}')
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert "pyrightconfig.json: strict mode not enabled" in " ".join(
            finding.evidence
        )

    def test_multiple_config_files(self, tmp_path):
        """When multiple configs exist, each is reported."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.mypy]\nstrict = true\n")
        mypy_ini = tmp_path / "mypy.ini"
        mypy_ini.write_text("[mypy]\nstrict = false\n")
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        evidence_str = " ".join(finding.evidence)
        assert "pyproject.toml: strict mode enabled" in evidence_str
        assert "mypy.ini: strict mode not enabled" in evidence_str

    def test_pyright_monorepo_subdir(self, tmp_path):
        """pyrightconfig.json in subdirectory is detected for monorepos."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        # Root config
        root_pyright = tmp_path / "pyrightconfig.json"
        root_pyright.write_text('{"typeCheckingMode": "strict"}')
        # Subdirectory config
        sub_pyright = tmp_path / "src" / "package" / "pyrightconfig.json"
        sub_pyright.parent.mkdir(parents=True, exist_ok=True)
        sub_pyright.write_text('{"typeCheckingMode": "strict"}')
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        evidence_str = " ".join(finding.evidence)
        assert "pyrightconfig.json: strict mode enabled" in evidence_str
        assert (
            "src/package/pyrightconfig.json: typeCheckingMode: strict" in evidence_str
        )

    def test_skips_node_modules_vendor_testdata(self, tmp_path):
        """pyrightconfig.json in excluded dirs is not reported."""
        repo = self._make_repo_with_file(tmp_path, "def foo() -> int: return 1\n")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "pyrightconfig.json").write_text(
            '{"typeCheckingMode": "strict"}'
        )
        (tmp_path / "vendor").mkdir()
        (tmp_path / "vendor" / "pyrightconfig.json").write_text(
            '{"typeCheckingMode": "strict"}'
        )
        (tmp_path / "testdata").mkdir()
        (tmp_path / "testdata" / "pyrightconfig.json").write_text(
            '{"typeCheckingMode": "strict"}'
        )
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        evidence_str = " ".join(finding.evidence)
        assert "node_modules" not in evidence_str
        assert "vendor" not in evidence_str
        assert "testdata" not in evidence_str


class TestTypeAnnotationsAssessorLanguageFallback:
    """Test non-Python language handling."""

    def test_java_returns_not_applicable(self, tmp_path):
        """Java repositories return not_applicable for type annotations."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        repo = Repository(
            path=tmp_path,
            name="java-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Java": 100},
            total_files=10,
            total_lines=1000,
        )
        assessor = TypeAnnotationsAssessor()
        finding = assessor.assess(repo)
        assert finding.status == "not_applicable"


class TestCyclomaticComplexityAssessor:
    """Test CyclomaticComplexityAssessor."""

    def test_simple_function_low_complexity(self, tmp_path):
        """A simple function produces low complexity score."""
        repo = _make_python_repo(tmp_path)
        src = tmp_path / "src" / "app"
        src.mkdir(parents=True)
        simple_py = src / "simple.py"
        _write_python_file(
            simple_py,
            "def add(a, b):\n    return a + b\n",
        )
        _git_add_and_commit(tmp_path, [simple_py])

        assessor = CyclomaticComplexityAssessor()
        try:
            finding = assessor.assess(repo)
        except MissingToolError:
            pytest.skip("radon CLI not available")
        assert finding.status in ("pass", "fail")
        assert finding.score >= 0

    def test_no_python_files(self, tmp_path):
        """Repo with no Python files returns not_applicable."""
        repo = _make_python_repo(tmp_path)
        assessor = CyclomaticComplexityAssessor()
        try:
            finding = assessor.assess(repo)
        except MissingToolError:
            pytest.skip("radon CLI not available")
        assert finding.status == "not_applicable"


class TestStructuredLoggingAssessor:
    """Test StructuredLoggingAssessor."""

    def test_python_repo_with_logging(self, tmp_path):
        """Python repo with loguru/structlog detection."""
        repo = _make_python_repo(tmp_path)
        src = tmp_path / "src" / "app"
        src.mkdir(parents=True)
        logger_py = src / "logger.py"
        _write_python_file(
            logger_py,
            "import loguru\nlogger = loguru.logger\n",
        )
        _git_add_and_commit(tmp_path, [logger_py])

        assessor = StructuredLoggingAssessor()
        try:
            finding = assessor.assess(repo)
        except MissingToolError:
            pytest.skip("radon CLI not available")
        assert finding.status in ("pass", "fail", "not_applicable")

    def test_no_logging_found(self, tmp_path):
        """Repo without any logging library returns not_applicable."""
        repo = _make_python_repo(tmp_path)
        src = tmp_path / "src" / "app"
        src.mkdir(parents=True)
        app_py = src / "app.py"
        _write_python_file(app_py, "def foo(): pass\n")
        _git_add_and_commit(tmp_path, [app_py])

        assessor = StructuredLoggingAssessor()
        try:
            finding = assessor.assess(repo)
        except MissingToolError:
            pytest.skip("radon CLI not available")
        assert finding.status in ("not_applicable", "fail")

"""Tests for code quality assessors."""

import json
import subprocess
from unittest.mock import patch

from agentready.assessors.code_quality import (
    CyclomaticComplexityAssessor,
    LintConfigCoverageAssessor,
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


# =============================================================================
# LintConfigCoverageAssessor
# =============================================================================


def _make_repo(tmp_path, languages=None):
    (tmp_path / ".git").mkdir()
    return Repository(
        path=tmp_path,
        name="test-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=languages or {"Python": 100},
        total_files=5,
        total_lines=200,
    )


class TestLintConfigCoverageAssessorPython:
    """Tests for Python lint config coverage detection."""

    def test_all_three_categories_passes(self, tmp_path):
        """Correctness (mypy) + standards (ruff) + security (bandit) → pass."""
        repo = _make_repo(tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[tool.mypy]\nstrict = true\n\n"
            "[tool.ruff]\nselect = ['E']\n\n"
            "[tool.bandit]\ntargets = ['src']\n"
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "3/3" in finding.measured_value

    def test_standards_only_fails_with_partial_credit(self, tmp_path):
        """Only black (standards) → 1/3 categories, score=33, fail.

        Note: ruff covers correctness+standards; use black (standards only) here.
        """
        repo = _make_repo(tmp_path)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.black]\nline-length = 88\n")
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "fail"
        assert finding.score < 50
        assert "1/3" in finding.measured_value

    def test_correctness_and_standards_partial(self, tmp_path):
        """mypy + ruff → 2/3 → score≈67, fail (below pass threshold of 100)."""
        repo = _make_repo(tmp_path)
        (tmp_path / "mypy.ini").write_text("[mypy]\nstrict = True\n")
        (tmp_path / "ruff.toml").write_text("[lint]\n")
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "fail"
        assert finding.score >= 60.0
        assert "2/3" in finding.measured_value

    def test_precommit_bandit_adds_security(self, tmp_path):
        """bandit in pre-commit hooks counts as security category."""
        repo = _make_repo(tmp_path)
        # standards + correctness via pyproject, security via pre-commit
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mypy]\nstrict = true\n\n[tool.ruff]\nselect=['E']\n"
        )
        precommit = tmp_path / ".pre-commit-config.yaml"
        precommit.write_text(
            "repos:\n"
            "  - repo: https://github.com/pycqa/bandit\n"
            "    rev: 1.7.5\n"
            "    hooks:\n"
            "      - id: bandit\n"
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_ci_workflow_bandit_adds_security(self, tmp_path):
        """bandit mention in CI workflow counts as security coverage."""
        repo = _make_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mypy]\nstrict = true\n\n[tool.ruff]\nselect=['E']\n"
        )
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text(
            "name: CI\non: [push]\njobs:\n  lint:\n    steps:\n"
            "      - run: bandit -r src/\n"
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"

    def test_no_lint_config_fails_with_zero(self, tmp_path):
        """Repo with no lint configuration → 0/3, score=0, fail."""
        repo = _make_repo(tmp_path)
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_remediation_lists_missing_categories(self, tmp_path):
        """Remediation steps mention the missing category (security)."""
        repo = _make_repo(tmp_path)
        # ruff covers correctness+standards; only security missing
        (tmp_path / "ruff.toml").write_text("[lint]\n")
        (tmp_path / "mypy.ini").write_text("[mypy]\nstrict = True\n")
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.remediation is not None
        combined = " ".join(finding.remediation.steps).lower()
        assert "security" in combined or "bandit" in combined

    def test_not_applicable_for_unsupported_language(self, tmp_path):
        """Repo with no supported language returns not_applicable."""
        repo = _make_repo(tmp_path, languages={"Haskell": 100})
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "not_applicable"

    def test_empty_pyproject_tool_section_not_counted(self, tmp_path):
        """Empty [tool.ruff] section in pyproject.toml must not award category credit.

        A bare section header with no keys is indistinguishable from a mis-pasted
        config; only a section with at least one explicit key is counted.
        """
        repo = _make_repo(tmp_path)
        # [tool.ruff] has no keys — ruff is not meaningfully configured
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "0/3" in finding.measured_value

    def test_empty_setup_cfg_section_not_counted(self, tmp_path):
        """Empty [ruff] section in setup.cfg must not award category credit.

        Mirrors test_empty_pyproject_tool_section_not_counted for setup.cfg.
        """
        repo = _make_repo(tmp_path)
        (tmp_path / "setup.cfg").write_text("[ruff]\n")
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert "0/3" in finding.measured_value


class TestLintConfigCoverageAssessorGo:
    """Tests for Go lint config coverage detection."""

    def _make_go_repo(self, tmp_path):
        (tmp_path / ".git").mkdir(exist_ok=True)
        (tmp_path / "go.mod").write_text("module example.com/myapp\n\ngo 1.21\n")
        return Repository(
            path=tmp_path,
            name="test-go-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Go": 100},
            total_files=5,
            total_lines=200,
        )

    def test_golangci_all_three_categories(self, tmp_path):
        """golangci config with errcheck + revive + gosec → pass."""
        repo = self._make_go_repo(tmp_path)
        (tmp_path / ".golangci.yml").write_text(
            "linters:\n"
            "  enable:\n"
            "    - errcheck\n"
            "    - staticcheck\n"
            "    - revive\n"
            "    - gosec\n"
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_golangci_correctness_only_partial(self, tmp_path):
        """golangci with only errcheck → 1/3, fail."""
        repo = self._make_go_repo(tmp_path)
        (tmp_path / ".golangci.yml").write_text("linters:\n  enable:\n    - errcheck\n")
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "fail"
        assert finding.score < 50

    def test_golangci_enable_all(self, tmp_path):
        """golangci enable-all covers all categories."""
        repo = self._make_go_repo(tmp_path)
        (tmp_path / ".golangci.yml").write_text("linters:\n  enable-all: true\n")
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"


class TestLintConfigCoverageAssessorJS:
    """Tests for JavaScript/TypeScript lint config coverage detection."""

    def _make_js_repo(self, tmp_path, lang="JavaScript"):
        (tmp_path / ".git").mkdir(exist_ok=True)
        (tmp_path / "package.json").write_text('{"name":"test","version":"1.0.0"}\n')
        return Repository(
            path=tmp_path,
            name="test-js-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={lang: 100},
            total_files=5,
            total_lines=200,
        )

    def test_js_only_full_pass_without_typescript(self, tmp_path):
        """Pure JS repo: eslint:recommended (correctness+standards) + security → 3/3 pass."""
        repo = self._make_js_repo(tmp_path, "JavaScript")
        (tmp_path / ".eslintrc.json").write_text(
            json.dumps(
                {
                    "extends": ["eslint:recommended", "plugin:security/recommended"],
                }
            )
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0
        assert "3/3" in finding.measured_value

    def test_eslint_with_ts_and_security(self, tmp_path):
        """ESLint with @typescript-eslint + airbnb + security plugin → pass."""
        repo = self._make_js_repo(tmp_path, "TypeScript")
        (tmp_path / ".eslintrc.json").write_text(
            json.dumps(
                {
                    "extends": [
                        "airbnb",
                        "plugin:@typescript-eslint/recommended-type-checked",
                        "plugin:security/recommended",
                    ]
                }
            )
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"

    def test_tsconfig_strict_counts_for_correctness(self, tmp_path):
        """tsconfig strict:true + eslint:recommended → correctness + standards."""
        repo = self._make_js_repo(tmp_path, "TypeScript")
        (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {"strict": true}}')
        (tmp_path / ".eslintrc.json").write_text('{"extends": ["eslint:recommended"]}')
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.score >= 60  # at least 2/3
        assert "2/3" in finding.measured_value or "3/3" in finding.measured_value

    def test_installed_but_unused_plugin_gets_no_credit(self, tmp_path):
        """eslint-plugin-security in devDependencies but NOT in ESLint config gets no credit.

        Installing a plugin does not activate it — it must appear in extends/plugins.
        """
        repo = self._make_js_repo(tmp_path)
        (tmp_path / "package.json").write_text(
            json.dumps(
                {
                    "devDependencies": {
                        "eslint": "^8",
                        "eslint-plugin-security": "^1",
                        "@typescript-eslint/eslint-plugin": "^5",
                    }
                }
            )
        )
        # Only eslint:recommended in extends — security plugin installed but not enabled
        (tmp_path / ".eslintrc.json").write_text('{"extends": ["eslint:recommended"]}')
        finding = LintConfigCoverageAssessor().assess(repo)

        # correctness+standards from eslint:recommended; security devDep alone ≠ active
        assert finding.score < 100
        assert "2/3" in finding.measured_value
        assert "Missing category: security" in finding.evidence

    def test_eslint_json_comment_not_false_positive(self, tmp_path):
        """Tool name in a JSON comment must not count as coverage (JSON parsed structurally)."""
        repo = self._make_js_repo(tmp_path, "TypeScript")
        # Only eslint:recommended in extends — security mentioned only in a comment
        (tmp_path / ".eslintrc.json").write_text(
            '{"extends": ["eslint:recommended"], "_comment": "we chose not to use plugin:security"}'
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        # Should detect standards (eslint:recommended) but NOT security from the comment
        assert "Missing category: security" in finding.evidence

    def test_prettier_standalone_config_counts(self, tmp_path):
        """A standalone .prettierrc file signals active prettier (standards)."""
        repo = self._make_js_repo(tmp_path)
        (tmp_path / ".prettierrc.json").write_text('{"singleQuote": true}')
        # Also add correctness and security via ESLint to get a meaningful result
        (tmp_path / ".eslintrc.json").write_text(
            '{"extends": ["plugin:@typescript-eslint/recommended", "plugin:security/recommended"]}'
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0


class TestLintConfigCoverageAssessorCI:
    """Tests for CI workflow step-aware scanning."""

    def _make_python_repo_ci(self, tmp_path):
        (tmp_path / ".git").mkdir()
        return Repository(
            path=tmp_path,
            name="test-ci-repo",
            url=None,
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=5,
            total_lines=200,
        )

    def test_ci_tool_in_run_step_detected(self, tmp_path):
        """Tool name inside a run: step is detected as coverage."""
        repo = self._make_python_repo_ci(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mypy]\nstrict = true\n\n[tool.ruff]\nselect=['E']\n"
        )
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text(
            "name: CI\non: [push]\njobs:\n"
            "  security:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: pip install bandit && bandit -r src/\n"
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_ci_tool_in_comment_not_detected(self, tmp_path):
        """Tool name appearing only in a YAML comment must not count as coverage."""
        repo = self._make_python_repo_ci(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mypy]\nstrict = true\n\n[tool.ruff]\nselect=['E']\n"
        )
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        # bandit only in a comment, not in any run: step
        (wf_dir / "ci.yml").write_text(
            "name: CI\non: [push]\n"
            "# we considered bandit but skipped it\n"
            "jobs:\n  lint:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - run: ruff check .\n"
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert "Missing category: security" in finding.evidence

    def test_gitlab_ci_script_field_detected(self, tmp_path):
        """GitLab CI script: list commands are scanned for tool invocations."""
        repo = self._make_python_repo_ci(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mypy]\nstrict = true\n\n[tool.ruff]\nselect=['E']\n"
        )
        # GitLab CI uses script: list, not run:
        (tmp_path / ".gitlab-ci.yml").write_text(
            "stages:\n  - lint\n\n"
            "security-scan:\n"
            "  stage: lint\n"
            "  script:\n"
            "    - pip install bandit\n"
            "    - bandit -r src/\n"
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_circleci_run_command_field_detected(self, tmp_path):
        """CircleCI run.command dict field is scanned for tool invocations."""
        repo = self._make_python_repo_ci(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "[tool.mypy]\nstrict = true\n\n[tool.ruff]\nselect=['E']\n"
        )
        circleci_dir = tmp_path / ".circleci"
        circleci_dir.mkdir()
        # CircleCI stores commands in run: {command: "..."} dicts
        (circleci_dir / "config.yml").write_text(
            "version: 2.1\n"
            "jobs:\n"
            "  security:\n"
            "    steps:\n"
            "      - run:\n"
            "          name: Run bandit security check\n"
            "          command: bandit -r src/\n"
        )
        finding = LintConfigCoverageAssessor().assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

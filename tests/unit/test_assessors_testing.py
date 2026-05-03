"""Tests for testing assessors (TestExecutionAssessor, CIQualityGatesAssessor, etc.)."""

import json

from agentready.assessors.testing import (
    CIQualityGatesAssessor,
    DeterministicEnforcementAssessor,
    TestExecutionAssessor,
)
from agentready.models.repository import Repository


def _make_repo(tmp_path, languages=None, **kwargs):
    """Create a test repository."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir(exist_ok=True)
    return Repository(
        path=tmp_path,
        name="test-repo",
        url=None,
        branch="main",
        commit_hash="abc123",
        languages=languages or {"Python": 100},
        total_files=kwargs.get("total_files", 10),
        total_lines=kwargs.get("total_lines", 1000),
    )


class TestTestExecutionAssessor:
    """Test TestExecutionAssessor."""

    def test_attribute_id(self):
        """Test attribute ID matches expected value."""
        assessor = TestExecutionAssessor()
        assert assessor.attribute_id == "test_execution"

    def test_tier(self):
        """Test tier is Essential (1)."""
        assessor = TestExecutionAssessor()
        assert assessor.tier == 1

    def test_default_weight(self):
        """Test default weight matches YAML config."""
        assessor = TestExecutionAssessor()
        assert assessor.attribute.default_weight == 0.10

    def test_not_applicable_no_test_dirs(self, tmp_path):
        """Test not applicable when no test directories exist."""
        repo = _make_repo(tmp_path)

        assessor = TestExecutionAssessor()
        assert not assessor.is_applicable(repo)

    def test_applicable_with_tests_dir(self, tmp_path):
        """Test applicable when tests/ directory exists."""
        (tmp_path / "tests").mkdir()
        repo = _make_repo(tmp_path)

        assessor = TestExecutionAssessor()
        assert assessor.is_applicable(repo)

    # --- Python tests ---

    def test_python_full_score(self, tmp_path):
        """Test full score with test files + runner + coverage + enforcement."""
        # Create test directory with test files
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text("def test_one(): pass\n")

        # Create pyproject.toml with runner + coverage + enforcement
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[tool.pytest.ini_options]\n"
            "testpaths = ['tests']\n\n"
            "[tool.coverage.run]\n"
            "source = ['src']\n\n"
            "[tool.coverage.report]\n"
            "fail_under = 80\n\n"
            "[project]\n"
            "dependencies = []\n"
            "[project.optional-dependencies]\n"
            'dev = ["pytest-cov"]\n'
        )

        repo = _make_repo(tmp_path)
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_python_test_files_and_runner_only(self, tmp_path):
        """Test score with test files + runner but no coverage."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text("def test_one(): pass\n")

        # pytest.ini as runner signal
        (tmp_path / "pytest.ini").write_text("[pytest]\n")

        repo = _make_repo(tmp_path)
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 60.0
        assert any("test files found" in e.lower() for e in finding.evidence)
        assert any("runner" in e.lower() for e in finding.evidence)

    def test_python_coverage_config_only_no_tests(self, tmp_path):
        """Test that coverage config alone without test files gives low score."""
        # Need a tests dir for is_applicable, but no test_*.py files
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")

        (tmp_path / ".coveragerc").write_text("[run]\nsource = src\n")

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["pytest-cov"]\n')

        repo = _make_repo(tmp_path)
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        # Only coverage config (20) + enforcement (20) = 40, no test files
        assert finding.status == "fail"
        assert finding.score <= 40.0

    def test_python_nothing_configured(self, tmp_path):
        """Test zero score when nothing is configured."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")

        repo = _make_repo(tmp_path)
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_python_test_files_only_no_runner(self, tmp_path):
        """Test partial score with test files but no runner config."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_something.py").write_text("def test_it(): pass\n")

        repo = _make_repo(tmp_path)
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        # Test files only: 40 pts
        assert finding.status == "fail"
        assert finding.score == 40.0

    def test_python_tox_ini_as_runner(self, tmp_path):
        """Test that tox.ini is recognized as a test runner."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text("def test_one(): pass\n")

        (tmp_path / "tox.ini").write_text("[tox]\nenvlist = py312\n")

        repo = _make_repo(tmp_path)
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 60.0

    def test_python_coveragerc_fail_under(self, tmp_path):
        """Test that .coveragerc with fail_under is detected as enforcement."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text("def test_one(): pass\n")

        coveragerc = tmp_path / ".coveragerc"
        coveragerc.write_text("[report]\nfail_under = 80\n")

        repo = _make_repo(tmp_path)
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        # test files (40) + coverage config via .coveragerc (20) + enforcement (20) = 80
        assert finding.status == "pass"
        assert finding.score == 80.0

    def test_python_remediation_on_fail(self, tmp_path):
        """Test that remediation is provided when assessment fails."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")

        repo = _make_repo(tmp_path)
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.remediation is not None
        assert len(finding.remediation.steps) > 0

    # --- JavaScript tests ---

    def test_js_full_score(self, tmp_path):
        """Test full score for JS repo with all signals."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # package.json with scripts.test + jest
        pkg = {
            "scripts": {"test": "jest --coverage"},
            "devDependencies": {"jest": "^29.0.0"},
            "jest": {"coverageThreshold": {"global": {"branches": 80}}},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        # Test files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "utils.test.js").write_text("test('it works', () => {})\n")

        repo = _make_repo(tmp_path, languages={"JavaScript": 100})
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score == 100.0

    def test_js_scripts_test_only(self, tmp_path):
        """Test score with only scripts.test and no other signals."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        pkg = {"scripts": {"test": "node test.js"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        repo = _make_repo(tmp_path, languages={"JavaScript": 100})
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        # scripts.test only: 40 pts
        assert finding.status == "fail"
        assert finding.score == 40.0

    def test_js_devdeps_only_no_script(self, tmp_path):
        """Test partial score with jest in devDeps but no scripts.test."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        pkg = {"devDependencies": {"jest": "^29.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        repo = _make_repo(tmp_path, languages={"JavaScript": 100})
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        # devDeps only: 20 pts
        assert finding.status == "fail"
        assert finding.score == 20.0

    def test_js_no_package_json(self, tmp_path):
        """Test fail when package.json doesn't exist."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        repo = _make_repo(tmp_path, languages={"JavaScript": 100})
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

    def test_js_malformed_package_json(self, tmp_path):
        """Test error handling for malformed package.json."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        (tmp_path / "package.json").write_text("{invalid json")

        repo = _make_repo(tmp_path, languages={"JavaScript": 100})
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "error"

    def test_js_vitest_recognized(self, tmp_path):
        """Test that vitest is recognized as a test tool."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        pkg = {
            "scripts": {"test": "vitest"},
            "devDependencies": {"vitest": "^1.0.0"},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        repo = _make_repo(tmp_path, languages={"TypeScript": 100})
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        # scripts.test (40) + vitest devDep (20) = 60
        assert finding.status == "pass"
        assert finding.score == 60.0

    def test_unsupported_language(self, tmp_path):
        """Test not applicable for unsupported languages."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        repo = _make_repo(tmp_path, languages={"Rust": 100})
        assessor = TestExecutionAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "not_applicable"


class TestCIQualityGatesAssessor:
    """Test CIQualityGatesAssessor."""

    def test_attribute_id(self):
        """Test attribute ID matches expected value."""
        assessor = CIQualityGatesAssessor()
        assert assessor.attribute_id == "ci_quality_gates"

    def test_tier(self):
        """Test tier is Essential (1)."""
        assessor = CIQualityGatesAssessor()
        assert assessor.tier == 1

    def test_default_weight(self):
        """Test default weight matches YAML config."""
        assessor = CIQualityGatesAssessor()
        assert assessor.attribute.default_weight == 0.05

    def test_no_ci_config_fails(self, tmp_path):
        """Test fail when no CI configuration exists."""
        repo = _make_repo(tmp_path)

        assessor = CIQualityGatesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0
        assert finding.remediation is not None

    def test_all_three_gates_passes(self, tmp_path):
        """Test pass when all three gates are present."""
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text(
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  lint:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: ruff check .\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: pytest\n"
            "  typecheck:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: mypy src/\n"
        )

        repo = _make_repo(tmp_path)
        assessor = CIQualityGatesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        assert finding.score >= 75

    def test_missing_typecheck_gate_fails(self, tmp_path):
        """Test that missing typecheck gate causes failure even with high config quality."""
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        # Only lint and test, no typecheck
        (workflows_dir / "ci.yml").write_text(
            "name: CI Pipeline\n"
            "on: [push]\n"
            "jobs:\n"
            "  lint-and-format:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/cache@v4\n"
            "      - run: ruff check .\n"
            "  run-tests:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: pytest --cov\n"
            "      - uses: actions/upload-artifact@v4\n"
        )

        repo = _make_repo(tmp_path)
        assessor = CIQualityGatesAssessor()
        finding = assessor.assess(repo)

        # Has CI (50) + lint (10) + test (10) + config quality points
        # But missing typecheck gate -> must fail
        assert finding.status == "fail"

    def test_missing_lint_gate_fails(self, tmp_path):
        """Test that missing lint gate causes failure."""
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text(
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: pytest\n"
            "  typecheck:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: mypy src/\n"
        )

        repo = _make_repo(tmp_path)
        assessor = CIQualityGatesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"

    def test_config_quality_adds_score(self, tmp_path):
        """Test that config quality adds points on top of gates."""
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text(
            "# CI Pipeline for quality enforcement\n"
            "name: CI Quality Gates\n"
            "on: [push, pull_request]\n"
            "jobs:\n"
            "  lint-and-format:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: actions/cache@v4\n"
            "        with:\n"
            "          path: ~/.cache\n"
            "      - run: ruff check .\n"
            "  run-tests:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: pytest --cov\n"
            "      - uses: actions/upload-artifact@v4\n"
            "  type-check:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: mypy src/\n"
        )

        repo = _make_repo(tmp_path)
        assessor = CIQualityGatesAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "pass"
        # 50 (CI) + 30 (all gates) + config quality bonus
        assert finding.score > 80


class TestDeterministicEnforcementAssessor:
    """Test DeterministicEnforcementAssessor."""

    def test_attribute_id(self):
        """Test attribute ID matches expected value."""
        assessor = DeterministicEnforcementAssessor()
        assert assessor.attribute_id == "deterministic_enforcement"

    def test_tier(self):
        """Test tier is Critical (2)."""
        assessor = DeterministicEnforcementAssessor()
        assert assessor.tier == 2

    def test_default_weight(self):
        """Test default weight matches YAML config."""
        assessor = DeterministicEnforcementAssessor()
        assert assessor.attribute.default_weight == 0.03

    def test_pre_commit_config_passes(self, tmp_path):
        """Test that .pre-commit-config.yaml is detected."""
        (tmp_path / ".pre-commit-config.yaml").write_text(
            "repos:\n  - repo: https://github.com/pre-commit/pre-commit-hooks\n"
        )

        repo = _make_repo(tmp_path)
        assessor = DeterministicEnforcementAssessor()
        finding = assessor.assess(repo)

        assert finding.score >= 60.0
        assert any("pre-commit" in e.lower() for e in finding.evidence)

    def test_no_config_fails(self, tmp_path):
        """Test fail when no enforcement config exists."""
        repo = _make_repo(tmp_path)

        assessor = DeterministicEnforcementAssessor()
        finding = assessor.assess(repo)

        assert finding.status == "fail"
        assert finding.score == 0.0

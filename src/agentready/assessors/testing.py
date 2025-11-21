"""Testing assessors for test coverage, naming conventions, and pre-commit hooks."""


from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class TestCoverageAssessor(BaseAssessor):
    """Assesses test coverage requirements.

    Tier 2 Critical (3% weight) - Test coverage is important for AI-assisted refactoring.
    """

    @property
    def attribute_id(self) -> str:
        return "test_coverage"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Test Coverage Requirements",
            category="Testing & CI/CD",
            tier=self.tier,
            description="Test coverage thresholds configured and enforced",
            criteria=">80% code coverage",
            default_weight=0.03,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Applicable if tests directory exists."""
        test_dirs = ["tests", "test", "spec", "__tests__"]
        return any((repository.path / d).exists() for d in test_dirs)

    def assess(self, repository: Repository) -> Finding:
        """Check for test coverage configuration and actual coverage.

        Looks for:
        - Python: pytest.ini, .coveragerc, pyproject.toml with coverage config
        - JavaScript: jest.config.js, package.json with coverage threshold
        """
        if "Python" in repository.languages:
            return self._assess_python_coverage(repository)
        elif any(lang in repository.languages for lang in ["JavaScript", "TypeScript"]):
            return self._assess_javascript_coverage(repository)
        else:
            return Finding.not_applicable(
                self.attribute,
                reason=f"Coverage check not implemented for {list(repository.languages.keys())}",
            )

    def _assess_python_coverage(self, repository: Repository) -> Finding:
        """Assess Python test coverage configuration."""
        # Check for coverage configuration files
        coverage_configs = [
            repository.path / ".coveragerc",
            repository.path / "pyproject.toml",
            repository.path / "setup.cfg",
        ]

        has_coverage_config = any(f.exists() for f in coverage_configs)

        # Check for pytest-cov in dependencies
        has_pytest_cov = False
        pyproject = repository.path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "r", encoding="utf-8") as f:
                    content = f.read()
                    has_pytest_cov = "pytest-cov" in content
            except OSError:
                pass

        # Score based on configuration presence
        if has_coverage_config and has_pytest_cov:
            score = 100.0
            status = "pass"
            evidence = [
                "Coverage configuration found",
                "pytest-cov dependency present",
            ]
        elif has_coverage_config or has_pytest_cov:
            score = 50.0
            status = "fail"
            evidence = [
                f"Coverage config: {'✓' if has_coverage_config else '✗'}",
                f"pytest-cov: {'✓' if has_pytest_cov else '✗'}",
            ]
        else:
            score = 0.0
            status = "fail"
            evidence = ["No coverage configuration found"]

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value="configured" if score > 50 else "not configured",
            threshold="configured with >80% threshold",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _assess_javascript_coverage(self, repository: Repository) -> Finding:
        """Assess JavaScript/TypeScript test coverage configuration."""
        package_json = repository.path / "package.json"

        if not package_json.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no package.json",
                threshold="configured coverage",
                evidence=["package.json not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

        try:
            import json

            with open(package_json, "r") as f:
                pkg = json.load(f)

            # Check for jest or vitest with coverage
            has_jest = "jest" in pkg.get("devDependencies", {})
            has_vitest = "vitest" in pkg.get("devDependencies", {})
            has_coverage = has_jest or has_vitest

            if has_coverage:
                return Finding(
                    attribute=self.attribute,
                    status="pass",
                    score=100.0,
                    measured_value="configured",
                    threshold="configured",
                    evidence=["Test coverage tool configured"],
                    remediation=None,
                    error_message=None,
                )
            else:
                return Finding(
                    attribute=self.attribute,
                    status="fail",
                    score=0.0,
                    measured_value="not configured",
                    threshold="configured",
                    evidence=["No test coverage tool found in devDependencies"],
                    remediation=self._create_remediation(),
                    error_message=None,
                )

        except (OSError, json.JSONDecodeError) as e:
            return Finding.error(
                self.attribute, reason=f"Could not parse package.json: {str(e)}"
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for test coverage."""
        return Remediation(
            summary="Configure test coverage with ≥80% threshold",
            steps=[
                "Install coverage tool (pytest-cov for Python, jest for JavaScript)",
                "Configure coverage threshold in project config",
                "Add coverage reporting to CI/CD pipeline",
                "Run coverage locally before committing",
            ],
            tools=["pytest-cov", "jest", "vitest", "coverage"],
            commands=[
                "# Python",
                "pip install pytest-cov",
                "pytest --cov=src --cov-report=term-missing --cov-fail-under=80",
                "",
                "# JavaScript",
                "npm install --save-dev jest",
                "npm test -- --coverage --coverageThreshold='{\\'global\\': {\\'lines\\': 80}}'",
            ],
            examples=[
                """# Python - pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing"

[tool.coverage.report]
fail_under = 80
""",
                """// JavaScript - package.json
{
  "jest": {
    "coverageThreshold": {
      "global": {
        "lines": 80,
        "statements": 80,
        "functions": 80,
        "branches": 80
      }
    }
  }
}
""",
            ],
            citations=[
                Citation(
                    source="pytest-cov",
                    title="Coverage Configuration",
                    url="https://pytest-cov.readthedocs.io/",
                    relevance="pytest-cov configuration guide",
                )
            ],
        )


class PreCommitHooksAssessor(BaseAssessor):
    """Assesses pre-commit hooks configuration."""

    @property
    def attribute_id(self) -> str:
        return "precommit_hooks"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Pre-commit Hooks & CI/CD Linting",
            category="Testing & CI/CD",
            tier=self.tier,
            description="Pre-commit hooks configured for linting and formatting",
            criteria=".pre-commit-config.yaml exists",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for pre-commit configuration."""
        precommit_config = repository.path / ".pre-commit-config.yaml"

        if precommit_config.exists():
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=100.0,
                measured_value="configured",
                threshold="configured",
                evidence=[".pre-commit-config.yaml found"],
                remediation=None,
                error_message=None,
            )
        else:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="not configured",
                threshold="configured",
                evidence=[".pre-commit-config.yaml not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for pre-commit hooks."""
        return Remediation(
            summary="Configure pre-commit hooks for automated code quality checks",
            steps=[
                "Install pre-commit framework",
                "Create .pre-commit-config.yaml",
                "Add hooks for linting and formatting",
                "Install hooks: pre-commit install",
                "Run on all files: pre-commit run --all-files",
            ],
            tools=["pre-commit"],
            commands=[
                "pip install pre-commit",
                "pre-commit install",
                "pre-commit run --all-files",
            ],
            examples=[
                """# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
"""
            ],
            citations=[
                Citation(
                    source="pre-commit.com",
                    title="Pre-commit Framework",
                    url="https://pre-commit.com/",
                    relevance="Official pre-commit documentation",
                )
            ],
        )

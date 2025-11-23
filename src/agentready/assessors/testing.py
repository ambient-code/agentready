"""Testing assessors for test coverage, naming conventions, and pre-commit hooks."""

import re
from pathlib import Path

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


class CICDPipelineVisibilityAssessor(BaseAssessor):
    """Assesses CI/CD pipeline configuration visibility and quality.

    Tier 3 Important (1.5% weight) - Clear CI/CD configs enable AI to understand
    build/test/deploy processes and suggest improvements.
    """

    @property
    def attribute_id(self) -> str:
        return "cicd_pipeline_visibility"

    @property
    def tier(self) -> int:
        return 3  # Important

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="CI/CD Pipeline Visibility",
            category="Testing & CI/CD",
            tier=self.tier,
            description="Clear, well-documented CI/CD configuration files",
            criteria="CI config with descriptive names, caching, parallelization",
            default_weight=0.015,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for CI/CD configuration and assess quality.

        Scoring:
        - CI config exists (50%)
        - Config quality (30%): descriptive names, caching, parallelization
        - Best practices (20%): comments, artifacts
        """
        # Check for CI config files
        ci_configs = self._detect_ci_configs(repository)

        if not ci_configs:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no CI config",
                threshold="CI config present",
                evidence=[
                    "No CI/CD configuration found",
                    "Checked: GitHub Actions, GitLab CI, CircleCI, Travis CI",
                ],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Score: CI exists (50%)
        score = 50
        evidence = [
            f"CI config found: {', '.join(str(c.relative_to(repository.path)) for c in ci_configs)}"
        ]

        # Analyze first CI config for quality
        primary_config = ci_configs[0]
        quality_score, quality_evidence = self._assess_config_quality(primary_config)
        score += quality_score
        evidence.extend(quality_evidence)

        status = "pass" if score >= 75 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=(
                "configured with best practices" if score >= 75 else "basic config"
            ),
            threshold="CI with best practices",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _detect_ci_configs(self, repository: Repository) -> list:
        """Detect CI/CD configuration files."""
        ci_config_checks = [
            repository.path / ".github" / "workflows",  # GitHub Actions (directory)
            repository.path / ".gitlab-ci.yml",  # GitLab CI
            repository.path / ".circleci" / "config.yml",  # CircleCI
            repository.path / ".travis.yml",  # Travis CI
            repository.path / "Jenkinsfile",  # Jenkins
        ]

        configs = []
        for config_path in ci_config_checks:
            if config_path.exists():
                if config_path.is_dir():
                    # GitHub Actions: check for workflow files
                    workflow_files = list(config_path.glob("*.yml")) + list(
                        config_path.glob("*.yaml")
                    )
                    if workflow_files:
                        configs.extend(workflow_files)
                else:
                    configs.append(config_path)

        return configs

    def _assess_config_quality(self, config_file: Path) -> tuple:
        """Assess quality of CI config file.

        Returns:
            Tuple of (quality_score, evidence_list)
            quality_score: 0-50 (30 for quality checks + 20 for best practices)
        """
        try:
            content = config_file.read_text()
        except OSError:
            return (0, ["Could not read CI config file"])

        quality_score = 0
        evidence = []

        # Quality checks (30 points total)
        # Descriptive job/step names (10 points)
        if self._has_descriptive_names(content):
            quality_score += 10
            evidence.append("Descriptive job/step names found")
        else:
            evidence.append("Generic job names (consider more descriptive names)")

        # Caching configured (10 points)
        if self._has_caching(content):
            quality_score += 10
            evidence.append("Caching configured")
        else:
            evidence.append("No caching detected")

        # Parallelization (10 points)
        if self._has_parallelization(content):
            quality_score += 10
            evidence.append("Parallel job execution detected")
        else:
            evidence.append("No parallelization detected")

        # Best practices (20 points total)
        # Comments in config (10 points)
        if self._has_comments(content):
            quality_score += 10
            evidence.append("Config includes comments")

        # Artifact uploading (10 points)
        if self._has_artifacts(content):
            quality_score += 10
            evidence.append("Artifacts uploaded")

        return (quality_score, evidence)

    def _has_descriptive_names(self, content: str) -> bool:
        """Check for descriptive job/step names (not just 'build', 'test')."""
        # Look for name fields with descriptive text (>2 words or specific actions)
        descriptive_patterns = [
            r'name:\s*["\']?[A-Z][^"\'\n]{20,}',  # Long descriptive names
            r'name:\s*["\']?(?:Run|Build|Deploy|Install|Lint|Format|Check)\s+\w+',  # Action + context
        ]

        return any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in descriptive_patterns
        )

    def _has_caching(self, content: str) -> bool:
        """Check for caching configuration."""
        cache_patterns = [
            r'cache:\s*["\']?(pip|npm|yarn|maven|gradle)',  # GitLab/CircleCI style
            r"actions/cache@",  # GitHub Actions cache action
            r"with:\s*\n\s*cache:",  # GitHub Actions setup with cache
        ]

        return any(
            re.search(pattern, content, re.IGNORECASE) for pattern in cache_patterns
        )

    def _has_parallelization(self, content: str) -> bool:
        """Check for parallel job execution."""
        parallel_patterns = [
            r"jobs:\s*\n\s+\w+:\s*\n.*\n\s+\w+:",  # Multiple jobs defined
            r"matrix:",  # Matrix strategy
            r"parallel:\s*\d+",  # Explicit parallelization
        ]

        return any(
            re.search(pattern, content, re.DOTALL) for pattern in parallel_patterns
        )

    def _has_comments(self, content: str) -> bool:
        """Check for explanatory comments in config."""
        # Look for YAML comments
        comment_lines = [
            line for line in content.split("\n") if line.strip().startswith("#")
        ]
        # Filter out just shebang or empty comments
        meaningful_comments = [c for c in comment_lines if len(c.strip()) > 2]

        return len(meaningful_comments) >= 3  # At least 3 meaningful comments

    def _has_artifacts(self, content: str) -> bool:
        """Check for artifact uploading."""
        artifact_patterns = [
            r"actions/upload-artifact@",  # GitHub Actions
            r"artifacts:",  # GitLab CI
            r"store_artifacts:",  # CircleCI
        ]

        return any(re.search(pattern, content) for pattern in artifact_patterns)

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for CI/CD visibility."""
        return Remediation(
            summary="Add or improve CI/CD pipeline configuration",
            steps=[
                "Create CI config for your platform (GitHub Actions, GitLab CI, etc.)",
                "Define jobs: lint, test, build",
                "Use descriptive job and step names",
                "Configure dependency caching",
                "Enable parallel job execution",
                "Upload artifacts: test results, coverage reports",
                "Add status badge to README",
            ],
            tools=["github-actions", "gitlab-ci", "circleci"],
            commands=[
                "# Create GitHub Actions workflow",
                "mkdir -p .github/workflows",
                "touch .github/workflows/ci.yml",
                "",
                "# Validate workflow",
                "gh workflow view ci.yml",
            ],
            examples=[
                """# .github/workflows/ci.yml - Good example

name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'  # Caching

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run linters
        run: |
          black --check .
          isort --check .
          ruff check .

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests with coverage
        run: pytest --cov --cov-report=xml

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: [lint, test]  # Runs after lint/test pass
    steps:
      - uses: actions/checkout@v4

      - name: Build package
        run: python -m build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
""",
            ],
            citations=[
                Citation(
                    source="GitHub",
                    title="GitHub Actions Documentation",
                    url="https://docs.github.com/en/actions",
                    relevance="Official GitHub Actions guide",
                ),
                Citation(
                    source="CircleCI",
                    title="CI/CD Best Practices",
                    url="https://circleci.com/blog/ci-cd-best-practices/",
                    relevance="Industry best practices for CI/CD",
                ),
            ],
        )


class BranchProtectionAssessor(BaseAssessor):
    """Assesses branch protection rules on main/production branches.

    Tier 4 Advanced (0.5% weight) - Requires GitHub API access to check
    branch protection settings. This is a stub implementation that will
    return not_applicable until GitHub API integration is implemented.
    """

    @property
    def attribute_id(self) -> str:
        return "branch_protection"

    @property
    def tier(self) -> int:
        return 4  # Advanced

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Branch Protection Rules",
            category="Git & Version Control",
            tier=self.tier,
            description="Required status checks and review approvals before merging",
            criteria="Branch protection enabled with status checks and required reviews",
            default_weight=0.005,
        )

    def assess(self, repository: Repository) -> Finding:
        """Stub implementation - requires GitHub API integration."""
        return Finding.not_applicable(
            self.attribute,
            reason="Requires GitHub API integration for branch protection checks. "
            "Future implementation will verify: required status checks, "
            "required reviews, force push prevention, and branch update requirements.",
        )

"""Testing assessors for test coverage, naming conventions, and pre-commit hooks."""

import re
from pathlib import Path

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class TestExecutionAssessor(BaseAssessor):
    """Assesses test execution capability and coverage.

    Tier 1 Essential (10% weight) - Anthropic identifies test execution as
    "the single highest-leverage thing you can do" for AI agent effectiveness.
    Agents succeed through tight feedback loops: change code, run tests, iterate.
    """

    @property
    def attribute_id(self) -> str:
        return "test_execution"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Test Execution & Coverage",
            category="Testing & CI/CD",
            tier=self.tier,
            description="Single-command test runner with adequate coverage configuration",
            criteria="Runnable tests with coverage config",
            default_weight=0.10,
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
        """Assess Python test execution and coverage configuration.

        Scoring (additive, 100 max):
        - Test files exist (tests/test_*.py or test/*.py):  40 pts
        - Runnable test command configured:                  20 pts
        - Coverage config (.coveragerc, pyproject.toml):     20 pts
        - Coverage enforcement (pytest-cov, fail_under):     20 pts
        """
        score = 0.0
        evidence = []

        # Signal 1: Test files exist (40 pts)
        has_test_files = self._has_python_test_files(repository)
        if has_test_files:
            score += 40.0
            evidence.append("Python test files found")
        else:
            evidence.append("No Python test files found (test_*.py / *_test.py)")

        # Signal 2: Runnable test command configured (20 pts)
        has_runner = self._has_python_test_runner(repository)
        if has_runner:
            score += 20.0
            evidence.append("Test runner configured (pytest/tox)")
        else:
            evidence.append("No test runner configuration found")

        # Signal 3: Coverage config (20 pts)
        coverage_configs = [
            repository.path / ".coveragerc",
            repository.path / "setup.cfg",
        ]
        has_coverage_config = any(f.exists() for f in coverage_configs)

        # Also check pyproject.toml for coverage sections
        pyproject = repository.path / "pyproject.toml"
        pyproject_content = ""
        if pyproject.exists():
            try:
                with open(pyproject, "r", encoding="utf-8") as f:
                    pyproject_content = f.read()
                if "[tool.coverage" in pyproject_content:
                    has_coverage_config = True
            except (OSError, UnicodeDecodeError):
                pass

        if has_coverage_config:
            score += 20.0
            evidence.append("Coverage configuration found")

        # Signal 4: Coverage enforcement (20 pts)
        has_enforcement = False
        if "pytest-cov" in pyproject_content:
            has_enforcement = True
        if "fail_under" in pyproject_content:
            has_enforcement = True
        # Check .coveragerc for fail_under
        coveragerc = repository.path / ".coveragerc"
        if coveragerc.exists():
            try:
                with open(coveragerc, "r", encoding="utf-8") as f:
                    if "fail_under" in f.read():
                        has_enforcement = True
            except (OSError, UnicodeDecodeError):
                pass

        if has_enforcement:
            score += 20.0
            evidence.append("Coverage enforcement configured (pytest-cov/fail_under)")

        score = min(score, 100.0)
        status = "pass" if score > 50 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value="configured" if score > 50 else "not configured",
            threshold="runnable tests with coverage config",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _has_python_test_files(self, repository: Repository) -> bool:
        """Check if Python test files exist."""
        test_dirs = ["tests", "test"]
        for d in test_dirs:
            test_dir = repository.path / d
            if test_dir.exists():
                # Look for test_*.py or *_test.py files
                test_files = list(test_dir.rglob("test_*.py")) + list(
                    test_dir.rglob("*_test.py")
                )
                if test_files:
                    return True
        return False

    def _has_python_test_runner(self, repository: Repository) -> bool:
        """Check if a test runner is configured."""
        # pytest.ini or tox.ini
        if (repository.path / "pytest.ini").exists():
            return True
        if (repository.path / "tox.ini").exists():
            return True

        # pyproject.toml with pytest config
        pyproject = repository.path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "r", encoding="utf-8") as f:
                    content = f.read()
                if "[tool.pytest" in content:
                    return True
            except (OSError, UnicodeDecodeError):
                pass

        return False

    def _assess_javascript_coverage(self, repository: Repository) -> Finding:
        """Assess JavaScript/TypeScript test execution and coverage.

        Scoring (additive, 100 max):
        - scripts.test entry in package.json:                40 pts
        - Test files exist (*.test.js, *.spec.js, etc.):     20 pts
        - jest/vitest in devDependencies:                     20 pts
        - Coverage threshold configured:                     20 pts
        """
        package_json = repository.path / "package.json"

        if not package_json.exists():
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no package.json",
                threshold="runnable tests with coverage config",
                evidence=["package.json not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

        try:
            import json

            with open(package_json, "r") as f:
                pkg = json.load(f)

            score = 0.0
            evidence = []

            # Signal 1: scripts.test exists (40 pts)
            scripts = pkg.get("scripts", {})
            has_test_script = bool(scripts.get("test"))
            if has_test_script:
                score += 40.0
                evidence.append("scripts.test entry found in package.json")
            else:
                evidence.append("No scripts.test entry in package.json")

            # Signal 2: Test files exist (20 pts)
            has_test_files = self._has_js_test_files(repository)
            if has_test_files:
                score += 20.0
                evidence.append("Test files found (*.test.* / *.spec.* / __tests__/)")
            else:
                evidence.append("No test files found")

            # Signal 3: jest/vitest in devDependencies (20 pts)
            dev_deps = pkg.get("devDependencies", {})
            has_jest = "jest" in dev_deps
            has_vitest = "vitest" in dev_deps
            if has_jest or has_vitest:
                tool = "jest" if has_jest else "vitest"
                score += 20.0
                evidence.append(f"{tool} found in devDependencies")
            else:
                evidence.append("No test framework in devDependencies")

            # Signal 4: Coverage threshold configured (20 pts)
            has_threshold = self._has_js_coverage_threshold(repository, pkg)
            if has_threshold:
                score += 20.0
                evidence.append("Coverage threshold configured")

            score = min(score, 100.0)
            status = "pass" if score > 50 else "fail"

            return Finding(
                attribute=self.attribute,
                status=status,
                score=score,
                measured_value="configured" if score > 50 else "not configured",
                threshold="runnable tests with coverage config",
                evidence=evidence,
                remediation=self._create_remediation() if status == "fail" else None,
                error_message=None,
            )

        except (OSError, json.JSONDecodeError) as e:
            return Finding.error(
                self.attribute, reason=f"Could not parse package.json: {str(e)}"
            )

    def _has_js_test_files(self, repository: Repository) -> bool:
        """Check if JavaScript/TypeScript test files exist."""
        # Check for __tests__ directory
        if (repository.path / "__tests__").exists():
            return True
        # Check for *.test.* or *.spec.* files in src/ or root
        for pattern in ["**/*.test.*", "**/*.spec.*"]:
            if list(repository.path.glob(pattern)):
                return True
        return False

    def _has_js_coverage_threshold(self, repository: Repository, pkg: dict) -> bool:
        """Check if JS coverage threshold is configured."""
        # Check package.json jest.coverageThreshold
        jest_config = pkg.get("jest", {})
        if isinstance(jest_config, dict) and jest_config.get("coverageThreshold"):
            return True

        # Check for jest.config.* or vitest.config.* with coverage
        config_files = [
            "jest.config.js",
            "jest.config.ts",
            "vitest.config.js",
            "vitest.config.ts",
        ]
        for config_name in config_files:
            config_file = repository.path / config_name
            if config_file.exists():
                try:
                    content = config_file.read_text(encoding="utf-8")
                    if "coverageThreshold" in content or "coverage" in content:
                        return True
                except (OSError, UnicodeDecodeError):
                    pass

        return False

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


class DeterministicEnforcementAssessor(BaseAssessor):
    """Assesses deterministic enforcement via hooks and lint rules.

    Tier 2 Critical (3% weight) - Context file instructions are advisory;
    hooks are deterministic. Factory.ai: "Agents write the code; linters write the law."
    """

    @property
    def attribute_id(self) -> str:
        return "deterministic_enforcement"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Deterministic Enforcement (Hooks & Lint Rules)",
            category="Testing & CI/CD",
            tier=self.tier,
            description="Hooks and lint rules for deterministic quality enforcement",
            criteria="Pre-commit or agent hooks configured",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for deterministic enforcement mechanisms."""
        precommit_config = repository.path / ".pre-commit-config.yaml"
        claude_settings = repository.path / ".claude" / "settings.json"
        husky_dir = repository.path / ".husky"

        evidence = []
        score = 0.0

        if precommit_config.exists():
            score += 60.0
            evidence.append(".pre-commit-config.yaml found (pre-commit hooks)")

        if claude_settings.exists():
            try:
                import json

                content = json.loads(claude_settings.read_text())
                if "hooks" in content:
                    score += 30.0
                    evidence.append(
                        ".claude/settings.json has hooks configured (agent hooks)"
                    )
                else:
                    score += 10.0
                    evidence.append(".claude/settings.json exists but no hooks defined")
            except (json.JSONDecodeError, OSError):
                score += 10.0
                evidence.append(".claude/settings.json exists")

        if husky_dir.exists():
            score += 10.0
            evidence.append(".husky directory found (git hooks)")

        score = min(score, 100.0)

        if score >= 60:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=score,
                measured_value="configured",
                threshold="configured",
                evidence=evidence,
                remediation=None,
                error_message=None,
            )
        elif score > 0:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=score,
                measured_value="partially configured",
                threshold="configured",
                evidence=evidence,
                remediation=self._create_remediation(),
                error_message=None,
            )
        else:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="not configured",
                threshold="configured",
                evidence=["No deterministic enforcement found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for deterministic enforcement."""
        return Remediation(
            summary="Set up deterministic enforcement with hooks and lint rules",
            steps=[
                "Start with 2 hooks: auto-format on edit + block destructive operations",
                "Install pre-commit framework for git hooks",
                "Configure .claude/settings.json with agent hooks for team-wide sharing",
                "Add lint rules for import restrictions and architectural boundaries",
            ],
            tools=["pre-commit"],
            commands=[
                "pip install pre-commit",
                "pre-commit install",
                "mkdir -p .claude",
            ],
            examples=[
                """# .claude/settings.json - Agent hooks
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "npx prettier --write $CLAUDE_FILE_PATH 2>/dev/null || true"
      }
    ]
  }
}""",
            ],
            citations=[
                Citation(
                    source="Red Hat",
                    title="Repository Scaffolding for AI Coding Agents, Section 2.2",
                    url="",
                    relevance="Recommended starter hooks for AI agent enforcement",
                ),
                Citation(
                    source="Factory.ai",
                    title="Using Linters to Direct Agents",
                    url="https://factory.ai/news/using-linters-to-direct-agents",
                    relevance="Agents write the code; linters write the law",
                ),
            ],
        )


class CIQualityGatesAssessor(BaseAssessor):
    """Assesses CI quality gates — lint, type-check, and tests on every PR.

    Tier 1 Essential (5% weight) - Quality gates provide definitive pass/fail
    signals for agent-generated code and enable self-correction.
    """

    @property
    def attribute_id(self) -> str:
        return "ci_quality_gates"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="CI Quality Gates",
            category="Testing & CI/CD",
            tier=self.tier,
            description="CI runs lint, type-check, and tests on every PR",
            criteria="CI gates with lint + type-check + tests",
            default_weight=0.05,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for CI/CD configuration and assess quality.

        Scoring:
        - CI config exists (50 pts)
        - Quality gates — lint + test + typecheck (30 pts)
        - Config quality (15 pts): descriptive names, caching, parallelization
        - Best practices (5 pts): comments, artifacts
        """
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

        score = 50
        evidence = [
            f"CI config found: {', '.join(str(c.relative_to(repository.path)) for c in ci_configs)}"
        ]

        # Check quality gates across ALL configs (30 pts)
        gate_score, gate_evidence = self._assess_quality_gates(ci_configs)
        score += gate_score
        evidence.extend(gate_evidence)

        # Check config quality across all configs — take best score (15 pts)
        best_quality = 0
        best_quality_evidence = []
        for config in ci_configs:
            q_score, q_evidence = self._assess_config_quality(config)
            if q_score > best_quality:
                best_quality = q_score
                best_quality_evidence = q_evidence
        score += best_quality
        evidence.extend(best_quality_evidence)

        # All three gates (lint, test, typecheck) are required for pass
        has_all_gates = gate_score == 30
        status = "pass" if has_all_gates and score >= 75 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=(
                "configured with quality gates"
                if has_all_gates
                else "missing quality gates"
            ),
            threshold="CI with lint + test + type-check gates",
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

    def _assess_quality_gates(self, ci_configs: list) -> tuple:
        """Check whether lint, test, and type-check gates exist across CI configs.

        Returns:
            Tuple of (gate_score, evidence_list)
            gate_score: 0-30
        """
        lint_patterns = [
            r"(?:eslint|ruff|pylint|flake8|rubocop|golangci-lint|black|isort|prettier|stylelint)\b",
            r"\blint\b",
            r"\bformatting?\b",
        ]
        test_patterns = [
            r"\bpytest\b",
            r"\bjest\b",
            r"\bvitest\b",
            r"\bmocha\b",
            r"\bnpm\s+test\b",
            r"\byarn\s+test\b",
            r"\bgo\s+test\b",
            r"\bcargo\s+test\b",
            r"\brspec\b",
        ]
        typecheck_patterns = [
            r"\bmypy\b",
            r"\bpyright\b",
            r"\btsc\b",
            r"\btype[_-]?check\b",
        ]

        found_lint = False
        found_test = False
        found_typecheck = False

        for config in ci_configs:
            try:
                content = config.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            if not found_lint and any(
                re.search(p, content, re.IGNORECASE) for p in lint_patterns
            ):
                found_lint = True
            if not found_test and any(
                re.search(p, content, re.IGNORECASE) for p in test_patterns
            ):
                found_test = True
            if not found_typecheck and any(
                re.search(p, content, re.IGNORECASE) for p in typecheck_patterns
            ):
                found_typecheck = True

        gate_score = 0
        evidence = []

        if found_lint:
            gate_score += 10
            evidence.append("Lint gate detected in CI")
        else:
            evidence.append("No lint gate found in CI")

        if found_test:
            gate_score += 10
            evidence.append("Test gate detected in CI")
        else:
            evidence.append("No test gate found in CI")

        if found_typecheck:
            gate_score += 10
            evidence.append("Type-check gate detected in CI")
        else:
            evidence.append("No type-check gate found in CI")

        return (gate_score, evidence)

    def _assess_config_quality(self, config_file: Path) -> tuple:
        """Assess quality of CI config file.

        Returns:
            Tuple of (quality_score, evidence_list)
            quality_score: 0-20 (15 for quality checks + 5 for best practices)
        """
        try:
            content = config_file.read_text()
        except OSError:
            return (0, ["Could not read CI config file"])

        quality_score = 0
        evidence = []

        # Quality checks (15 points total)
        if self._has_descriptive_names(content):
            quality_score += 5
            evidence.append("Descriptive job/step names found")

        if self._has_caching(content):
            quality_score += 5
            evidence.append("Caching configured")

        if self._has_parallelization(content):
            quality_score += 5
            evidence.append("Parallel job execution detected")

        # Best practices (5 points total)
        if self._has_comments(content):
            quality_score += 3
            evidence.append("Config includes comments")

        if self._has_artifacts(content):
            quality_score += 2
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


# Backward-compatible aliases for renamed assessors
TestCoverageAssessor = TestExecutionAssessor
PreCommitHooksAssessor = DeterministicEnforcementAssessor
CICDPipelineVisibilityAssessor = CIQualityGatesAssessor

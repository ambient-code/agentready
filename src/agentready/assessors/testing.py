"""Testing assessors for test coverage, naming conventions, and pre-commit hooks."""

import re
from pathlib import Path

import yaml

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
        """Applicable if tests directory or test config exists."""
        test_dirs = ["tests", "test", "spec", "__tests__"]
        if any((repository.path / d).exists() for d in test_dirs):
            return True
        if self._has_python_test_runner(repository):
            return True
        if (repository.path / "package.json").exists():
            return True
        if self._has_go_test_files(repository):
            return True
        return False

    def assess(self, repository: Repository) -> Finding:
        """Check for test coverage configuration and actual coverage.

        Dispatches based on the primary programming language (by file count)
        to handle multi-language repos correctly.
        """
        primary = self._primary_language(
            repository, {"Python", "JavaScript", "TypeScript", "Go"}
        )
        if primary == "Python":
            return self._assess_python_coverage(repository)
        elif primary in ("JavaScript", "TypeScript"):
            return self._assess_javascript_coverage(repository)
        elif primary == "Go":
            return self._assess_go_coverage(repository)
        else:
            return Finding.not_applicable(
                self.attribute,
                reason=f"Coverage check not implemented for {list(repository.languages.keys())}",
            )

    def _assess_python_coverage(self, repository: Repository) -> Finding:
        """Assess Python test execution and coverage configuration.

        Scoring (additive, capped at 100):
        - Test files exist (tests/test_*.py or test/*.py):  40 pts
        - Runnable test command configured:                  20 pts
        - Coverage config (.coveragerc, pyproject.toml):     20 pts
        - Coverage enforcement (pytest-cov, fail_under):     20 pts
        - Test command documented in context files:          10 pts (bonus)
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

        # Signal 5: Test command documented in context files (10 pts)
        python_patterns = [
            "pytest",
            "python -m pytest",
            "tox",
            "make test",
            "nox",
            "pytest -k",
            "pytest path/",
            "pytest tests/",
        ]
        doc_found, doc_evidence = self._check_test_command_documented(
            repository, python_patterns
        )
        if doc_found:
            score += 10.0
        evidence.extend(doc_evidence)

        # Substantiating evidence: test organization
        org_evidence = self._check_test_organization(repository, "Python")
        evidence.extend(org_evidence)

        score = min(score, 100.0)
        status = "pass" if has_test_files and has_runner and score > 50 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=(
                "configured"
                if has_test_files and has_runner and score > 50
                else "not configured"
            ),
            threshold="runnable tests with coverage config",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _check_test_command_documented(
        self, repository: Repository, patterns: list[str]
    ) -> tuple[bool, list[str]]:
        """Check if test commands are documented in context files.

        Scans CLAUDE.md, AGENTS.md, and README.md for test command keywords.
        Returns (found, evidence_lines).
        """
        context_files = ["CLAUDE.md", "AGENTS.md", "README.md"]
        for filename in context_files:
            filepath = repository.path / filename
            if not filepath.exists():
                continue
            try:
                content = filepath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            content_lower = content.lower()
            for pattern in patterns:
                if pattern.lower() in content_lower:
                    return True, [f"Test command documented in {filename}"]
        return False, ["Test command not documented in context files"]

    def _check_test_organization(
        self, repository: Repository, language: str
    ) -> list[str]:
        """Check for test organization signals (substantiating evidence).

        Looks for unit/integration separation patterns. Returns evidence lines.
        """
        evidence = []

        if language == "Python":
            tests_dir = repository.path / "tests"
            has_unit = (tests_dir / "unit").is_dir() if tests_dir.exists() else False
            has_integration = (
                (tests_dir / "integration").is_dir() if tests_dir.exists() else False
            )
            if has_unit or has_integration:
                parts = []
                if has_unit:
                    parts.append("unit")
                if has_integration:
                    parts.append("integration")
                evidence.append(
                    f"Test organization: separate {'/'.join(parts)} directories"
                )

            if not evidence and repository.assessment_exists("tests"):
                test_files = [
                    p
                    for p in repository.assessment_files("test_*.py")
                    if tests_dir in p.parents or p.parent == tests_dir
                ][:10]
                for tf in test_files:
                    try:
                        content = tf.read_text(encoding="utf-8")
                        if (
                            "@pytest.mark.integration" in content
                            or "@pytest.mark.slow" in content
                        ):
                            evidence.append(
                                "Test organization: pytest markers found (integration/slow)"
                            )
                            break
                    except (OSError, UnicodeDecodeError):
                        continue

            makefile = repository.path / "Makefile"
            if makefile.exists():
                try:
                    content = makefile.read_text(encoding="utf-8")
                    targets = []
                    for target in ["test-unit", "test-integration", "test-e2e"]:
                        if re.search(rf"^{target}\s*:", content, re.MULTILINE):
                            targets.append(target)
                    if targets:
                        evidence.append(
                            f"Test organization: Makefile targets ({', '.join(targets)})"
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        elif language in ("JavaScript", "TypeScript"):
            for test_root in ["__tests__", "test", "tests"]:
                test_dir = repository.path / test_root
                if not test_dir.is_dir():
                    continue
                has_unit = (test_dir / "unit").is_dir()
                has_integration = (test_dir / "integration").is_dir()
                if has_unit or has_integration:
                    parts = []
                    if has_unit:
                        parts.append("unit")
                    if has_integration:
                        parts.append("integration")
                    evidence.append(
                        f"Test organization: separate {'/'.join(parts)} directories"
                    )
                    break

            pkg_json = repository.path / "package.json"
            if pkg_json.exists():
                try:
                    import json

                    pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
                    scripts = pkg.get("scripts", {})
                    test_scripts = [
                        k
                        for k in scripts
                        if k.startswith("test:") or k.startswith("test-")
                    ]
                    if test_scripts:
                        evidence.append(
                            f"Test organization: filtered test scripts ({', '.join(test_scripts[:3])})"
                        )
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    pass

        elif language == "Go":
            test_files = repository.assessment_files("*_test.go")[:10]
            for tf in test_files:
                try:
                    content = tf.read_text(encoding="utf-8")
                    if (
                        "//go:build integration" in content
                        or "// +build integration" in content
                    ):
                        evidence.append(
                            "Test organization: Go build tags for integration tests"
                        )
                        break
                except (OSError, UnicodeDecodeError):
                    continue

            makefile = repository.path / "Makefile"
            if makefile.exists():
                try:
                    content = makefile.read_text(encoding="utf-8")
                    targets = []
                    for target in ["test-unit", "test-integration", "test-e2e"]:
                        if re.search(rf"^{target}\s*:", content, re.MULTILINE):
                            targets.append(target)
                    if targets:
                        evidence.append(
                            f"Test organization: Makefile targets ({', '.join(targets)})"
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        return evidence

    def _has_python_test_files(self, repository: Repository) -> bool:
        """Check if Python test files exist."""
        test_dirs = ["tests", "test"]
        for d in test_dirs:
            test_dir = repository.path / d
            if repository.assessment_exists(d):
                test_files = [
                    p
                    for p in repository.assessment_files("test_*.py")
                    + repository.assessment_files("*_test.py")
                    if test_dir in p.parents or p.parent == test_dir
                ]
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

        Scoring (additive, capped at 100):
        - scripts.test entry in package.json:                40 pts
        - Test files exist (*.test.js, *.spec.js, etc.):     20 pts
        - jest/vitest in devDependencies:                     20 pts
        - Coverage threshold configured:                     20 pts
        - Test command documented in context files:           10 pts (bonus)
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

            # Signal 5: Test command documented in context files (10 pts)
            js_patterns = [
                "npm test",
                "yarn test",
                "pnpm test",
                "npx jest",
                "npx vitest",
                "npm test --",
                "jest path/",
                "vitest path/",
            ]
            doc_found, doc_evidence = self._check_test_command_documented(
                repository, js_patterns
            )
            if doc_found:
                score += 10.0
            evidence.extend(doc_evidence)

            # Substantiating evidence: test organization
            primary = self._primary_language(repository, {"JavaScript", "TypeScript"})
            org_evidence = self._check_test_organization(
                repository, primary or "JavaScript"
            )
            evidence.extend(org_evidence)

            score = min(score, 100.0)
            status = "pass" if has_test_script and score > 50 else "fail"

            return Finding(
                attribute=self.attribute,
                status=status,
                score=score,
                measured_value=(
                    "configured" if has_test_script and score > 50 else "not configured"
                ),
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
        if repository.assessment_exists("__tests__"):
            return True
        return bool(repository.assessment_match_any(["*.test.*", "*.spec.*"]))

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

    def _has_go_test_files(self, repository: Repository) -> bool:
        """Check if Go test files (*_test.go) exist."""
        return bool(repository.assessment_files("*_test.go"))

    def _assess_go_coverage(self, repository: Repository) -> Finding:
        """Assess Go test execution and coverage configuration.

        Scoring (additive, capped at 100):
        - Test files exist (*_test.go):                40 pts
        - Test command found (Makefile/CI/README):     20 pts
        - Coverage configured (-coverprofile):         20 pts
        - Race detection (-race flag):                 20 pts
        - Test command documented in context files:    10 pts (bonus)
        """
        score = 0.0
        evidence = []

        has_test_files = self._has_go_test_files(repository)
        if has_test_files:
            score += 40.0
            evidence.append("Go test files found (*_test.go)")
        else:
            evidence.append("No Go test files found (*_test.go)")

        text_sources = self._read_go_build_files(repository)

        has_test_cmd = bool(
            re.search(
                r"(?:\bgo|\$\(GO\))\s+test\b|\bmake\s+test\b|\bginkgo\b",
                text_sources,
            )
        )
        if has_test_cmd:
            score += 20.0
            evidence.append("Go test command found in project files")
        else:
            evidence.append("No test command found in Makefile/CI/README/AGENTS.md")

        has_coverage = bool(
            re.search(r"(?<!\S)-cover(?:\b|profile\b|mode\b)", text_sources)
        )
        if has_coverage:
            score += 20.0
            evidence.append("Coverage configuration found")
        else:
            evidence.append("No coverage configuration found")

        has_race = bool(re.search(r"-race\b", text_sources))
        if has_race:
            score += 20.0
            evidence.append("Race detector enabled (-race flag)")
        else:
            evidence.append("Race detector not configured (-race flag)")

        # Signal 5: Test command documented in context files (10 pts)
        go_patterns = [
            "go test",
            "make test",
            "go test ./",
            "go test -run",
        ]
        doc_found, doc_evidence = self._check_test_command_documented(
            repository, go_patterns
        )
        if doc_found:
            score += 10.0
        evidence.extend(doc_evidence)

        # Substantiating evidence: test organization
        org_evidence = self._check_test_organization(repository, "Go")
        evidence.extend(org_evidence)

        score = min(score, 100.0)
        status = "pass" if has_test_files and has_test_cmd and score > 50 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=(
                "configured"
                if has_test_files and has_test_cmd and score > 50
                else "not configured"
            ),
            threshold="runnable tests with coverage config",
            evidence=evidence,
            remediation=self._create_go_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _read_go_build_files(self, repository: Repository) -> str:
        """Read Makefiles, CI configs, and README for Go test patterns.

        Checks root and subdirectory Makefiles to support Go monorepos
        where go.mod and Makefile live in subdirectories.
        """
        contents = []
        files_to_check: list[Path] = [
            repository.path / "Makefile",
            repository.path / "Taskfile.yml",
            repository.path / "README.md",
            repository.path / "AGENTS.md",
            repository.path / "CLAUDE.md",
        ]

        # Include module-local build files (Go monorepos)
        for module_root in self._find_go_module_roots(repository):
            if module_root == repository.path:
                continue
            files_to_check.extend(
                [
                    module_root / "Makefile",
                    module_root / "Taskfile.yml",
                    module_root / "README.md",
                ]
            )

        for rel in repository.assessment_match_any(
            [".github/workflows/*.yml", ".github/workflows/*.yaml"]
        ):
            files_to_check.append(repository.path / rel)
        for f in files_to_check:
            if f.exists():
                try:
                    contents.append(f.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError):
                    pass
        return "\n".join(contents)

    def _create_go_remediation(self) -> Remediation:
        """Create remediation guidance for Go test coverage."""
        return Remediation(
            summary="Configure Go test execution with coverage and race detection",
            steps=[
                "Create test files alongside source code (*_test.go)",
                "Add a Makefile target for running tests with coverage",
                "Enable race detection in CI with -race flag",
                "Configure coverage reporting in CI pipeline",
            ],
            tools=["go test"],
            commands=[
                "go test -v -race -coverprofile=coverage.txt -covermode=atomic ./...",
                "go tool cover -html=coverage.txt -o coverage.html",
            ],
            examples=[
                """# Makefile
.PHONY: test
test:
\tgo test -v -race -coverprofile=coverage.txt -covermode=atomic ./...

.PHONY: coverage
coverage: test
\tgo tool cover -html=coverage.txt -o coverage.html
""",
            ],
            citations=[
                Citation(
                    source="Go Documentation",
                    title="Testing",
                    url="https://pkg.go.dev/testing",
                    relevance="Go testing package reference",
                )
            ],
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
            tools=["pytest-cov", "jest", "vitest", "coverage", "go test"],
            commands=[
                "# Python",
                "pip install pytest-cov",
                "pytest --cov=src --cov-report=term-missing --cov-fail-under=80",
                "",
                "# JavaScript",
                "npm install --save-dev jest",
                "npm test -- --coverage --coverageThreshold='{\\'global\\': {\\'lines\\': 80}}'",
                "",
                "# Go",
                "go test -v -race -coverprofile=coverage.txt -covermode=atomic ./...",
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
            score += 40.0
            evidence.append(".pre-commit-config.yaml found (git hooks, bypassable)")

        if claude_settings.exists():
            try:
                import json

                content = json.loads(claude_settings.read_text())
                hooks = content.get("hooks")
                has_configured_hooks = isinstance(hooks, dict) and any(
                    isinstance(entries, list) and entries for entries in hooks.values()
                )
                if has_configured_hooks:
                    score += 60.0
                    evidence.append(
                        ".claude/settings.json has hooks configured (deterministic agent hooks)"
                    )
                else:
                    score += 10.0
                    evidence.append(".claude/settings.json exists but no hooks defined")
            except (json.JSONDecodeError, OSError):
                score += 10.0
                evidence.append(".claude/settings.json exists")

        if husky_dir.exists() and husky_dir.is_dir():
            valid_hook_names = {
                "applypatch-msg",
                "commit-msg",
                "post-applypatch",
                "post-checkout",
                "post-commit",
                "post-merge",
                "post-rewrite",
                "pre-applypatch",
                "pre-auto-gc",
                "pre-commit",
                "pre-merge-commit",
                "pre-push",
                "pre-rebase",
                "prepare-commit-msg",
            }
            try:
                hook_scripts = [
                    f.name
                    for f in husky_dir.iterdir()
                    if f.is_file()
                    and not f.name.startswith("_")
                    and f.name in valid_hook_names
                ]
            except OSError:
                hook_scripts = []
                evidence.append(".husky directory exists but could not be read")
            if hook_scripts:
                score += 40.0
                hooks_list = ", ".join(sorted(hook_scripts))
                evidence.append(
                    f".husky directory found with hooks: {hooks_list} (git hooks, bypassable)"
                )
            else:
                score += 10.0
                evidence.append(".husky directory found but no hook scripts")

        score = min(score, 100.0)

        if score >= 40:
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
                "Configure .claude/settings.json with agent hooks (deterministic, cannot be bypassed)",
                "Start with 2 hooks: auto-format on edit + block destructive operations",
                "Optionally add pre-commit (Python) or Husky (Node.js) for git hooks",
                "Add lint rules for import restrictions and architectural boundaries",
            ],
            tools=["pre-commit", "husky"],
            commands=[
                "pip install pre-commit && pre-commit install",
                "npx husky init",
                "mkdir -p .claude",
            ],
            examples=[
                """# .claude/settings.json - Agent hooks
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write $CLAUDE_FILE_PATH 2>/dev/null || true"
          }
        ]
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

        # Only count quality gates from PR-triggered workflows
        pr_configs = [c for c in ci_configs if self._has_pr_trigger(c)]
        has_pr_trigger = len(pr_configs) > 0

        # Check quality gates in PR-triggered configs (30 pts)
        # Fall back to all configs when none have PR triggers (for evidence)
        gate_score, gate_evidence = self._assess_quality_gates(
            pr_configs if pr_configs else ci_configs
        )
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

        if not has_pr_trigger:
            evidence.append("No CI workflow triggers on pull requests")

        # All three gates (lint, test, typecheck) are required for pass,
        # and at least one workflow must trigger on PRs
        has_all_gates = gate_score == 30
        status = "pass" if has_all_gates and has_pr_trigger and score >= 75 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=(
                "configured with quality gates"
                if has_all_gates and has_pr_trigger
                else "missing quality gates"
            ),
            threshold="CI with lint + test + type-check gates on PRs",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _detect_ci_configs(self, repository: Repository) -> list:
        """Detect CI/CD configuration files."""
        configs: list[Path] = []
        for rel in repository.assessment_match_any(
            [".github/workflows/*.yml", ".github/workflows/*.yaml"]
        ):
            configs.append(repository.path / rel)

        for rel in (
            ".gitlab-ci.yml",
            ".circleci/config.yml",
            ".travis.yml",
            "Jenkinsfile",
        ):
            if repository.assessment_exists(rel):
                configs.append(repository.path / rel)

        for rel in repository.assessment_match_any([".tekton/*.yml", ".tekton/*.yaml"]):
            configs.append(repository.path / rel)

        return configs

    def _has_pr_trigger(self, config: Path) -> bool:
        """Check if a CI config file triggers on pull requests.

        For GitHub Actions, requires explicit pull_request trigger.
        For Pipelines as Code, requires explicit pull_request event trigger.
        Other CI systems (GitLab CI, CircleCI, Travis) run on MRs by default.
        """
        if ".github" in str(config) and "workflows" in str(config):
            try:
                content = config.read_text()
                return bool(re.search(r"\bpull_request", content))
            except (OSError, UnicodeDecodeError):
                return False
        elif ".tekton" in str(config):
            # Check each pipeline definition for annotation: pipelinesascode.tekton.dev/on-event,
            # note, values could be just "pull_request" or be an array of events "[pull_request,push]"
            # Also, the matcher could be configured as CEL expression, so check for
            # pipelinesascode.tekton.dev/on-cel-expression: ... event == "pull_request" ...
            try:
                content = config.read_text()
                docs = yaml.safe_load_all(content)

                for doc in docs:
                    if not isinstance(doc, dict):
                        continue
                    annotations = doc.get("metadata", {}).get("annotations", {})

                    # Check on-event annotation
                    on_event = annotations.get(
                        "pipelinesascode.tekton.dev/on-event", ""
                    )
                    if "pull_request" in str(on_event):
                        return True

                    # Check on-cel-expression annotation value only
                    cel_expr = annotations.get(
                        "pipelinesascode.tekton.dev/on-cel-expression", ""
                    )
                    if re.search(r'event\s*==\s*["\']pull_request["\']', str(cel_expr)):
                        return True

                return False
            except (OSError, UnicodeDecodeError, yaml.YAMLError):
                return False
        return True

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
            r"\bcargo\s+clippy\b",
        ]
        test_patterns = [
            r"\bpytest\b",
            r"\bjest\b",
            r"\bvitest\b",
            r"\bmocha\b",
            r"\bnpm\s+test\b",
            r"\byarn\s+test\b",
            r"(?:\bgo|\$\(GO\))\s+test\b",
            r"\bcargo\s+test\b",
            r"\brspec\b",
            r"\bmake\s+test\b",
        ]
        typecheck_patterns = [
            r"\bmypy\b",
            r"\bpyright\b",
            r"\btsc\b",
            r"\btype[_-]?check\b",
            r"\bgo\s+vet\b",
            r"(?:\bgo|\$\(GO\))\s+build\b",
            r"\bmake\s+build\b",
            r"\bgolangci-lint\b",
            r"\bcargo\s+build\b",
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


# Backward-compatible aliases for renamed assessors
TestCoverageAssessor = TestExecutionAssessor
PreCommitHooksAssessor = DeterministicEnforcementAssessor
CICDPipelineVisibilityAssessor = CIQualityGatesAssessor

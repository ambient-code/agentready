"""Structure assessors for project layout and separation of concerns."""

import re
import tomllib

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor

# Directories that should not be considered as source directories
# Fix for #246, #305: These are common non-source directories
_NON_SOURCE_DIRS = frozenset(
    {
        "tests",
        "test",
        "docs",
        "doc",
        "documentation",
        "scripts",
        "utilities",
        "utils",
        "tools",
        "examples",
        "samples",
        "benchmarks",
        "fixtures",
        ".git",
        ".github",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
        "build",
        "dist",
        "htmlcov",
        ".eggs",
    }
)


class StandardLayoutAssessor(BaseAssessor):
    """Assesses standard project layout patterns.

    Tier 1 Essential (10% weight) - Standard layouts help AI navigate code.

    Supports multiple valid Python project structures:
    - src/ layout (PEP 517 recommended)
    - Project-named flat layout (e.g., pandas/pandas/, numpy/numpy/)
    - Test-only repositories (marked as not_applicable)

    Fix for #246: Recognize project-named source directories
    Fix for #305: Handle test-only repositories gracefully
    """

    @property
    def attribute_id(self) -> str:
        return "standard_layout"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Standard Project Layouts",
            category="Repository Structure",
            tier=self.tier,
            description="Follows standard project structure for language",
            criteria="Standard directories (src/ or project-named, tests/) present",
            default_weight=0.10,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for standard project layout directories.

        Expected patterns:
        - Python: src/ or project-named directory, plus tests/
        - JavaScript: src/, test/, docs/
        - Java: src/main/java, src/test/java

        Fix for #246, #305: Support multiple valid Python layouts
        """
        # Check for tests directory (either tests/ or test/)
        tests_path = repository.path / "tests"
        has_tests = tests_path.exists()
        if not has_tests:
            tests_path = repository.path / "test"
            has_tests = tests_path.exists()

        # Check for source directory: src/ or project-named
        # Fix for #246: Detect project-named source directories
        source_info = self._find_source_directory(repository)
        has_source = source_info["found"]
        source_type = source_info["type"]
        source_dir = source_info["directory"]

        # Fix for #305: Handle test-only repositories
        if not has_source and has_tests:
            if self._is_test_only_repository(repository):
                return Finding.not_applicable(
                    self.attribute,
                    reason="Test-only repository (no source code to organize)",
                )

        # Calculate score based on what we found
        found_dirs = (1 if has_source else 0) + (1 if has_tests else 0)
        required_dirs = 2

        score = self.calculate_proportional_score(
            measured_value=found_dirs,
            threshold=required_dirs,
            higher_is_better=True,
        )

        status = "pass" if score >= 75 else "fail"

        # Build evidence with detailed source directory info
        if has_source:
            if source_type == "src":
                source_evidence = "src/: ✓"
            else:
                source_evidence = f"source ({source_type}): ✓ ({source_dir})"
        else:
            source_evidence = "source directory: ✗ (no src/ or project-named dir)"

        evidence = [
            f"Found {found_dirs}/{required_dirs} standard directories",
            source_evidence,
            f"tests/: {'✓' if has_tests else '✗'}",
        ]

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{found_dirs}/{required_dirs} directories",
            threshold=f"{required_dirs}/{required_dirs} directories",
            evidence=evidence,
            remediation=(
                self._create_remediation(has_source, has_tests)
                if status == "fail"
                else None
            ),
            error_message=None,
        )

    def _find_source_directory(self, repository: Repository) -> dict:
        """Find the source directory using multiple strategies.

        Fix for #246: Support both src/ layout and project-named layout.

        Returns:
            dict with keys:
            - found: bool - whether a source directory was found
            - type: str - "src", "project-named", or "none"
            - directory: str - name of the source directory
        """
        # Strategy 1: Check for src/ directory (PEP 517 recommended)
        if (repository.path / "src").exists():
            return {"found": True, "type": "src", "directory": "src/"}

        # Strategy 2: Look for project-named directory from pyproject.toml
        package_name = self._get_package_name_from_pyproject(repository)
        if package_name:
            # Normalize package name (replace hyphens with underscores)
            normalized_name = package_name.replace("-", "_")
            package_dir = repository.path / normalized_name
            if package_dir.exists() and (package_dir / "__init__.py").exists():
                return {
                    "found": True,
                    "type": "project-named",
                    "directory": f"{normalized_name}/",
                }

        # Strategy 3: Look for any directory with __init__.py at root level
        # that isn't in the blocklist
        for item in repository.path.iterdir():
            if not item.is_dir():
                continue
            if item.name.startswith("."):
                continue
            if item.name.lower() in _NON_SOURCE_DIRS:
                continue
            if (item / "__init__.py").exists():
                return {
                    "found": True,
                    "type": "project-named",
                    "directory": f"{item.name}/",
                }

        return {"found": False, "type": "none", "directory": ""}

    def _get_package_name_from_pyproject(self, repository: Repository) -> str | None:
        """Extract package name from pyproject.toml.

        Supports both PEP 621 [project].name and Poetry [tool.poetry].name.

        Returns:
            Package name string or None if not found.
        """
        pyproject_path = repository.path / "pyproject.toml"
        if not pyproject_path.exists():
            return None

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            # PEP 621 format: [project].name
            if "project" in data and "name" in data["project"]:
                return data["project"]["name"]

            # Poetry format: [tool.poetry].name
            if (
                "tool" in data
                and "poetry" in data["tool"]
                and "name" in data["tool"]["poetry"]
            ):
                return data["tool"]["poetry"]["name"]

        except (OSError, tomllib.TOMLDecodeError):
            # If we can't read pyproject.toml, fall back to other strategies
            pass

        return None

    def _is_test_only_repository(self, repository: Repository) -> bool:
        """Detect if this is a test-only repository.

        Fix for #305: Test-only repos should be marked as not_applicable.

        A test-only repository has:
        - tests/ or test/ directory
        - No source directory (src/ or project-named)
        - Test-specific files (conftest.py, pytest.ini, tox.ini)

        Returns:
            True if this appears to be a test-only repository.
        """
        # Must have tests directory (already checked by caller)
        has_tests = (repository.path / "tests").exists() or (
            repository.path / "test"
        ).exists()
        if not has_tests:
            return False

        # Look for test-specific indicators
        test_indicators = [
            repository.path / "conftest.py",
            repository.path / "pytest.ini",
            repository.path / "tox.ini",
            repository.path / "setup.cfg",  # Often contains pytest config
        ]

        has_test_config = any(f.exists() for f in test_indicators)

        # Check if the repo name suggests it's a test repo
        name_suggests_tests = any(
            pattern in repository.name.lower()
            for pattern in ["test", "tests", "testing", "spec", "specs"]
        )

        # It's test-only if it has test configs OR the name suggests it
        return has_test_config or name_suggests_tests

    def _create_remediation(self, has_source: bool, has_tests: bool) -> Remediation:
        """Create context-aware remediation guidance for standard layout.

        Fix for #246: Provide guidance appropriate to the project type.
        """
        steps = []
        commands = []

        if not has_source:
            steps.extend(
                [
                    "Create a source directory for your code",
                    "Option A: Use src/ layout (recommended for packages)",
                    "Option B: Use project-named directory (e.g., mypackage/)",
                    "Ensure your package has __init__.py",
                ]
            )
            commands.extend(
                [
                    "# Option A: src layout",
                    "mkdir -p src/mypackage",
                    "touch src/mypackage/__init__.py",
                    "",
                    "# Option B: flat layout (project-named)",
                    "mkdir -p mypackage",
                    "touch mypackage/__init__.py",
                ]
            )

        if not has_tests:
            steps.extend(
                [
                    "Create tests/ directory for test files",
                    "Add at least one test file",
                ]
            )
            commands.extend(
                [
                    "",
                    "# Create tests directory",
                    "mkdir -p tests",
                    "touch tests/__init__.py",
                    "touch tests/test_example.py",
                ]
            )

        return Remediation(
            summary="Organize code into standard directories",
            steps=steps,
            tools=[],
            commands=commands,
            examples=[
                """# src layout (recommended for distributable packages)
project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       └── module.py
├── tests/
│   └── test_module.py
└── pyproject.toml

# flat layout (common in major projects like pandas, numpy)
project/
├── mypackage/
│   ├── __init__.py
│   └── module.py
├── tests/
│   └── test_module.py
└── pyproject.toml
""",
            ],
            citations=[
                Citation(
                    source="Python Packaging Authority",
                    title="src layout vs flat layout",
                    url="https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/",
                    relevance="Official guidance on Python project layouts",
                )
            ],
        )


class OneCommandSetupAssessor(BaseAssessor):
    """Assesses single-command development environment setup.

    Tier 2 Critical (3% weight) - One-command setup enables AI to quickly
    reproduce environments and reduces onboarding friction.
    """

    @property
    def attribute_id(self) -> str:
        return "one_command_setup"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="One-Command Build/Setup",
            category="Build & Development",
            tier=self.tier,
            description="Single command to set up development environment from fresh clone",
            criteria="Single command (make setup, npm install, etc.) documented prominently",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for single-command setup documentation and tooling.

        Scoring:
        - README has setup command (40%)
        - Setup script/Makefile exists (30%)
        - Setup in prominent location (30%)
        """
        # Check if README exists
        readme_path = repository.path / "README.md"
        if not readme_path.exists():
            return Finding.not_applicable(
                self.attribute,
                reason="No README found, cannot assess setup documentation",
            )

        score = 0
        evidence = []

        # Read README
        try:
            readme_content = readme_path.read_text()
        except Exception as e:
            return Finding(
                attribute=self.attribute,
                status="error",
                score=0.0,
                measured_value="error reading README",
                threshold="single command documented",
                evidence=[f"Error reading README: {e}"],
                remediation=None,
                error_message=str(e),
            )

        # Check 1: README has setup command (40%)
        setup_command = self._find_setup_command(readme_content, repository.languages)
        if setup_command:
            score += 40
            evidence.append(f"Setup command found in README: '{setup_command}'")
        else:
            evidence.append("No clear setup command found in README")

        # Check 2: Setup script/Makefile exists (30%)
        setup_files = self._check_setup_files(repository)
        if setup_files:
            score += 30
            evidence.append(f"Setup automation found: {', '.join(setup_files)}")
        else:
            evidence.append("No Makefile or setup script found")

        # Check 3: Setup in prominent location (30%)
        if self._is_setup_prominent(readme_content):
            score += 30
            evidence.append("Setup instructions in prominent location")
        else:
            evidence.append("Setup instructions not in first 3 sections")

        status = "pass" if score >= 75 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=setup_command or "multi-step setup",
            threshold="single command",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _find_setup_command(self, readme_content: str, languages: dict) -> str:
        """Find setup command in README based on language.

        Returns the setup command if found, empty string otherwise.
        """
        # Common setup patterns by language
        patterns = [
            r"(?:^|\n)(?:```(?:bash|sh|shell)?\n)?([a-z\-_]+\s+(?:install|setup))",
            r"(?:^|\n)(?:```(?:bash|sh|shell)?\n)?((?:make|npm|yarn|pnpm|pip|poetry|uv|cargo|go)\s+[a-z\-_]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, readme_content, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return ""

    def _check_setup_files(self, repository: Repository) -> list:
        """Check for setup automation files."""
        setup_files = []

        # Check for common setup files
        files_to_check = {
            "Makefile": "Makefile",
            "setup.sh": "shell script",
            "bootstrap.sh": "bootstrap script",
            "package.json": "npm/yarn",
            "pyproject.toml": "Python project",
            "setup.py": "Python setup",
        }

        for filename, description in files_to_check.items():
            if (repository.path / filename).exists():
                setup_files.append(filename)

        return setup_files

    def _is_setup_prominent(self, readme_content: str) -> bool:
        """Check if setup instructions are in first 3 sections of README."""
        # Split by markdown headers (## or ###)
        sections = re.split(r"\n##\s+", readme_content)

        # Check first 3 sections (plus preamble)
        first_sections = "\n".join(sections[:4])

        setup_keywords = [
            "install",
            "setup",
            "quick start",
            "getting started",
            "installation",
        ]

        return any(keyword in first_sections.lower() for keyword in setup_keywords)

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for one-command setup."""
        return Remediation(
            summary="Create single-command setup for development environment",
            steps=[
                "Choose setup automation tool (Makefile, setup script, or package manager)",
                "Create setup command that handles all dependencies",
                "Document setup command prominently in README (Quick Start section)",
                "Ensure setup is idempotent (safe to run multiple times)",
                "Test setup on fresh clone to verify it works",
            ],
            tools=["make", "npm", "pip", "poetry"],
            commands=[
                "# Example Makefile",
                "cat > Makefile << 'EOF'",
                ".PHONY: setup",
                "setup:",
                "\tpython -m venv venv",
                "\t. venv/bin/activate && pip install -r requirements.txt",
                "\tpre-commit install",
                "\tcp .env.example .env",
                "\t@echo 'Setup complete! Run make test to verify.'",
                "EOF",
            ],
            examples=[
                """# Quick Start section in README

## Quick Start

```bash
make setup  # One command to set up development environment
make test   # Run tests to verify setup
```
""",
            ],
            citations=[
                Citation(
                    source="freeCodeCamp",
                    title="Using make for project automation",
                    url="https://www.freecodecamp.org/news/want-to-know-the-easiest-way-to-save-time-use-make/",
                    relevance="Guide to using Makefiles for one-command setup",
                ),
            ],
        )


class IssuePRTemplatesAssessor(BaseAssessor):
    """Assesses presence of GitHub issue and PR templates.

    Tier 3 Important (1.5% weight) - Templates provide structure for AI
    when creating issues/PRs and ensure consistent formatting.
    """

    @property
    def attribute_id(self) -> str:
        return "issue_pr_templates"

    @property
    def tier(self) -> int:
        return 3  # Important

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Issue & Pull Request Templates",
            category="Repository Structure",
            tier=self.tier,
            description="Standardized templates for issues and PRs",
            criteria="PR template and issue templates in .github/",
            default_weight=0.015,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for GitHub issue and PR templates.

        Scoring:
        - PR template exists (50%)
        - Issue templates exist (50%, requires ≥2 templates)
        """
        score = 0
        evidence = []

        # Check for PR template (50%)
        pr_template_paths = [
            repository.path / ".github" / "PULL_REQUEST_TEMPLATE.md",
            repository.path / "PULL_REQUEST_TEMPLATE.md",
            repository.path / ".github" / "pull_request_template.md",
        ]

        pr_template_found = any(p.exists() for p in pr_template_paths)

        if pr_template_found:
            score += 50
            evidence.append("PR template found")
        else:
            evidence.append("No PR template found")

        # Check for issue templates (50%)
        issue_template_dir = repository.path / ".github" / "ISSUE_TEMPLATE"

        if issue_template_dir.exists() and issue_template_dir.is_dir():
            try:
                # Count .md and .yml files (both formats supported)
                md_templates = list(issue_template_dir.glob("*.md"))
                yml_templates = list(issue_template_dir.glob("*.yml")) + list(
                    issue_template_dir.glob("*.yaml")
                )
                template_count = len(md_templates) + len(yml_templates)

                if template_count >= 2:
                    score += 50
                    evidence.append(
                        f"Issue templates found: {template_count} templates"
                    )
                elif template_count == 1:
                    score += 25
                    evidence.append(
                        "Issue template directory exists with 1 template (need ≥2)"
                    )
                else:
                    evidence.append("Issue template directory exists but is empty")
            except OSError:
                evidence.append("Could not read issue template directory")
        else:
            evidence.append("No issue template directory found")

        status = "pass" if score >= 75 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"PR:{pr_template_found}, Issues:{template_count if issue_template_dir.exists() else 0}",
            threshold="PR template + ≥2 issue templates",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for missing templates."""
        return Remediation(
            summary="Create GitHub issue and PR templates in .github/ directory",
            steps=[
                "Create .github/ directory if it doesn't exist",
                "Add PULL_REQUEST_TEMPLATE.md for PRs",
                "Create .github/ISSUE_TEMPLATE/ directory",
                "Add bug_report.md for bug reports",
                "Add feature_request.md for feature requests",
                "Optionally add config.yml to configure template chooser",
            ],
            tools=["gh"],
            commands=[
                "# Create directories",
                "mkdir -p .github/ISSUE_TEMPLATE",
                "",
                "# Create PR template",
                "cat > .github/PULL_REQUEST_TEMPLATE.md << 'EOF'",
                "## Summary",
                "<!-- Describe the changes in this PR -->",
                "",
                "## Related Issues",
                "Fixes #",
                "",
                "## Testing",
                "- [ ] Tests added/updated",
                "- [ ] All tests pass",
                "",
                "## Checklist",
                "- [ ] Documentation updated",
                "- [ ] CHANGELOG.md updated",
                "EOF",
            ],
            examples=[
                """# Bug Report Template (.github/ISSUE_TEMPLATE/bug_report.md)

```markdown
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g. macOS 13.0]
- Version: [e.g. 1.0.0]
```
""",
            ],
            citations=[
                Citation(
                    source="GitHub Docs",
                    title="About issue and pull request templates",
                    url="https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates",
                    relevance="Official GitHub guide for templates",
                ),
            ],
        )


class SeparationOfConcernsAssessor(BaseAssessor):
    """Assesses code organization and separation of concerns.

    Tier 2 Critical (3% weight) - Clear boundaries improve testability,
    maintainability, and reduce cognitive load for AI.
    """

    @property
    def attribute_id(self) -> str:
        return "separation_of_concerns"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Separation of Concerns",
            category="Code Organization",
            tier=self.tier,
            description="Code organized with single responsibility per module",
            criteria="Feature-based organization, cohesive modules, low coupling",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for separation of concerns anti-patterns.

        Scoring:
        - Directory organization (40%): feature-based vs layer-based
        - File cohesion (30%): files under 500 lines
        - Module naming (30%): avoid utils/helpers
        """
        score = 0
        evidence = []

        # Check 1: Directory organization (40%)
        org_score = self._check_directory_organization(repository)
        score += org_score * 0.4
        if org_score >= 80:
            evidence.append("Good directory organization (feature-based or flat)")
        else:
            evidence.append("Layer-based directories detected (models/, views/, etc.)")

        # Check 2: File cohesion via size (30%)
        cohesion_score, file_stats = self._check_file_cohesion(repository)
        score += cohesion_score * 0.3
        evidence.append(
            f"File cohesion: {file_stats['oversized']}/{file_stats['total']} files >500 lines"
        )

        # Check 3: Module naming (30%)
        naming_score, antipatterns = self._check_module_naming(repository)
        score += naming_score * 0.3
        if antipatterns:
            evidence.append(f"Anti-pattern files found: {', '.join(antipatterns[:3])}")
        else:
            evidence.append("No catch-all modules (utils.py, helpers.py) detected")

        status = "pass" if score >= 75 else "fail"

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"organization:{org_score:.0f}, cohesion:{cohesion_score:.0f}, naming:{naming_score:.0f}",
            threshold="≥75 overall",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _check_directory_organization(self, repository: Repository) -> float:
        """Check for layer-based anti-patterns."""
        # Layer-based anti-patterns (BAD)
        layer_dirs = ["models", "views", "controllers", "services"]

        # Check src directory if it exists
        check_path = repository.path / "src"
        if not check_path.exists():
            check_path = repository.path

        found_layers = []
        for layer in layer_dirs:
            if (check_path / layer).exists():
                found_layers.append(layer)

        # Score: 100 if no layers, 60 if any layers found
        if not found_layers:
            return 100.0
        else:
            # Penalty per layer directory
            return max(60.0, 100.0 - (len(found_layers) * 15))

    def _check_file_cohesion(self, repository: Repository) -> tuple:
        """Check file sizes as cohesion indicator."""
        threshold = 500  # lines
        total_files = 0
        oversized_files = 0

        # Check Python files
        try:
            py_files = list(repository.path.rglob("*.py"))
            for py_file in py_files:
                # Skip venv, node_modules, etc.
                if any(
                    part in py_file.parts
                    for part in [".venv", "venv", "node_modules", ".git"]
                ):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        lines = len(f.readlines())
                    total_files += 1
                    if lines > threshold:
                        oversized_files += 1
                except (OSError, UnicodeDecodeError):
                    continue

        except OSError:
            pass

        if total_files == 0:
            return 100.0, {"total": 0, "oversized": 0}

        # Score: penalize based on percentage of oversized files
        oversized_ratio = oversized_files / total_files
        cohesion_score = max(0, 100.0 - (oversized_ratio * 100))

        return cohesion_score, {"total": total_files, "oversized": oversized_files}

    def _check_module_naming(self, repository: Repository) -> tuple:
        """Check for catch-all module anti-patterns."""
        antipattern_names = ["utils.py", "helpers.py", "common.py", "misc.py"]

        found = []
        try:
            for pattern in antipattern_names:
                matches = list(repository.path.rglob(pattern))
                # Filter out venv/node_modules
                matches = [
                    m
                    for m in matches
                    if not any(
                        part in m.parts
                        for part in [".venv", "venv", "node_modules", ".git"]
                    )
                ]
                if matches:
                    found.extend([m.name for m in matches])

        except OSError:
            pass

        # Score: 100 if none found, -20 per antipattern file
        naming_score = max(0, 100.0 - (len(found) * 20))

        return naming_score, found

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for separation of concerns."""
        return Remediation(
            summary="Refactor code to improve separation of concerns",
            steps=[
                "Avoid layer-based directories (models/, views/, controllers/)",
                "Organize by feature/domain instead (auth/, users/, billing/)",
                "Break large files (>500 lines) into focused modules",
                "Eliminate catch-all modules (utils.py, helpers.py)",
                "Each module should have single, well-defined responsibility",
                "Group related functions/classes by domain, not technical layer",
            ],
            tools=[],
            commands=[],
            examples=[
                """# Good: Feature-based organization
project/
├── auth/
│   ├── login.py
│   ├── signup.py
│   └── tokens.py
├── users/
│   ├── profile.py
│   └── preferences.py
└── billing/
    ├── invoices.py
    └── payments.py

# Bad: Layer-based organization
project/
├── models/
│   ├── user.py
│   ├── invoice.py
├── views/
│   ├── user_view.py
│   ├── invoice_view.py
└── controllers/
    ├── user_controller.py
    ├── invoice_controller.py
""",
            ],
            citations=[
                Citation(
                    source="Martin Fowler",
                    title="PresentationDomainDataLayering",
                    url="https://martinfowler.com/bliki/PresentationDomainDataLayering.html",
                    relevance="Explains layering vs feature organization",
                ),
                Citation(
                    source="Uncle Bob Martin",
                    title="The Single Responsibility Principle",
                    url="https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html",
                    relevance="Core SRP principle for module design",
                ),
            ],
        )

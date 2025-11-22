"""Structure assessors for project layout and separation of concerns."""

import re

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class StandardLayoutAssessor(BaseAssessor):
    """Assesses standard project layout patterns.

    Tier 1 Essential (10% weight) - Standard layouts help AI navigate code.
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
            criteria="Standard directories (src/, tests/, docs/) present",
            default_weight=0.10,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for standard project layout directories.

        Expected patterns:
        - Python: src/, tests/, docs/
        - JavaScript: src/, test/, docs/
        - Java: src/main/java, src/test/java
        """
        # Check for common standard directories
        standard_dirs = {
            "src": repository.path / "src",
        }

        # Check for tests directory (either tests/ or test/)
        tests_path = repository.path / "tests"
        if not tests_path.exists():
            tests_path = repository.path / "test"
        standard_dirs["tests"] = tests_path

        found_dirs = sum(1 for d in standard_dirs.values() if d.exists())
        required_dirs = len(standard_dirs)

        score = self.calculate_proportional_score(
            measured_value=found_dirs,
            threshold=required_dirs,
            higher_is_better=True,
        )

        status = "pass" if score >= 75 else "fail"

        evidence = [
            f"Found {found_dirs}/{required_dirs} standard directories",
            f"src/: {'✓' if (repository.path / 'src').exists() else '✗'}",
            f"tests/: {'✓' if (repository.path / 'tests').exists() or (repository.path / 'test').exists() else '✗'}",
        ]

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{found_dirs}/{required_dirs} directories",
            threshold=f"{required_dirs}/{required_dirs} directories",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for standard layout."""
        return Remediation(
            summary="Organize code into standard directories (src/, tests/, docs/)",
            steps=[
                "Create src/ directory for source code",
                "Create tests/ directory for test files",
                "Create docs/ directory for documentation",
                "Move source code into src/",
                "Move tests into tests/",
            ],
            tools=[],
            commands=[
                "mkdir -p src tests docs",
                "# Move source files to src/",
                "# Move test files to tests/",
            ],
            examples=[],
            citations=[
                Citation(
                    source="Python Packaging Authority",
                    title="Python Project Structure",
                    url="https://packaging.python.org/en/latest/tutorials/packaging-projects/",
                    relevance="Standard Python project layout",
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

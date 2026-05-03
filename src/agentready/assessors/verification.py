"""Verification assessor for single-file lint/type-check commands."""

import re

from ..models.attribute import Attribute
from ..models.finding import Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class SingleFileVerificationAssessor(BaseAssessor):
    """Assesses availability of single-file lint and type-check commands.

    Tier 1 Essential (5% weight) - Fast feedback loops are what separate
    agents that self-correct from agents that spiral. If linting takes 2
    minutes, the agent won't lint after each change. 2 seconds? It will.
    """

    @property
    def attribute_id(self) -> str:
        return "single_file_verification"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Single-File Verification",
            category="Verification & Feedback Loops",
            tier=self.tier,
            description="Single-file lint and type-check commands available for fast feedback",
            criteria="Documented single-file lint/type-check commands",
            default_weight=0.05,
        )

    # Patterns that suggest single-file lint/type-check commands.
    # Each entry is (regex, category) where category is "lint" or "typecheck".
    SINGLE_FILE_PATTERNS = [
        # Lint single file patterns — require file extension to avoid matching directories
        (r"eslint\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        (r"ruff\s+check\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        (r"pylint\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        (r"flake8\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        (r"rubocop\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        (r"golangci-lint\s+run\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        (r"black\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        (r"prettier\s+--check\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        (r"gofmt\s+(?!-)[\w./\-]*\.\w{1,10}", "lint"),
        # Type check single file patterns
        (r"mypy\s+(?!-)[\w./\-]*\.\w{1,10}", "typecheck"),
        (r"pyright\s+(?!-)[\w./\-]*\.\w{1,10}", "typecheck"),
        (r"tsc\s+--noEmit\s+(?!-)[\w./\-]*\.\w{1,10}", "typecheck"),
        # Path placeholder patterns (require path-like token)
        (r"lint.*(?:path/to|<file)", "lint"),
        (r"type.?check.*(?:path/to|<file)", "typecheck"),
    ]

    def assess(self, repository: Repository) -> Finding:
        """Check for documented single-file verification commands."""
        context_files = [
            "CLAUDE.md",
            "AGENTS.md",
            ".claude/CLAUDE.md",
        ]

        score = 0.0
        evidence = []
        found_lint = False
        found_typecheck = False

        for filename in context_files:
            filepath = repository.path / filename
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for pattern, category in self.SINGLE_FILE_PATTERNS:
                if not re.search(pattern, content, re.IGNORECASE):
                    continue
                if category == "lint" and not found_lint:
                    found_lint = True
                    score += 50.0
                    evidence.append(f"Single-file lint command found in {filename}")
                elif category == "typecheck" and not found_typecheck:
                    found_typecheck = True
                    score += 50.0
                    evidence.append(
                        f"Single-file type-check command found in {filename}"
                    )
                if found_lint and found_typecheck:
                    break

        # Also check README for documented commands
        readme_path = repository.path / "README.md"
        if readme_path.exists() and not (found_lint and found_typecheck):
            try:
                readme_content = readme_path.read_text(encoding="utf-8")
                for pattern, category in self.SINGLE_FILE_PATTERNS:
                    if not re.search(pattern, readme_content, re.IGNORECASE):
                        continue
                    if category == "lint" and not found_lint:
                        found_lint = True
                        score += 30.0
                        evidence.append("Single-file lint command found in README")
                    elif category == "typecheck" and not found_typecheck:
                        found_typecheck = True
                        score += 30.0
                        evidence.append(
                            "Single-file type-check command found in README"
                        )
                    if found_lint and found_typecheck:
                        break
            except (OSError, UnicodeDecodeError):
                pass

        # Check for linter configs that imply single-file capability
        linter_configs = {
            ".eslintrc": "ESLint",
            ".eslintrc.js": "ESLint",
            ".eslintrc.json": "ESLint",
            "eslint.config.js": "ESLint",
            "eslint.config.mjs": "ESLint",
            "ruff.toml": "Ruff",
            ".flake8": "Flake8",
            "mypy.ini": "MyPy",
        }

        pyproject = repository.path / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                if "[tool.ruff]" in content:
                    linter_configs["pyproject.toml(ruff)"] = "Ruff"
                if "[tool.mypy]" in content:
                    linter_configs["pyproject.toml(mypy)"] = "MyPy"
            except (OSError, UnicodeDecodeError):
                pass

        found_configs = [
            name
            for path, name in linter_configs.items()
            if not path.startswith("pyproject") and (repository.path / path).exists()
        ]
        if "pyproject.toml(ruff)" in linter_configs and "Ruff" not in found_configs:
            found_configs.append("Ruff")
        if "pyproject.toml(mypy)" in linter_configs and "MyPy" not in found_configs:
            found_configs.append("MyPy")

        if found_configs and score < 50:
            score = max(score, 30.0)
            evidence.append(
                f"Linter configs found ({', '.join(set(found_configs))}) but no documented single-file commands"
            )

        score = min(score, 100.0)

        if score >= 50:
            return Finding(
                attribute=self.attribute,
                status="pass",
                score=score,
                measured_value="documented" if score >= 80 else "partially documented",
                threshold="single-file lint + type-check commands documented",
                evidence=evidence,
                remediation=None if score >= 80 else self._create_remediation(),
                error_message=None,
            )
        else:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=score,
                measured_value="not documented",
                threshold="single-file lint + type-check commands documented",
                evidence=evidence
                or ["No single-file verification commands found in context files"],
                remediation=self._create_remediation(),
                error_message=None,
            )

    def _create_remediation(self) -> Remediation:
        return Remediation(
            summary="Document single-file lint and type-check commands in CLAUDE.md/AGENTS.md",
            steps=[
                "Add single-file lint command to context file (e.g., 'ruff check path/to/file.py')",
                "Add single-file type-check command (e.g., 'mypy path/to/file.py')",
                "Ensure these commands work without a full build step",
                "Target <5 seconds execution per file",
            ],
            tools=["ruff", "eslint", "mypy", "pyright", "tsc"],
            commands=[
                "# Python",
                "ruff check path/to/file.py",
                "mypy path/to/file.py",
                "",
                "# JavaScript/TypeScript",
                "npx eslint path/to/file.ts",
                "npx tsc --noEmit path/to/file.ts",
            ],
            examples=[],
            citations=[],
        )

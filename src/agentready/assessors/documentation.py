"""Documentation assessor for CLAUDE.md, README, docstrings, and ADRs."""

import re

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from .base import BaseAssessor


class CLAUDEmdAssessor(BaseAssessor):
    """Assesses presence and quality of CLAUDE.md configuration file.

    CLAUDE.md is the MOST IMPORTANT attribute (10% weight - Tier 1 Essential).
    Missing this file has 10x the impact of missing advanced features.
    """

    @property
    def attribute_id(self) -> str:
        return "claude_md_file"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="CLAUDE.md Configuration Files",
            category="Context Window Optimization",
            tier=self.tier,
            description="Project-specific configuration for Claude Code",
            criteria="CLAUDE.md file exists in repository root",
            default_weight=0.10,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for CLAUDE.md file in repository root.

        Pass criteria: CLAUDE.md exists
        Scoring: Binary (100 if exists, 0 if not)
        """
        claude_md_path = repository.path / "CLAUDE.md"

        # Fix TOCTOU: Use try-except around file read instead of existence check
        try:
            with open(claude_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            size = len(content)
            if size < 50:
                # File exists but is too small
                return Finding(
                    attribute=self.attribute,
                    status="fail",
                    score=25.0,
                    measured_value=f"{size} bytes",
                    threshold=">50 bytes",
                    evidence=[f"CLAUDE.md exists but is minimal ({size} bytes)"],
                    remediation=self._create_remediation(),
                    error_message=None,
                )

            return Finding(
                attribute=self.attribute,
                status="pass",
                score=100.0,
                measured_value="present",
                threshold="present",
                evidence=[f"CLAUDE.md found at {claude_md_path}"],
                remediation=None,
                error_message=None,
            )

        except FileNotFoundError:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="missing",
                threshold="present",
                evidence=["CLAUDE.md not found in repository root"],
                remediation=self._create_remediation(),
                error_message=None,
            )
        except OSError as e:
            return Finding.error(
                self.attribute, reason=f"Could not read CLAUDE.md file: {e}"
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for missing/inadequate CLAUDE.md."""
        return Remediation(
            summary="Create CLAUDE.md file with project-specific configuration for Claude Code",
            steps=[
                "Create CLAUDE.md file in repository root",
                "Add project overview and purpose",
                "Document key architectural patterns",
                "Specify coding standards and conventions",
                "Include build/test/deployment commands",
                "Add any project-specific context that helps AI assistants",
            ],
            tools=[],
            commands=[
                "touch CLAUDE.md",
                "# Add content describing your project",
            ],
            examples=[
                """# My Project

## Overview
Brief description of what this project does.

## Architecture
Key patterns and structure.

## Development
```bash
# Install dependencies
npm install

# Run tests
npm test

# Build
npm run build
```

## Coding Standards
- Use TypeScript strict mode
- Follow ESLint configuration
- Write tests for new features
"""
            ],
            citations=[
                Citation(
                    source="Anthropic",
                    title="Claude Code Documentation",
                    url="https://docs.anthropic.com/claude-code",
                    relevance="Official guidance on CLAUDE.md configuration",
                )
            ],
        )


class READMEAssessor(BaseAssessor):
    """Assesses README structure and completeness."""

    @property
    def attribute_id(self) -> str:
        return "readme_structure"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="README Structure",
            category="Documentation Standards",
            tier=self.tier,
            description="Well-structured README with key sections",
            criteria="README.md with installation, usage, and development sections",
            default_weight=0.10,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for README.md with required sections.

        Pass criteria: README.md exists with essential sections
        Scoring: Proportional based on section count
        """
        readme_path = repository.path / "README.md"

        # Fix TOCTOU: Use try-except around file read instead of existence check
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read().lower()

            required_sections = {
                "installation": any(
                    keyword in content
                    for keyword in ["install", "setup", "getting started"]
                ),
                "usage": any(
                    keyword in content for keyword in ["usage", "quickstart", "example"]
                ),
                "development": any(
                    keyword in content
                    for keyword in ["development", "contributing", "build"]
                ),
            }

            found_sections = sum(required_sections.values())
            total_sections = len(required_sections)

            score = self.calculate_proportional_score(
                measured_value=found_sections,
                threshold=total_sections,
                higher_is_better=True,
            )

            status = "pass" if score >= 75 else "fail"

            evidence = [
                f"Found {found_sections}/{total_sections} essential sections",
                f"Installation: {'✓' if required_sections['installation'] else '✗'}",
                f"Usage: {'✓' if required_sections['usage'] else '✗'}",
                f"Development: {'✓' if required_sections['development'] else '✗'}",
            ]

            return Finding(
                attribute=self.attribute,
                status=status,
                score=score,
                measured_value=f"{found_sections}/{total_sections} sections",
                threshold=f"{total_sections}/{total_sections} sections",
                evidence=evidence,
                remediation=self._create_remediation() if status == "fail" else None,
                error_message=None,
            )

        except FileNotFoundError:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="missing",
                threshold="present with sections",
                evidence=["README.md not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )
        except OSError as e:
            return Finding.error(
                self.attribute, reason=f"Could not read README.md: {str(e)}"
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for inadequate README."""
        return Remediation(
            summary="Create or enhance README.md with essential sections",
            steps=[
                "Add project overview and description",
                "Include installation/setup instructions",
                "Document basic usage with examples",
                "Add development/contributing guidelines",
                "Include build and test commands",
            ],
            tools=[],
            commands=[],
            examples=[
                """# Project Name

## Overview
What this project does and why it exists.

## Installation
```bash
pip install -e .
```

## Usage
```bash
myproject --help
```

## Development
```bash
# Run tests
pytest

# Format code
black .
```
"""
            ],
            citations=[
                Citation(
                    source="GitHub",
                    title="About READMEs",
                    url="https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes",
                    relevance="Best practices for README structure",
                )
            ],
        )


class ArchitectureDecisionsAssessor(BaseAssessor):
    """Assesses presence and quality of Architecture Decision Records (ADRs).

    Tier 3 Important (1.5% weight) - ADRs provide historical context for
    architectural decisions, helping AI understand "why" choices were made.
    """

    @property
    def attribute_id(self) -> str:
        return "architecture_decisions"

    @property
    def tier(self) -> int:
        return 3  # Important

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Architecture Decision Records (ADRs)",
            category="Documentation Standards",
            tier=self.tier,
            description="Lightweight documents capturing architectural decisions",
            criteria="ADR directory with documented decisions",
            default_weight=0.015,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for ADR directory and validate ADR format.

        Scoring:
        - ADR directory exists (40%)
        - ADR count (40%, up to 5 ADRs)
        - Template compliance (20%)
        """
        # Check for ADR directory in common locations
        adr_paths = [
            repository.path / "docs" / "adr",
            repository.path / ".adr",
            repository.path / "adr",
            repository.path / "docs" / "decisions",
        ]

        adr_dir = None
        for path in adr_paths:
            if path.exists() and path.is_dir():
                adr_dir = path
                break

        if not adr_dir:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no ADR directory",
                threshold="ADR directory with decisions",
                evidence=[
                    "No ADR directory found (checked docs/adr/, .adr/, adr/, docs/decisions/)"
                ],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Count .md files in ADR directory
        try:
            adr_files = list(adr_dir.glob("*.md"))
        except OSError as e:
            return Finding.error(
                self.attribute, reason=f"Could not read ADR directory: {e}"
            )

        adr_count = len(adr_files)

        if adr_count == 0:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=40.0,  # Directory exists but no ADRs
                measured_value="0 ADRs",
                threshold="≥3 ADRs",
                evidence=[
                    f"ADR directory found: {adr_dir.relative_to(repository.path)}",
                    "No ADR files (.md) found in directory",
                ],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Calculate score
        dir_score = 40  # Directory exists

        # Count score (8 points per ADR, up to 5 ADRs = 40 points)
        count_score = min(adr_count * 8, 40)

        # Template compliance score (sample up to 3 ADRs)
        template_score = self._check_template_compliance(adr_files[:3])

        total_score = dir_score + count_score + template_score

        status = "pass" if total_score >= 75 else "fail"

        evidence = [
            f"ADR directory found: {adr_dir.relative_to(repository.path)}",
            f"{adr_count} architecture decision records",
        ]

        # Check for consistent naming
        if self._has_consistent_naming(adr_files):
            evidence.append("Consistent naming pattern detected")

        # Add template compliance evidence
        if template_score > 0:
            evidence.append(
                f"Sampled {min(len(adr_files), 3)} ADRs: template compliance {template_score}/20"
            )

        return Finding(
            attribute=self.attribute,
            status=status,
            score=total_score,
            measured_value=f"{adr_count} ADRs",
            threshold="≥3 ADRs with template",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _has_consistent_naming(self, adr_files: list) -> bool:
        """Check if ADR files follow consistent naming pattern."""
        if len(adr_files) < 2:
            return True  # Not enough files to check consistency

        # Common patterns: 0001-*.md, ADR-001-*.md, adr-001-*.md
        patterns = [
            r"^\d{4}-.*\.md$",  # 0001-title.md
            r"^ADR-\d{3}-.*\.md$",  # ADR-001-title.md
            r"^adr-\d{3}-.*\.md$",  # adr-001-title.md
        ]

        for pattern in patterns:
            matches = sum(1 for f in adr_files if re.match(pattern, f.name))
            if matches >= len(adr_files) * 0.8:  # 80% match threshold
                return True

        return False

    def _check_template_compliance(self, sample_files: list) -> int:
        """Check if ADRs follow template structure.

        Returns score out of 20 points.
        """
        if not sample_files:
            return 0

        required_sections = ["status", "context", "decision", "consequences"]
        total_points = 0
        max_points_per_file = 20 // len(sample_files)

        for adr_file in sample_files:
            try:
                content = adr_file.read_text().lower()
                sections_found = sum(
                    1 for section in required_sections if section in content
                )

                # Award points proportionally
                file_score = (
                    sections_found / len(required_sections)
                ) * max_points_per_file
                total_points += file_score

            except OSError:
                continue  # Skip unreadable files

        return int(total_points)

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for missing/inadequate ADRs."""
        return Remediation(
            summary="Create Architecture Decision Records (ADRs) directory and document key decisions",
            steps=[
                "Create docs/adr/ directory in repository root",
                "Use Michael Nygard ADR template or MADR format",
                "Document each significant architectural decision",
                "Number ADRs sequentially (0001-*.md, 0002-*.md)",
                "Include Status, Context, Decision, and Consequences sections",
                "Update ADR status when decisions are revised (Superseded, Deprecated)",
            ],
            tools=["adr-tools", "log4brains"],
            commands=[
                "# Create ADR directory",
                "mkdir -p docs/adr",
                "",
                "# Create first ADR using template",
                "cat > docs/adr/0001-use-architecture-decision-records.md << 'EOF'",
                "# 1. Use Architecture Decision Records",
                "",
                "Date: 2025-11-22",
                "",
                "## Status",
                "Accepted",
                "",
                "## Context",
                "We need to record architectural decisions made in this project.",
                "",
                "## Decision",
                "We will use Architecture Decision Records (ADRs) as described by Michael Nygard.",
                "",
                "## Consequences",
                "- Decisions are documented with context",
                "- Future contributors understand rationale",
                "- ADRs are lightweight and version-controlled",
                "EOF",
            ],
            examples=[
                """# Example ADR Structure

```markdown
# 2. Use PostgreSQL for Database

Date: 2025-11-22

## Status
Accepted

## Context
We need a relational database for complex queries and ACID transactions.
Team has PostgreSQL experience. Need full-text search capabilities.

## Decision
Use PostgreSQL 15+ as primary database.

## Consequences
- Positive: Robust ACID, full-text search, team familiarity
- Negative: Higher resource usage than SQLite
- Neutral: Need to manage migrations, backups
```
""",
            ],
            citations=[
                Citation(
                    source="Michael Nygard",
                    title="Documenting Architecture Decisions",
                    url="https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions",
                    relevance="Original ADR format and rationale",
                ),
                Citation(
                    source="GitHub adr/madr",
                    title="Markdown ADR (MADR) Template",
                    url="https://github.com/adr/madr",
                    relevance="Modern ADR template with examples",
                ),
            ],
        )

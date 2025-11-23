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


class ConciseDocumentationAssessor(BaseAssessor):
    """Assesses documentation conciseness and structure.

    Tier 2 Critical (3% weight) - Concise documentation improves LLM
    performance by reducing context window pollution and improving
    information retrieval speed.
    """

    @property
    def attribute_id(self) -> str:
        return "concise_documentation"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Concise Documentation",
            category="Documentation",
            tier=self.tier,
            description="Documentation maximizes information density while minimizing token consumption",
            criteria="README <500 lines with clear structure, bullet points over prose",
            default_weight=0.03,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check README for conciseness and structure.

        Scoring:
        - README length (30%): <300 excellent, 300-500 good, 500-750 acceptable, >750 poor
        - Markdown structure (40%): Heading density (target 3-5 per 100 lines)
        - Concise formatting (30%): Bullet points, code blocks, no walls of text
        """
        readme_path = repository.path / "README.md"

        if not readme_path.exists():
            return Finding.not_applicable(
                self.attribute, reason="No README.md found in repository"
            )

        try:
            content = readme_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            return Finding.error(
                self.attribute, reason=f"Could not read README.md: {e}"
            )

        # Analyze README
        lines = content.splitlines()
        line_count = len(lines)

        # Check 1: README length (30%)
        length_score = self._calculate_length_score(line_count)

        # Check 2: Markdown structure (40%)
        headings = re.findall(r"^#{1,6} .+$", content, re.MULTILINE)
        heading_count = len(headings)
        structure_score = self._calculate_structure_score(heading_count, line_count)

        # Check 3: Concise formatting (30%)
        bullets = len(re.findall(r"^[\-\*] .+$", content, re.MULTILINE))
        code_blocks = len(re.findall(r"```", content)) // 2  # Pairs of backticks
        long_paragraphs = self._count_long_paragraphs(content)
        formatting_score = self._calculate_formatting_score(
            bullets, code_blocks, long_paragraphs
        )

        # Calculate total score
        score = (
            (length_score * 0.3) + (structure_score * 0.4) + (formatting_score * 0.3)
        )

        status = "pass" if score >= 75 else "fail"

        # Build evidence
        evidence = []

        # Length evidence
        if line_count < 300:
            evidence.append(f"README length: {line_count} lines (excellent)")
        elif line_count < 500:
            evidence.append(f"README length: {line_count} lines (good)")
        elif line_count < 750:
            evidence.append(f"README length: {line_count} lines (acceptable)")
        else:
            evidence.append(f"README length: {line_count} lines (excessive)")

        # Structure evidence
        heading_density = (heading_count / max(line_count, 1)) * 100
        if 3 <= heading_density <= 5:
            evidence.append(
                f"Heading density: {heading_density:.1f} per 100 lines (good structure)"
            )
        else:
            evidence.append(
                f"Heading density: {heading_density:.1f} per 100 lines (target: 3-5)"
            )

        # Formatting evidence
        if bullets > 10 and long_paragraphs == 0:
            evidence.append(
                f"{bullets} bullet points, {code_blocks} code blocks (concise formatting)"
            )
        elif long_paragraphs > 0:
            evidence.append(
                f"{long_paragraphs} paragraphs exceed 10 lines (walls of text)"
            )
        else:
            evidence.append(f"Only {bullets} bullet points (prefer bullets over prose)")

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{line_count} lines, {heading_count} headings, {bullets} bullets",
            threshold="<500 lines, structured format",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _calculate_length_score(self, line_count: int) -> float:
        """Calculate score based on README length.

        <300 lines: 100%
        300-500: 80%
        500-750: 60%
        >750: 0%
        """
        if line_count < 300:
            return 100.0
        elif line_count < 500:
            return 80.0
        elif line_count < 750:
            return 60.0
        else:
            return 0.0

    def _calculate_structure_score(self, heading_count: int, line_count: int) -> float:
        """Calculate score based on heading density.

        Target: 3-5 headings per 100 lines
        """
        if line_count == 0:
            return 0.0

        density = (heading_count / line_count) * 100

        # Optimal range: 3-5 headings per 100 lines
        if 3 <= density <= 5:
            return 100.0
        elif 2 <= density < 3 or 5 < density <= 7:
            return 80.0
        elif 1 <= density < 2 or 7 < density <= 10:
            return 60.0
        else:
            return 40.0

    def _calculate_formatting_score(
        self, bullets: int, code_blocks: int, long_paragraphs: int
    ) -> float:
        """Calculate score based on formatting style.

        Rewards: bullet points, code blocks
        Penalizes: long paragraphs (walls of text)
        """
        score = 50.0  # Base score

        # Reward bullet points
        if bullets > 20:
            score += 30
        elif bullets > 10:
            score += 20
        elif bullets > 5:
            score += 10

        # Reward code blocks
        if code_blocks > 5:
            score += 20
        elif code_blocks > 2:
            score += 10

        # Penalize long paragraphs
        if long_paragraphs == 0:
            score += 0  # No penalty
        elif long_paragraphs <= 3:
            score -= 20
        else:
            score -= 40

        return max(0, min(100, score))

    def _count_long_paragraphs(self, content: str) -> int:
        """Count paragraphs exceeding 10 lines (walls of text)."""
        # Split by double newlines to find paragraphs
        paragraphs = re.split(r"\n\n+", content)

        long_count = 0
        for para in paragraphs:
            # Skip code blocks and lists
            if para.strip().startswith("```") or para.strip().startswith("-"):
                continue

            lines = para.count("\n") + 1
            if lines > 10:
                long_count += 1

        return long_count

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for verbose documentation."""
        return Remediation(
            summary="Make documentation more concise and structured",
            steps=[
                "Break long README into multiple documents (docs/ directory)",
                "Add clear Markdown headings (##, ###) for structure",
                "Convert prose paragraphs to bullet points where possible",
                "Add table of contents for documents >100 lines",
                "Use code blocks instead of describing commands in prose",
                "Move detailed content to wiki or docs/, keep README focused",
            ],
            tools=[],
            commands=[
                "# Check README length",
                "wc -l README.md",
                "",
                "# Count headings",
                "grep -c '^#' README.md",
            ],
            examples=[
                """# Good: Concise with structure

## Quick Start
```bash
pip install -e .
agentready assess .
```

## Features
- Fast repository scanning
- HTML and Markdown reports
- 25 agent-ready attributes

## Documentation
See [docs/](docs/) for detailed guides.
""",
                """# Bad: Verbose prose

This project is a tool that helps you assess your repository
against best practices for AI-assisted development. It works by
scanning your codebase and checking for various attributes that
make repositories more effective when working with AI coding
assistants like Claude Code...

[Many more paragraphs of prose...]
""",
            ],
            citations=[
                Citation(
                    source="ArXiv",
                    title="LongCodeBench: Evaluating Coding LLMs at 1M Context Windows",
                    url="https://arxiv.org/abs/2501.00343",
                    relevance="Research showing performance degradation with long contexts",
                ),
                Citation(
                    source="Markdown Guide",
                    title="Basic Syntax",
                    url="https://www.markdownguide.org/basic-syntax/",
                    relevance="Best practices for Markdown formatting",
                ),
            ],
        )

"""Documentation assessor for CLAUDE.md, README, docstrings, and ADRs."""

import ast
import json
import re

import yaml

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from ..utils.subprocess_utils import safe_subprocess_run
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


class InlineDocumentationAssessor(BaseAssessor):
    """Assesses inline documentation (docstrings) coverage.

    Tier 2 Critical (3% weight) - Docstrings provide function-level
    context that helps LLMs understand code without reading implementation.
    """

    @property
    def attribute_id(self) -> str:
        return "inline_documentation"

    @property
    def tier(self) -> int:
        return 2  # Critical

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Inline Documentation",
            category="Documentation",
            tier=self.tier,
            description="Function, class, and module-level documentation using language-specific conventions",
            criteria="≥80% of public functions/classes have docstrings",
            default_weight=0.03,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Only applicable to languages with docstring conventions."""
        applicable_languages = {"Python", "JavaScript", "TypeScript"}
        return bool(set(repository.languages.keys()) & applicable_languages)

    def assess(self, repository: Repository) -> Finding:
        """Check docstring coverage for public functions and classes.

        Currently supports Python only. JavaScript/TypeScript can be added later.
        """
        if "Python" in repository.languages:
            return self._assess_python_docstrings(repository)
        else:
            return Finding.not_applicable(
                self.attribute,
                reason=f"Docstring check not implemented for {list(repository.languages.keys())}",
            )

    def _assess_python_docstrings(self, repository: Repository) -> Finding:
        """Assess Python docstring coverage using AST parsing."""
        # Get list of Python files
        try:
            result = safe_subprocess_run(
                ["git", "ls-files", "*.py"],
                cwd=repository.path,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            python_files = [f for f in result.stdout.strip().split("\n") if f]
        except Exception:
            python_files = [
                str(f.relative_to(repository.path))
                for f in repository.path.rglob("*.py")
            ]

        total_public_items = 0
        documented_items = 0

        for file_path in python_files:
            full_path = repository.path / file_path
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse the file with AST
                tree = ast.parse(content, filename=str(file_path))

                # Check module-level docstring
                module_doc = ast.get_docstring(tree)
                if module_doc:
                    documented_items += 1
                total_public_items += 1

                # Walk the AST and count functions/classes with docstrings
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        # Skip private functions/classes (starting with _)
                        if node.name.startswith("_"):
                            continue

                        total_public_items += 1
                        docstring = ast.get_docstring(node)
                        if docstring:
                            documented_items += 1

            except (OSError, UnicodeDecodeError, SyntaxError):
                # Skip files that can't be read or parsed
                continue

        if total_public_items == 0:
            return Finding.not_applicable(
                self.attribute,
                reason="No public Python functions or classes found",
            )

        coverage_percent = (documented_items / total_public_items) * 100
        score = self.calculate_proportional_score(
            measured_value=coverage_percent,
            threshold=80.0,
            higher_is_better=True,
        )

        status = "pass" if score >= 75 else "fail"

        # Build evidence
        evidence = [
            f"Documented items: {documented_items}/{total_public_items}",
            f"Coverage: {coverage_percent:.1f}%",
        ]

        if coverage_percent >= 80:
            evidence.append("Good docstring coverage")
        elif coverage_percent >= 60:
            evidence.append("Moderate docstring coverage")
        else:
            evidence.append("Many public functions/classes lack docstrings")

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{coverage_percent:.1f}%",
            threshold="≥80%",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for missing docstrings."""
        return Remediation(
            summary="Add docstrings to public functions and classes",
            steps=[
                "Identify functions/classes without docstrings",
                "Add PEP 257 compliant docstrings for Python",
                "Add JSDoc comments for JavaScript/TypeScript",
                "Include: description, parameters, return values, exceptions",
                "Add examples for complex functions",
                "Run pydocstyle to validate docstring format",
            ],
            tools=["pydocstyle", "jsdoc"],
            commands=[
                "# Install pydocstyle",
                "pip install pydocstyle",
                "",
                "# Check docstring coverage",
                "pydocstyle src/",
                "",
                "# Generate documentation",
                "pip install sphinx",
                "sphinx-apidoc -o docs/ src/",
            ],
            examples=[
                '''# Python - Good docstring
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price.

    Args:
        price: Original price in USD
        discount_percent: Discount percentage (0-100)

    Returns:
        Discounted price

    Raises:
        ValueError: If discount_percent not in 0-100 range

    Example:
        >>> calculate_discount(100.0, 20.0)
        80.0
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be 0-100")
    return price * (1 - discount_percent / 100)
''',
                """// JavaScript - Good JSDoc
/**
 * Calculate discounted price
 *
 * @param {number} price - Original price in USD
 * @param {number} discountPercent - Discount percentage (0-100)
 * @returns {number} Discounted price
 * @throws {Error} If discountPercent not in 0-100 range
 * @example
 * calculateDiscount(100.0, 20.0)
 * // Returns: 80.0
 */
function calculateDiscount(price, discountPercent) {
    if (discountPercent < 0 || discountPercent > 100) {
        throw new Error("Discount must be 0-100");
    }
    return price * (1 - discountPercent / 100);
}
""",
            ],
            citations=[
                Citation(
                    source="Python.org",
                    title="PEP 257 - Docstring Conventions",
                    url="https://peps.python.org/pep-0257/",
                    relevance="Python docstring standards",
                ),
                Citation(
                    source="TypeScript",
                    title="TSDoc Reference",
                    url="https://tsdoc.org/",
                    relevance="TypeScript documentation standard",
                ),
            ],
        )


class OpenAPISpecsAssessor(BaseAssessor):
    """Assesses presence and quality of OpenAPI specification.

    Tier 3 Important (1.5% weight) - Machine-readable API documentation
    enables AI to generate client code, tests, and integration code.
    """

    @property
    def attribute_id(self) -> str:
        return "openapi_specs"

    @property
    def tier(self) -> int:
        return 3  # Important

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="OpenAPI/Swagger Specifications",
            category="API Documentation",
            tier=self.tier,
            description="Machine-readable API documentation in OpenAPI format",
            criteria="OpenAPI 3.x spec with complete endpoint documentation",
            default_weight=0.015,
        )

    def is_applicable(self, repository: Repository) -> bool:
        """Check if repository appears to be a web API/service."""
        # Check for common web framework indicators
        web_indicators = [
            "flask",
            "django",
            "fastapi",
            "express",
            "spring",
            "gin",
            "rails",
            "sinatra",
        ]

        # Check for API-related files
        api_files = [
            repository.path / "app.py",
            repository.path / "server.py",
            repository.path / "main.py",
            repository.path / "api.py",
            repository.path / "routes.py",
        ]

        # If any API files exist, consider it applicable
        if any(f.exists() for f in api_files):
            return True

        # Check dependencies for web frameworks
        dep_files = [
            repository.path / "pyproject.toml",
            repository.path / "requirements.txt",
            repository.path / "package.json",
            repository.path / "pom.xml",
            repository.path / "go.mod",
            repository.path / "Gemfile",
        ]

        for dep_file in dep_files:
            if not dep_file.exists():
                continue

            try:
                content = dep_file.read_text(encoding="utf-8").lower()
                if any(framework in content for framework in web_indicators):
                    return True
            except (OSError, UnicodeDecodeError):
                continue

        # If no web framework indicators found, not applicable
        return False

    def assess(self, repository: Repository) -> Finding:
        """Check for OpenAPI specification files."""
        # Common OpenAPI spec file names
        spec_files = [
            "openapi.yaml",
            "openapi.yml",
            "openapi.json",
            "swagger.yaml",
            "swagger.yml",
            "swagger.json",
        ]

        # Check for spec file
        found_spec = None
        for spec_name in spec_files:
            spec_path = repository.path / spec_name
            if spec_path.exists():
                found_spec = spec_path
                break

        if not found_spec:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no OpenAPI spec",
                threshold="OpenAPI 3.x spec present",
                evidence=[
                    "No OpenAPI specification found",
                    f"Searched: {', '.join(spec_files)}",
                ],
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Parse the spec file
        try:
            content = found_spec.read_text(encoding="utf-8")

            # Try YAML first, then JSON
            try:
                spec_data = yaml.safe_load(content)
            except yaml.YAMLError:
                try:
                    spec_data = json.loads(content)
                except json.JSONDecodeError as e:
                    return Finding.error(
                        self.attribute,
                        reason=f"Could not parse {found_spec.name}: {str(e)}",
                    )

            # Extract version and check completeness
            openapi_version = spec_data.get("openapi", spec_data.get("swagger"))
            has_paths = "paths" in spec_data and len(spec_data["paths"]) > 0
            has_schemas = (
                "components" in spec_data
                and "schemas" in spec_data.get("components", {})
            ) or ("definitions" in spec_data)

            # Calculate score
            file_score = 60  # File exists

            # Version score
            if openapi_version and openapi_version.startswith("3."):
                version_score = 20
            elif openapi_version:
                version_score = 10  # Swagger 2.0
            else:
                version_score = 0

            # Completeness score
            if has_paths and has_schemas:
                completeness_score = 20
            elif has_paths:
                completeness_score = 10
            else:
                completeness_score = 0

            total_score = file_score + version_score + completeness_score
            status = "pass" if total_score >= 75 else "fail"

            # Build evidence
            evidence = [f"{found_spec.name} found in repository"]

            if openapi_version:
                evidence.append(f"OpenAPI version: {openapi_version}")

            if has_paths:
                path_count = len(spec_data["paths"])
                evidence.append(f"{path_count} endpoints documented")

            if has_schemas:
                if "components" in spec_data:
                    schema_count = len(spec_data["components"].get("schemas", {}))
                else:
                    schema_count = len(spec_data.get("definitions", {}))
                evidence.append(f"{schema_count} schemas defined")

            return Finding(
                attribute=self.attribute,
                status=status,
                score=total_score,
                measured_value=(
                    f"OpenAPI {openapi_version}" if openapi_version else "found"
                ),
                threshold="OpenAPI 3.x with paths and schemas",
                evidence=evidence,
                remediation=self._create_remediation() if status == "fail" else None,
                error_message=None,
            )

        except (OSError, UnicodeDecodeError) as e:
            return Finding.error(
                self.attribute, reason=f"Could not read {found_spec.name}: {str(e)}"
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for OpenAPI specs."""
        return Remediation(
            summary="Create OpenAPI specification for API endpoints",
            steps=[
                "Create openapi.yaml in repository root",
                "Define OpenAPI version 3.x",
                "Document all API endpoints with full schemas",
                "Add request/response examples",
                "Define security schemes (API keys, OAuth, etc.)",
                "Validate spec with Swagger Editor or Spectral",
                "Generate API documentation with Swagger UI or ReDoc",
            ],
            tools=["swagger-editor", "spectral", "openapi-generator"],
            commands=[
                "# Install OpenAPI validator",
                "npm install -g @stoplight/spectral-cli",
                "",
                "# Validate spec",
                "spectral lint openapi.yaml",
                "",
                "# Generate client SDK",
                "npx @openapitools/openapi-generator-cli generate \\",
                "  -i openapi.yaml \\",
                "  -g python \\",
                "  -o client/",
            ],
            examples=[
                """# openapi.yaml - Minimal example
openapi: 3.1.0
info:
  title: My API
  version: 1.0.0
  description: API for managing users

servers:
  - url: https://api.example.com/v1

paths:
  /users/{userId}:
    get:
      summary: Get user by ID
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found

components:
  schemas:
    User:
      type: object
      required:
        - id
        - email
      properties:
        id:
          type: string
          example: "user_123"
        email:
          type: string
          format: email
          example: "user@example.com"
        name:
          type: string
          example: "John Doe"
""",
            ],
            citations=[
                Citation(
                    source="OpenAPI Initiative",
                    title="OpenAPI Specification",
                    url="https://spec.openapis.org/oas/v3.1.0",
                    relevance="Official OpenAPI 3.1 specification",
                ),
                Citation(
                    source="Swagger",
                    title="API Documentation Best Practices",
                    url="https://swagger.io/resources/articles/best-practices-in-api-documentation/",
                    relevance="Guide to writing effective API docs",
                ),
            ],
        )

"""Documentation assessor for CLAUDE.md, README, docstrings, and ADRs."""

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

        if claude_md_path.exists():
            # Check file size (should have content)
            try:
                size = claude_md_path.stat().st_size
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

            except OSError:
                return Finding.error(
                    self.attribute, reason="Could not read CLAUDE.md file"
                )
        else:
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

        if not readme_path.exists():
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

        # Read README and check for key sections
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

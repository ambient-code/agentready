"""Documentation assessor for CLAUDE.md, README, docstrings, and ADRs."""

import ast
import json
import re
from pathlib import Path

import yaml

from ..models.attribute import Attribute
from ..models.finding import Citation, Finding, Remediation
from ..models.repository import Repository
from ..utils.subprocess_utils import safe_subprocess_run
from .adr_sources import CentralAdrSource
from .base import BaseAssessor


class AgentInstructionsAssessor(BaseAssessor):
    """Assesses presence and quality of agent instruction files (CLAUDE.md/AGENTS.md).

    Tier 1 Essential (7% weight). Context files help agents understand project
    conventions, but ETH Zurich (Feb 2026) found: auto-generated files hurt
    performance (-3%), human-written files help only marginally (+4%).
    Only include what agents can't discover by reading the code.
    """

    @property
    def attribute_id(self) -> str:
        return "agent_instructions"

    @property
    def tier(self) -> int:
        return 1  # Essential

    @property
    def attribute(self) -> Attribute:
        return Attribute(
            id=self.attribute_id,
            name="Agent Instruction Files",
            category="Context Window Optimization",
            tier=self.tier,
            description="Project-specific configuration for AI coding agents",
            criteria="CLAUDE.md or AGENTS.md file exists in repository root",
            default_weight=0.07,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for CLAUDE.md file in repository root.

        Two-phase scoring:

        Phase 1 - Presence (up to 70 points):
        - CLAUDE.md exists with >50 bytes (direct, symlink, or @ reference)
        - .claude/CLAUDE.md exists with >50 bytes
        - AGENTS.md exists with >50 bytes (cross-tool alternative)
        - 25 if file exists but is minimal, 0 if missing

        Phase 2 - Length (up to 30 points, only if presence passes):
        - <=150 lines: 30 (full credit)
        - 151-300 lines: 15 (partial credit)
        - >300 lines: 0 (exceeds recommended limit)

        Also checks for agent access documentation (substantiating evidence).

        Security:
        - @ references are restricted to relative paths within repository
        - Path traversal attempts (../) and absolute paths are rejected
        """
        claude_md_path = repository.path / "CLAUDE.md"
        agents_md_path = repository.path / "AGENTS.md"

        # Phase 1: Determine presence and read content
        resolved_content = None
        base_score = 0.0
        evidence = []
        measured_value = "missing"

        try:
            resolved_path = claude_md_path.resolve(strict=True)
            is_symlink = claude_md_path.is_symlink()

            with open(resolved_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            size = len(file_content)

            if size >= 50:
                resolved_content = file_content
                base_score = 100.0
                measured_value = "present"
                evidence.append(f"CLAUDE.md found at {claude_md_path}")
                if is_symlink:
                    target = (
                        resolved_path.relative_to(repository.path)
                        if resolved_path.is_relative_to(repository.path)
                        else resolved_path
                    )
                    evidence.append(f"Symlink to {target} ({size} bytes)")
                if self._check_agents_md_exists(agents_md_path):
                    evidence.append("AGENTS.md also present (cross-tool compatibility)")
            else:
                referenced_file = self._extract_at_reference(file_content)
                if referenced_file:
                    ref_path = repository.path / referenced_file
                    ref_content, ref_size = self._read_referenced_file(ref_path)
                    if ref_content and ref_size >= 50:
                        resolved_content = ref_content
                        base_score = 100.0
                        measured_value = f"@ reference to {referenced_file}"
                        evidence.append(
                            f"CLAUDE.md found with @ reference to {referenced_file}"
                        )
                        evidence.append(f"Referenced file contains {ref_size} bytes")
                        if self._check_agents_md_exists(agents_md_path):
                            evidence.append(
                                "AGENTS.md also present (cross-tool compatibility)"
                            )
                    else:
                        base_score = 25.0
                        measured_value = f"{size} bytes, invalid @ reference"
                        evidence.append(
                            f"CLAUDE.md exists but is minimal ({size} bytes)"
                        )
                        evidence.append(
                            f"@ reference to {referenced_file} but file is missing or too small"
                        )
                else:
                    base_score = 25.0
                    measured_value = f"{size} bytes"
                    evidence.append(f"CLAUDE.md exists but is minimal ({size} bytes)")

        except FileNotFoundError:
            dotclaude_md_path = repository.path / ".claude" / "CLAUDE.md"
            dotclaude_content, dotclaude_size = self._read_referenced_file(
                dotclaude_md_path
            )

            if dotclaude_content and dotclaude_size >= 50:
                resolved_content = dotclaude_content
                base_score = 100.0
                measured_value = ".claude/CLAUDE.md present"
                evidence.append("CLAUDE.md not found at repository root")
                evidence.append(f".claude/CLAUDE.md found with {dotclaude_size} bytes")
                if self._check_agents_md_exists(agents_md_path):
                    evidence.append("AGENTS.md also present (cross-tool compatibility)")
            else:
                agents_content, agents_size = self._read_referenced_file(agents_md_path)
                if agents_content and agents_size >= 50:
                    resolved_content = agents_content
                    base_score = 100.0
                    measured_value = "AGENTS.md present"
                    evidence.extend(
                        [
                            "CLAUDE.md not found",
                            f"AGENTS.md found with {agents_size} bytes",
                            "AGENTS.md is the cross-tool standard supported by Claude Code, Copilot, Cursor, Codex, and Gemini CLI",
                        ]
                    )
                else:
                    base_score = 0.0
                    measured_value = "missing"
                    evidence.extend(
                        [
                            "CLAUDE.md not found in repository root",
                            "AGENTS.md not found (alternative)",
                        ]
                    )
        except OSError as e:
            return Finding.error(
                self.attribute, reason=f"Could not read CLAUDE.md file: {e}"
            )

        # File missing or minimal: return early without quality checks
        if base_score < 50:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=base_score,
                measured_value=measured_value,
                threshold=">50 bytes, <=150 lines recommended",
                evidence=evidence,
                remediation=self._create_remediation(),
                error_message=None,
            )

        # Phase 2: Length validation (applies to all repos)
        line_count = len(resolved_content.splitlines()) if resolved_content else 0
        if line_count <= 150:
            length_score = 30.0
            evidence.append(f"Context file is {line_count} lines (good: <=150)")
        elif line_count <= 300:
            length_score = 15.0
            evidence.append(
                f"Context file is {line_count} lines (partial credit: <=300)"
            )
        else:
            length_score = 0.0
            evidence.append(
                f"Context file is {line_count} lines (exceeds 300 line limit, consider splitting into .claude/skills/)"
            )

        final_score = min(70.0 + length_score, 100.0)

        # Phase 3: Agent access documentation (substantiating evidence only)
        self._check_agent_access(resolved_content, evidence)

        return Finding(
            attribute=self.attribute,
            status="pass",
            score=final_score,
            measured_value=measured_value,
            threshold=">50 bytes, <=150 lines recommended",
            evidence=evidence,
            remediation=None,
            error_message=None,
        )

    def _extract_at_reference(self, content: str) -> str | None:
        """Extract @ reference from CLAUDE.md content.

        Looks for patterns like:
        - @AGENTS.md
        - @.claude/agents.md
        - @ AGENTS.md (with space)

        Security: Rejects path traversal attempts (../) and absolute paths.

        Returns the referenced filename or None if no reference found.
        """
        # Match @filename.md or @ filename.md (with optional space)
        # Support paths like @.claude/agents.md
        pattern = r"@\s*([A-Za-z0-9_\-./]+\.md)"
        match = re.search(pattern, content, re.IGNORECASE)

        if match:
            ref = match.group(1)
            # Prevent path traversal - reject if contains .. or starts with /
            if ".." in ref or ref.startswith("/"):
                return None
            return ref
        return None

    def _read_referenced_file(self, file_path: Path) -> tuple[str | None, int]:
        """Read a referenced file and return its content and size.

        Returns (content, size) tuple, or (None, 0) if file doesn't exist or can't be read.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content, len(content)
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            return None, 0

    def _check_agents_md_exists(self, agents_md_path: Path) -> bool:
        """Check if AGENTS.md exists and has sufficient content."""
        content, size = self._read_referenced_file(agents_md_path)
        return content is not None and size >= 50

    def _check_agent_access(self, content: str, evidence: list[str]) -> None:
        """Check for agent access documentation in context file content.

        Substantiating evidence only, not a hard gate. Looks for access-related
        headings or co-occurrence of platform and tool/auth keywords.
        """
        if not content:
            return

        access_heading = re.compile(
            r"^#{1,3}\s.*(agent\s+access|repository\s+access|repo\s+access|platform)",
            re.IGNORECASE | re.MULTILINE,
        )
        if access_heading.search(content):
            evidence.append("Agent access documentation found")
            return

        content_lower = content.lower()
        platform_keywords = ["github", "gitlab", "bitbucket", "azure devops"]
        tool_auth_keywords = [
            "gh ",
            "glab",
            "authentication",
            "token",
            "credential",
            "vpn",
            "cli tool",
        ]

        has_platform = any(kw in content_lower for kw in platform_keywords)
        has_tool_auth = any(kw in content_lower for kw in tool_auth_keywords)

        if has_platform and has_tool_auth:
            evidence.append(
                "Agent access documentation found (platform and tool/auth references)"
            )

    def _create_remediation(self) -> Remediation:
        """Create remediation guidance for missing/inadequate CLAUDE.md."""
        return Remediation(
            summary="Create CLAUDE.md or AGENTS.md with project-specific configuration for AI coding assistants",
            steps=[
                "Choose one of three approaches:",
                "  Option 1: Create standalone CLAUDE.md (>50 bytes) with project context",
                "  Option 2: Create AGENTS.md and symlink CLAUDE.md to it (cross-tool compatibility)",
                "  Option 3: Create AGENTS.md and reference it with @AGENTS.md in minimal CLAUDE.md",
                "Keep the file under 150 lines (hard cap: 300 lines)",
                "Add project overview and purpose",
                "Document key architectural patterns",
                "Specify coding standards and conventions",
                "Include build/test/deployment commands",
                "Add agent access info (platform, CLI tool, auth requirements) if applicable",
                "Add any project-specific context that helps AI assistants",
            ],
            tools=[],
            commands=[
                "# Option 1: Standalone CLAUDE.md",
                "touch CLAUDE.md",
                "# Add content describing your project",
                "",
                "# Option 2: Symlink CLAUDE.md to AGENTS.md",
                "touch AGENTS.md",
                "# Add content to AGENTS.md",
                "ln -s AGENTS.md CLAUDE.md",
                "",
                "# Option 3: @ reference in CLAUDE.md",
                "echo '@AGENTS.md' > CLAUDE.md",
                "touch AGENTS.md",
                "# Add content to AGENTS.md",
            ],
            examples=[
                """# Standalone CLAUDE.md (Option 1)

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
""",
                """# CLAUDE.md with @ reference (Option 3)
@AGENTS.md
""",
                """# AGENTS.md (shared by multiple tools)

## Project Overview
This project implements a REST API for user management.

## Architecture
- Layered architecture: controllers, services, repositories
- PostgreSQL database with SQLAlchemy ORM
- FastAPI web framework

## Development Workflow
```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Run tests
pytest

# Start server
uvicorn app.main:app --reload
```

## Code Conventions
- Use type hints for all functions
- Follow PEP 8 style guide
- Write docstrings for public APIs
- Maintain >80% test coverage
""",
            ],
            citations=[
                Citation(
                    source="Anthropic",
                    title="Claude Code Documentation",
                    url="https://docs.anthropic.com/claude-code",
                    relevance="Official guidance on CLAUDE.md configuration",
                ),
                Citation(
                    source="agents.md",
                    title="AGENTS.md Specification",
                    url="https://agents.md/",
                    relevance="Emerging standard for cross-tool AI assistant configuration",
                ),
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
            default_weight=0.05,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for README.md with required sections.

        Pass criteria: README.md exists with essential sections
        Scoring: Proportional based on section count
        """
        # Case-insensitive README lookup — handles readme.md, README.md, Readme.rst, etc.
        # sorted() ensures deterministic selection when multiple variants exist.
        readme_names = {"readme.md", "readme.rst", "readme.txt", "readme"}
        try:
            readme_path = next(
                (
                    f
                    for f in sorted(
                        repository.path.iterdir(), key=lambda f: f.name.lower()
                    )
                    if f.is_file() and f.name.lower() in readme_names
                ),
                None,
            )
        except OSError as e:
            return Finding.error(
                self.attribute, reason=f"Could not scan repository root: {e}"
            )

        if readme_path is None:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="missing",
                threshold="present with sections",
                evidence=["README not found"],
                remediation=self._create_remediation(),
                error_message=None,
            )

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
                self.attribute, reason=f"Could not read {readme_path.name}: {str(e)}"
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
            examples=["""# Project Name

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
"""],
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

    Tier 3 Important (1% weight) - ADRs provide historical context for
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
            default_weight=0.01,
        )

    def assess(self, repository: Repository) -> Finding:
        """Check for ADR directory and validate ADR format.

        Scoring:
        - ADR directory exists (40%)
        - ADR count (40%, up to 5 ADRs)
        - Template compliance (20%)
        - Partial credit (60%) when no directory exists but CLAUDE.md/AGENTS.md
          references an architecture decisions section or external ADR repo
        """
        # Case-insensitive ADR directory scan. Covers common conventions:
        # docs/adr, docs/ADRs, docs/architecture, docs/design, docs/specs, specs/, adr/, etc.
        docs_target_names = {
            "adr",
            "adrs",
            "decisions",
            "architecture-decisions",
            "architecture",
            "design",
            "specs",
        }
        root_target_names = {
            "adr",
            "adrs",
            "decisions",
            "architecture-decisions",
            "specs",
        }
        adr_dir = None

        # Search docs/ first (most common location)
        docs_dir = repository.path / "docs"
        if docs_dir.is_dir():
            try:
                for candidate in sorted(docs_dir.iterdir()):
                    if (
                        candidate.is_dir()
                        and candidate.name.lower() in docs_target_names
                    ):
                        adr_dir = candidate
                        break
            except OSError:
                pass  # docs/ unreadable — fall through to root scan

        # Fall back to repo root and hidden .adr
        if not adr_dir:
            if (repository.path / ".adr").is_dir():
                adr_dir = repository.path / ".adr"
            else:
                try:
                    for candidate in sorted(repository.path.iterdir()):
                        if (
                            candidate.is_dir()
                            and candidate.name.lower() in root_target_names
                        ):
                            adr_dir = candidate
                            break
                except OSError:
                    pass  # root unreadable — adr_dir stays None, fail finding follows

        if not adr_dir:
            # Check for central ADR repo configured via adr_source config.
            # If the org maintains ADRs centrally, the repo still gets full credit.
            central_finding = self._check_central_adr_source(repository)
            if central_finding is not None:
                return central_finding

            partial_score, partial_evidence = self._check_agent_file_adr_summary(
                repository
            )
            if partial_score > 0:
                return Finding(
                    attribute=self.attribute,
                    status="fail",
                    score=partial_score,
                    measured_value="ADR summary in agent context file",
                    threshold="ADR directory with decisions",
                    evidence=partial_evidence,
                    remediation=self._create_remediation(),
                    error_message=None,
                )
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no ADR directory",
                threshold="ADR directory with decisions",
                evidence=[
                    "No ADR directory found (checked docs/adr/, docs/architecture/, docs/design/, docs/specs/, specs/, and variants — all case-insensitive)"
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
            # An empty local ADR placeholder should not penalise repos that
            # rely on a central ADR source — check central config first.
            central_finding = self._check_central_adr_source(repository)
            if central_finding is not None:
                return central_finding
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

    def _check_central_adr_source(self, repository: Repository) -> "Finding | None":
        """Return a Finding if a central ADR source is configured.

        When an organisation maintains ADRs in a dedicated central repository
        (configured via config.adr_source), the assessed repo should receive
        full credit for architecture_decisions even though it has no local ADR dir.

        Returns:
            Passing Finding: central repo is reachable and has applicable ADRs.
            Skipped Finding: central repo is configured but the path or subdir
                             cannot be read (degrade gracefully, not a FAIL).
            None: adr_source is not configured, or is configured but has no ADRs
                  that match this repo (caller falls through to local checks).
        """
        if repository.config is None:
            return None
        adr_source = repository.config.adr_source
        if not adr_source:
            return None

        local_path = Path(adr_source.repo)
        if not local_path.exists():
            return Finding.skipped(
                self.attribute,
                f"Central ADR repo not found at configured path: {local_path}",
            )

        source = CentralAdrSource(local_path=local_path, adr_path=adr_source.path)

        if not source.adr_dir.is_dir():
            return Finding.skipped(
                self.attribute,
                f"Central ADR subdirectory missing: {source.adr_dir}",
            )

        # Explicitly verify the directory is readable before delegating.
        # get_matching_adr_files swallows OSError and returns [], which would
        # cause a misleading None/fall-through rather than a skipped finding.
        try:
            list(source.adr_dir.iterdir())
        except OSError:
            return Finding.skipped(
                self.attribute,
                f"Central ADR directory is not readable: {source.adr_dir}",
            )

        matched = source.get_matching_adr_files(repository.name)
        if not matched:
            return None

        # Score central ADRs using the same formula as local ADRs so that a
        # repo with 1 central ADR is not auto-passed at 100 points.
        adr_count = len(matched)
        dir_score = 40  # "directory" credit: central repo is configured and reachable
        count_score = min(adr_count * 8, 40)
        template_score = self._check_template_compliance(matched[:3])
        total_score = dir_score + count_score + template_score
        status = "pass" if total_score >= 75 else "fail"

        evidence = [
            f"Central ADR repository: {source.adr_dir}",
            f"{adr_count} ADR(s) in central repo apply to {repository.name}",
        ]
        if self._has_consistent_naming(matched):
            evidence.append("Consistent naming pattern detected")
        if template_score > 0:
            evidence.append(
                f"Sampled {min(adr_count, 3)} ADRs: template compliance {template_score}/20"
            )

        return Finding(
            attribute=self.attribute,
            status=status,
            score=float(total_score),
            measured_value=f"{adr_count} central ADR(s)",
            threshold="ADR directory with decisions",
            evidence=evidence,
            remediation=self._create_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _check_agent_file_adr_summary(
        self, repository: Repository
    ) -> tuple[float, list[str]]:
        """Check CLAUDE.md/AGENTS.md for an architecture decisions section or
        external ADR repo link. Returns (score, evidence) — score is 0 if nothing found.

        Partial credit (60/100) recognises projects that summarise key architectural
        decisions in their agent context file and link out to an external ADR repo.
        This is less agent-ready than an inline directory (agents can't follow links),
        but it's meaningfully better than no documentation at all.
        """
        section_header = re.compile(
            r"^#{1,3}\s.*(architecture|decision|adr|rfc|design)",
            re.IGNORECASE | re.MULTILINE,
        )
        external_link = re.compile(
            r"https?://\S*(adr|rfc|decision|architecture)\S*",
            re.IGNORECASE,
        )

        for filename in ("CLAUDE.md", "AGENTS.md"):
            filepath = repository.path / filename
            if not filepath.is_file():
                continue
            try:
                content = filepath.read_text()
            except OSError:
                continue

            has_section = bool(section_header.search(content))
            has_link = bool(external_link.search(content))

            if has_section and has_link:
                evidence = [
                    "No inline ADR directory found",
                    f"{filename} contains architectural decision documentation (partial credit: 60/100)",
                    "Add a docs/adr/ directory with inline ADRs for full credit",
                ]
                if has_link:
                    evidence.insert(
                        2, f"{filename} links to external ADR/RFC repository"
                    )
                return 60.0, evidence

        return 0.0, []

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
        max_points_per_file = 20 / len(sample_files)

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

        return round(total_points)

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
        """Only applicable to languages with documentation conventions."""
        applicable_languages = {"Python", "JavaScript", "TypeScript", "Go"}
        return bool(set(repository.languages.keys()) & applicable_languages)

    def assess(self, repository: Repository) -> Finding:
        """Check documentation coverage for public functions and classes.

        Dispatches based on the primary programming language (by file count)
        to handle multi-language repos correctly.
        """
        primary = self._primary_language(repository, {"Python", "Go"})
        if primary == "Python":
            return self._assess_python_docstrings(repository)
        elif primary == "Go":
            return self._assess_go_godoc(repository)
        else:
            return Finding.not_applicable(
                self.attribute,
                reason=f"Documentation check not implemented for {list(repository.languages.keys())}",
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

    @staticmethod
    def _has_go_doc_comment(
        lines: list[str], symbol_idx: int, symbol_name: str
    ) -> bool:
        """Check if an exported Go symbol has a doc comment above it.

        Matches go doc behavior: any comment immediately preceding a
        declaration (no blank line between) is a doc comment.
        """
        prev_idx = symbol_idx - 1
        while prev_idx >= 0 and not lines[prev_idx].strip():
            prev_idx -= 1
        if prev_idx < 0:
            return False

        prev_line = lines[prev_idx].strip()

        if prev_line.startswith("//"):
            return True

        if prev_line.endswith("*/"):
            return True

        return False

    def _assess_go_godoc(self, repository: Repository) -> Finding:
        """Assess Go godoc comment coverage on exported symbols.

        Go convention: exported symbols (starting with uppercase) should have
        a comment directly above starting with the symbol name.
        """
        import re

        try:
            result = safe_subprocess_run(
                ["git", "ls-files", "*.go"],
                cwd=repository.path,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            go_files = [
                f
                for f in result.stdout.strip().split("\n")
                if f and not f.endswith("_test.go") and "vendor/" not in f
            ]
        except Exception:
            go_files = [
                str(f.relative_to(repository.path))
                for f in repository.path.rglob("*.go")
                if not f.name.endswith("_test.go") and "vendor" not in f.parts
            ]

        total_exported = 0
        documented_exported = 0
        has_doc_go = False

        # Match exported functions (including methods with receivers), types,
        # vars, and consts. Group 1 captures the exported symbol name.
        exported_pattern = re.compile(
            r"^(?:func\s+(?:\([^)]+\)\s+)?|type\s+|var\s+|const\s+)([A-Z]\w*)"
        )

        for file_path in go_files:
            full_path = repository.path / file_path
            if full_path.name == "doc.go":
                has_doc_go = True

            try:
                lines = full_path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue

            for i, line in enumerate(lines):
                match = exported_pattern.match(line.strip())
                if not match:
                    continue

                total_exported += 1
                symbol_name = match.group(1)

                if i > 0 and self._has_go_doc_comment(lines, i, symbol_name):
                    documented_exported += 1

        if total_exported == 0:
            return Finding.not_applicable(
                self.attribute,
                reason="No exported Go symbols found",
            )

        coverage_percent = (documented_exported / total_exported) * 100
        score = self.calculate_proportional_score(
            measured_value=coverage_percent,
            threshold=80.0,
            higher_is_better=True,
        )

        status = "pass" if score >= 75 else "fail"

        evidence = [
            f"Documented exports: {documented_exported}/{total_exported}",
            f"Godoc coverage: {coverage_percent:.1f}%",
        ]
        if has_doc_go:
            evidence.append("doc.go package documentation found")

        return Finding(
            attribute=self.attribute,
            status=status,
            score=score,
            measured_value=f"{coverage_percent:.1f}%",
            threshold="≥80%",
            evidence=evidence,
            remediation=self._create_go_remediation() if status == "fail" else None,
            error_message=None,
        )

    def _create_go_remediation(self) -> Remediation:
        """Create remediation guidance for missing Go godoc comments."""
        return Remediation(
            summary="Add godoc comments to exported Go symbols",
            steps=[
                "Add comments above all exported functions, types, and constants",
                "Comments must start with the symbol name (Go convention)",
                "Add doc.go files for package-level documentation",
                "Add Example functions in test files for executable docs",
            ],
            tools=[],
            commands=[
                "# Check for missing documentation",
                "go vet ./...",
            ],
            examples=[
                """// Handler processes incoming HTTP requests and routes them
// to the appropriate service method.
func Handler(w http.ResponseWriter, r *http.Request) {
    // ...
}

// ErrNotFound is returned when the requested resource does not exist.
var ErrNotFound = errors.New("not found")
""",
            ],
            citations=[
                Citation(
                    source="Go Documentation",
                    title="Effective Go - Commentary",
                    url="https://go.dev/doc/effective_go#commentary",
                    relevance="Go documentation conventions",
                ),
            ],
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

    Tier 3 Important (2% weight) - Machine-readable API documentation
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
            default_weight=0.02,
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

        # Recursively search for spec files
        found_specs = []
        excluded_dirs = {
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
        }

        for spec_name in spec_files:
            try:
                # Use rglob to search recursively
                matches = list(repository.path.rglob(spec_name))
                # Filter out files in excluded directories
                matches = [
                    m
                    for m in matches
                    if not any(part in m.parts for part in excluded_dirs)
                ]
                found_specs.extend(matches)
            except OSError:
                # If rglob fails, continue to next pattern
                continue

        # Remove duplicates while preserving order
        seen = set()
        unique_specs = []
        for spec in found_specs:
            if spec not in seen:
                seen.add(spec)
                unique_specs.append(spec)

        # Select the first found spec (prefer root-level if available, otherwise first found)
        found_spec = None
        if unique_specs:
            # Prefer root-level specs, otherwise use first found
            root_specs = [s for s in unique_specs if s.parent == repository.path]
            found_spec = root_specs[0] if root_specs else unique_specs[0]

        if not found_spec:
            return Finding(
                attribute=self.attribute,
                status="fail",
                score=0.0,
                measured_value="no OpenAPI spec",
                threshold="OpenAPI 3.x spec present",
                evidence=[
                    "No OpenAPI specification found",
                    f"Searched recursively for: {', '.join(spec_files)}",
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
                    spec_relative_path = found_spec.relative_to(repository.path)
                    return Finding.error(
                        self.attribute,
                        reason=f"Could not parse {spec_relative_path}: {str(e)}",
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
            spec_relative_path = found_spec.relative_to(repository.path)
            evidence = [f"{spec_relative_path} found in repository"]

            # Indicate if multiple OpenAPI files were found
            if len(unique_specs) > 1:
                other_specs = [
                    s.relative_to(repository.path)
                    for s in unique_specs
                    if s != found_spec
                ]
                evidence.append(
                    f"Additional OpenAPI files found: {', '.join(str(p) for p in other_specs[:3])}"
                )
                if len(other_specs) > 3:
                    evidence.append(f"... and {len(other_specs) - 3} more")

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
            spec_relative_path = found_spec.relative_to(repository.path)
            return Finding.error(
                self.attribute, reason=f"Could not read {spec_relative_path}: {str(e)}"
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

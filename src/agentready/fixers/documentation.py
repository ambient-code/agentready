"""Fixers for documentation-related attributes."""

import os
import shutil
from pathlib import Path
from typing import Optional

from ..models.finding import Finding
from ..models.fix import CommandFix, Fix, MultiStepFix
from ..models.repository import Repository
from .base import BaseFixer

# Env var required for Claude CLI (used by CLAUDEmdFixer)
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"

# Single line written to CLAUDE.md when pointing to AGENTS.md
CLAUDE_MD_REDIRECT_LINE = "@AGENTS.md\n"

# Command run by CLAUDEmdFixer to generate CLAUDE.md via Claude CLI
CLAUDE_MD_COMMAND = (
    'claude -p "Initialize this project with a CLAUDE.md file" '
    '--allowedTools "Read,Edit,Write,Bash"'
)


class _ClaudeMdToAgentRedirectFix(Fix):
    """Post-step fix: move CLAUDE.md content to AGENTS.md, replace CLAUDE.md with @AGENTS.md."""

    def __init__(
        self,
        attribute_id: str,
        description: str,
        points_gained: float,
        repository_path: Path,
    ):
        self.attribute_id = attribute_id
        self.description = description
        self.points_gained = points_gained
        self.repository_path = repository_path

    def apply(self, dry_run: bool = False) -> bool:
        """Move CLAUDE.md content to AGENTS.md and replace CLAUDE.md with @AGENTS.md.

        If AGENTS.md already exists, it is preserved and only CLAUDE.md is replaced
        with the redirect (idempotent behavior).
        """
        claude_md = self.repository_path / "CLAUDE.md"
        if not claude_md.exists():
            return True  # Nothing to do (e.g. dry run of first step did not create it)
        if dry_run:
            return True
        agents_md = self.repository_path / "AGENTS.md"
        if not agents_md.exists():
            content = claude_md.read_text(encoding="utf-8")
            agents_md.write_text(content, encoding="utf-8")
        claude_md.write_text(CLAUDE_MD_REDIRECT_LINE, encoding="utf-8")
        return True

    def preview(self) -> str:
        """Preview move and redirect."""
        return "Move CLAUDE.md content to AGENTS.md and replace CLAUDE.md with @AGENTS.md"


class _ClaudeMdRedirectOnlyFix(Fix):
    """Single-step fix: create or overwrite CLAUDE.md with @AGENTS.md (when AGENTS.md already exists)."""

    def __init__(
        self,
        attribute_id: str,
        description: str,
        points_gained: float,
        repository_path: Path,
    ):
        self.attribute_id = attribute_id
        self.description = description
        self.points_gained = points_gained
        self.repository_path = repository_path

    def apply(self, dry_run: bool = False) -> bool:
        """Write CLAUDE.md with redirect to AGENTS.md."""
        if dry_run:
            return True
        (self.repository_path / "CLAUDE.md").write_text(CLAUDE_MD_REDIRECT_LINE, encoding="utf-8")
        return True

    def preview(self) -> str:
        return "Create CLAUDE.md with @AGENTS.md redirect"


class CLAUDEmdFixer(BaseFixer):
    """Fixer for missing CLAUDE.md file.

    Runs the Claude CLI to generate CLAUDE.md in the repository
    instead of using a static template.
    """

    @property
    def attribute_id(self) -> str:
        """Return attribute ID."""
        return "claude_md_file"

    def can_fix(self, finding: Finding) -> bool:
        """Check if CLAUDE.md is missing."""
        return finding.status == "fail" and finding.attribute.id == self.attribute_id

    def generate_fix(self, repository: Repository, finding: Finding) -> Optional[Fix]:
        """Return a fix for missing CLAUDE.md.

        If AGENTS.md already exists: create CLAUDE.md with @AGENTS.md only (no Claude CLI).
        Otherwise: run Claude CLI to generate CLAUDE.md, then move content to AGENTS.md
        and replace CLAUDE.md with @AGENTS.md. Returns None if Claude CLI is required
        but not on PATH or ANTHROPIC_API_KEY is not set.
        """
        if not self.can_fix(finding):
            return None

        agents_md = repository.path / "AGENTS.md"
        if agents_md.exists():
            points = self.estimate_score_improvement(finding)
            return _ClaudeMdRedirectOnlyFix(
                attribute_id=self.attribute_id,
                description="Create CLAUDE.md with @AGENTS.md redirect",
                points_gained=points,
                repository_path=repository.path,
            )

        if not shutil.which("claude"):
            return None
        if not os.environ.get(ANTHROPIC_API_KEY_ENV):
            return None

        points = self.estimate_score_improvement(finding)
        command_fix = CommandFix(
            attribute_id=self.attribute_id,
            description="Run Claude CLI to create CLAUDE.md in the project",
            points_gained=points,
            command=CLAUDE_MD_COMMAND,
            working_dir=repository.path,
            repository_path=repository.path,
            capture_output=False,  # Stream Claude output to terminal
        )
        post_step = _ClaudeMdToAgentRedirectFix(
            attribute_id=self.attribute_id,
            description="Move CLAUDE.md content to AGENTS.md and replace CLAUDE.md with @AGENTS.md",
            points_gained=0.0,  # Points already counted in command step
            repository_path=repository.path,
        )
        return MultiStepFix(
            attribute_id=self.attribute_id,
            description="Run Claude CLI to create CLAUDE.md, then move content to AGENTS.md",
            points_gained=points,
            steps=[command_fix, post_step],
        )


class GitignoreFixer(BaseFixer):
    """Fixer for incomplete .gitignore."""

    def __init__(self):
        """Initialize fixer."""
        self.template_path = (
            Path(__file__).parent.parent
            / "templates"
            / "align"
            / "gitignore_additions.txt"
        )

    @property
    def attribute_id(self) -> str:
        """Return attribute ID."""
        return "gitignore_completeness"

    def can_fix(self, finding: Finding) -> bool:
        """Check if .gitignore can be improved."""
        return finding.status == "fail" and finding.attribute.id == self.attribute_id

    def generate_fix(self, repository: Repository, finding: Finding) -> Optional[Fix]:
        """Add missing patterns to .gitignore."""
        if not self.can_fix(finding):
            return None

        # Load recommended patterns
        if not self.template_path.exists():
            return None

        additions = self.template_path.read_text(encoding="utf-8").splitlines()

        # Import FileModificationFix
        from ..models.fix import FileModificationFix

        # Create fix
        return FileModificationFix(
            attribute_id=self.attribute_id,
            description="Add recommended patterns to .gitignore",
            points_gained=self.estimate_score_improvement(finding),
            file_path=Path(".gitignore"),
            additions=additions,
            repository_path=repository.path,
            append=False,  # Smart merge to avoid duplicates
        )

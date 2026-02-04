"""Fixers for documentation-related attributes."""

import os
import shutil
from pathlib import Path
from typing import Optional

from ..models.finding import Finding
from ..models.fix import CommandFix, Fix
from ..models.repository import Repository
from .base import BaseFixer

# Env var required for Claude CLI (used by CLAUDEmdFixer)
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"

# Command run by CLAUDEmdFixer to generate CLAUDE.md via Claude CLI
CLAUDE_MD_COMMAND = (
    'claude -p "Initialize this project with a CLAUDE.md file" '
    '--allowedTools "Read,Edit,Write,Bash"'
)


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
        """Return a fix that runs Claude CLI to create CLAUDE.md.

        Returns None if Claude CLI is not on PATH or ANTHROPIC_API_KEY is not set.
        """
        if not self.can_fix(finding):
            return None

        if not shutil.which("claude"):
            return None
        if not os.environ.get(ANTHROPIC_API_KEY_ENV):
            return None

        return CommandFix(
            attribute_id=self.attribute_id,
            description="Run Claude CLI to create CLAUDE.md in the project",
            points_gained=self.estimate_score_improvement(finding),
            command=CLAUDE_MD_COMMAND,
            working_dir=repository.path,
            repository_path=repository.path,
            capture_output=False,  # Stream Claude output to terminal
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

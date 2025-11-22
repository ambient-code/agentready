"""Fixers for documentation-related attributes."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, PackageLoader

from ..models.finding import Finding
from ..models.fix import FileCreationFix, Fix
from ..models.repository import Repository
from .base import BaseFixer


class CLAUDEmdFixer(BaseFixer):
    """Fixer for missing CLAUDE.md file."""

    def __init__(self):
        """Initialize with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("agentready", "templates/align"),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @property
    def attribute_id(self) -> str:
        """Return attribute ID."""
        return "claude_md_file"

    def can_fix(self, finding: Finding) -> bool:
        """Check if CLAUDE.md is missing."""
        return finding.status == "fail" and finding.attribute.id == self.attribute_id

    def generate_fix(self, repository: Repository, finding: Finding) -> Optional[Fix]:
        """Generate CLAUDE.md from template."""
        if not self.can_fix(finding):
            return None

        # Load template
        template = self.env.get_template("CLAUDE.md.j2")

        # Render with repository context
        content = template.render(
            repo_name=repository.path.name,
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )

        # Create fix
        return FileCreationFix(
            attribute_id=self.attribute_id,
            description="Create CLAUDE.md with project documentation template",
            points_gained=self.estimate_score_improvement(finding),
            file_path=Path("CLAUDE.md"),
            content=content,
            repository_path=repository.path,
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

"""Fixers for testing-related attributes."""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, PackageLoader

from ..models.finding import Finding
from ..models.fix import CommandFix, FileCreationFix, Fix, MultiStepFix
from ..models.repository import Repository
from .base import BaseFixer


class PrecommitHooksFixer(BaseFixer):
    """Fixer for missing pre-commit hooks."""

    def __init__(self):
        """Initialize with Jinja2 environment."""
        self.env_bootstrap = Environment(
            loader=PackageLoader("agentready", "templates/bootstrap"),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @property
    def attribute_id(self) -> str:
        """Return attribute ID."""
        return "precommit_hooks"

    def can_fix(self, finding: Finding) -> bool:
        """Check if pre-commit hooks are missing."""
        return finding.status == "fail" and finding.attribute.id == self.attribute_id

    def generate_fix(self, repository: Repository, finding: Finding) -> Optional[Fix]:
        """Generate .pre-commit-config.yaml and install hooks."""
        if not self.can_fix(finding):
            return None

        # Determine primary language (use Python as default)
        primary_lang = "python"
        if repository.languages:
            primary_lang = max(
                repository.languages, key=repository.languages.get
            ).lower()

        # Try to load language-specific template, fallback to python
        try:
            template = self.env_bootstrap.get_template(
                f"precommit-{primary_lang}.yaml.j2"
            )
        except Exception:
            template = self.env_bootstrap.get_template("precommit-python.yaml.j2")

        content = template.render()

        # Create file creation fix
        file_fix = FileCreationFix(
            attribute_id=self.attribute_id,
            description="Create .pre-commit-config.yaml",
            points_gained=0,  # Will be set by multi-step fix
            file_path=Path(".pre-commit-config.yaml"),
            content=content,
            repository_path=repository.path,
        )

        # Create command to install hooks
        install_fix = CommandFix(
            attribute_id=self.attribute_id,
            description="Install pre-commit hooks",
            points_gained=0,
            command="pre-commit install",
            working_dir=None,
            repository_path=repository.path,
        )

        # Combine into multi-step fix
        return MultiStepFix(
            attribute_id=self.attribute_id,
            description="Set up pre-commit hooks (config + install)",
            points_gained=self.estimate_score_improvement(finding),
            steps=[file_fix, install_fix],
        )

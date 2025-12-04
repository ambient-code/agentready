"""Fixers for testing-related attributes."""

import logging
from pathlib import Path
from typing import Optional

from jinja2 import Environment, PackageLoader, TemplateError, TemplateNotFound

from ..models.finding import Finding
from ..models.fix import CommandFix, FileCreationFix, Fix, MultiStepFix
from ..models.repository import Repository
from .base import BaseFixer

logger = logging.getLogger(__name__)


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
            detected_lang = max(repository.languages, key=repository.languages.get)
            primary_lang = detected_lang.lower()
            logger.debug(
                f"Detected primary language: {detected_lang} (normalized: {primary_lang})"
            )

        # Try to load language-specific template, fallback to python
        template_name = f"precommit-{primary_lang}.yaml.j2"
        try:
            template = self.env_bootstrap.get_template(template_name)
            logger.info(f"Using pre-commit template for {primary_lang}")
        except TemplateNotFound:
            logger.warning(
                f"Template {template_name} not found, falling back to Python template"
            )
            try:
                template = self.env_bootstrap.get_template("precommit-python.yaml.j2")
            except (TemplateNotFound, TemplateError) as e:
                logger.error(f"Cannot load pre-commit template: {e}")
                return None
        except TemplateError as e:
            logger.error(f"Template error for {template_name}: {e}")
            return None

        # Render and validate template
        try:
            content = template.render()
        except TemplateError as e:
            logger.error(f"Failed to render pre-commit template: {e}")
            return None

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

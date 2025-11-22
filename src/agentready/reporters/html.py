"""HTML reporter for generating interactive assessment reports."""

import json
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..models.assessment import Assessment
from ..models.theme import Theme
from .base import BaseReporter


class HTMLReporter(BaseReporter):
    """Generates self-contained interactive HTML reports.

    Features:
    - Filter by status (pass/fail/skipped)
    - Sort by category, score, or tier
    - Search attributes by name
    - Collapsible finding details
    - Color-coded scores and tiers
    - Certification ladder visualization
    - Works offline (no CDN dependencies)
    """

    def __init__(self):
        """Initialize HTML reporter with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("agentready", "templates"),
            autoescape=select_autoescape(["html", "xml", "j2"]),
        )

    def generate(self, assessment: Assessment, output_path: Path) -> Path:
        """Generate HTML report from assessment data.

        Args:
            assessment: Complete assessment with findings
            output_path: Path where HTML file should be saved

        Returns:
            Path to generated HTML file

        Raises:
            IOError: If HTML cannot be written
        """
        # Load template
        template = self.env.get_template("report.html.j2")

        # Determine theme to use
        theme = self._resolve_theme(assessment.config)

        # Get all available themes for theme switcher
        available_themes = {
            name: Theme.get_theme(name).to_dict()
            for name in Theme.get_available_themes()
        }

        # Prepare data for template
        template_data = {
            "repository": assessment.repository,
            "timestamp": assessment.timestamp,
            "overall_score": assessment.overall_score,
            "certification_level": assessment.certification_level,
            "attributes_assessed": assessment.attributes_assessed,
            "attributes_not_assessed": assessment.attributes_not_assessed,
            "attributes_total": assessment.attributes_total,
            "findings": assessment.findings,
            "duration_seconds": assessment.duration_seconds,
            "config": assessment.config,
            "metadata": assessment.metadata,
            # Embed assessment JSON for JavaScript
            "assessment_json": json.dumps(assessment.to_dict()),
            # Theme data
            "theme": theme,
            "theme_name": theme.name,
            "available_themes": available_themes,
            "available_themes_json": json.dumps(available_themes),
        }

        # Render template
        html_content = template.render(**template_data)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def _resolve_theme(self, config) -> Theme:
        """Resolve theme from config.

        Args:
            config: Assessment config (may be None)

        Returns:
            Resolved Theme object
        """
        # No config or no custom theme → use default or configured theme
        if not config:
            return Theme.get_theme("default")

        # Custom theme provided → build from custom_theme dict
        if config.custom_theme:
            return Theme.from_dict(
                {
                    "name": "custom",
                    "display_name": "Custom",
                    **config.custom_theme,
                }
            )

        # Use configured theme name
        theme_name = getattr(config, "report_theme", "default")
        try:
            return Theme.get_theme(theme_name)
        except KeyError:
            # Fall back to default if theme not found
            return Theme.get_theme("default")

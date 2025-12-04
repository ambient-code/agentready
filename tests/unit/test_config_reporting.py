"""Tests for config display in HTML and Markdown reports."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agentready.models.assessment import Assessment
from agentready.models.attribute import Attribute
from agentready.models.config import Config
from agentready.models.finding import Finding
from agentready.models.repository import Repository
from agentready.reporters.html import HTMLReporter
from agentready.reporters.markdown import MarkdownReporter


@pytest.fixture
def sample_repository():
    """Create sample repository for testing."""
    return Repository(
        name="test-repo",
        path=Path("/tmp/test-repo"),
        branch="main",
        commit_hash="abc123def456",
        languages={"Python": 10, "JavaScript": 5},
        total_files=15,
        total_lines=1000,
    )


@pytest.fixture
def sample_attribute():
    """Create sample attribute for testing."""
    return Attribute(
        id="claude_md",
        name="CLAUDE.md File",
        tier=1,
        category="Documentation",
        default_weight=0.15,
        description="Repository has CLAUDE.md file",
    )


@pytest.fixture
def sample_config():
    """Create sample config with customizations."""
    return Config(
        weights={"claude_md": 0.20, "readme_file": 0.15},
        excluded_attributes=["dependency_freshness", "lock_files"],
        output_dir=Path("./custom-output"),
        language_overrides={"Python": True, "JavaScript": False},
        report_theme="dark",
    )


@pytest.fixture
def assessment_with_config(sample_repository, sample_attribute, sample_config):
    """Create assessment with custom config."""
    finding = Finding.create_pass(
        attribute=sample_attribute,
        evidence=["CLAUDE.md file found"],
        measured_value="Present",
    )

    return Assessment(
        repository=sample_repository,
        findings=[finding],
        timestamp=datetime.now(timezone.utc),
        duration_seconds=5.0,
        config=sample_config,
        version="1.0.0",
    )


@pytest.fixture
def assessment_without_config(sample_repository, sample_attribute):
    """Create assessment without custom config."""
    finding = Finding.create_pass(
        attribute=sample_attribute,
        evidence=["CLAUDE.md file found"],
        measured_value="Present",
    )

    return Assessment(
        repository=sample_repository,
        findings=[finding],
        timestamp=datetime.now(timezone.utc),
        duration_seconds=5.0,
        config=None,
        version="1.0.0",
    )


class TestHTMLConfigReporting:
    """Test config summary in HTML reports."""

    def test_html_includes_config_section_when_config_present(
        self, assessment_with_config
    ):
        """HTML report should include config section when config is used."""
        reporter = HTMLReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)

        try:
            reporter.generate(assessment_with_config, output_path)

            # Read generated HTML
            html_content = output_path.read_text()

            # Should include config summary section
            assert "⚙️ Configuration Used" in html_content
            assert "This assessment used custom configuration" in html_content

            # Should show custom weights
            assert "Custom weights" in html_content
            assert "2 attributes" in html_content  # 2 custom weights

            # Should show excluded attributes
            assert "Excluded attributes" in html_content
            assert "dependency_freshness" in html_content
            assert "lock_files" in html_content

            # Should show output directory
            assert "Output directory" in html_content
            assert "custom-output" in html_content

            # Should show language overrides
            assert "Language overrides" in html_content
            assert "2 languages" in html_content

            # Should show theme
            assert "Theme" in html_content
            assert "dark" in html_content

        finally:
            output_path.unlink()

    def test_html_no_config_section_when_no_config(self, assessment_without_config):
        """HTML report should not include config section when no config used."""
        reporter = HTMLReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)

        try:
            reporter.generate(assessment_without_config, output_path)

            # Read generated HTML
            html_content = output_path.read_text()

            # Should NOT include config summary section
            assert "⚙️ Configuration Used" not in html_content
            assert "This assessment used custom configuration" not in html_content

        finally:
            output_path.unlink()

    def test_html_config_section_styling(self, assessment_with_config):
        """Config section should have proper styling."""
        reporter = HTMLReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = Path(f.name)

        try:
            reporter.generate(assessment_with_config, output_path)

            # Read generated HTML
            html_content = output_path.read_text()

            # Check for styling elements
            assert "config-summary" in html_content
            assert "var(--surface-elevated)" in html_content
            assert "var(--primary)" in html_content

        finally:
            output_path.unlink()


class TestMarkdownConfigReporting:
    """Test config summary in Markdown reports."""

    def test_markdown_includes_config_section_when_config_present(
        self, assessment_with_config
    ):
        """Markdown report should include config section when config is used."""
        reporter = MarkdownReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = Path(f.name)

        try:
            reporter.generate(assessment_with_config, output_path)

            # Read generated Markdown
            md_content = output_path.read_text()

            # Should include config summary section
            assert "## ⚙️ Configuration Used" in md_content
            assert "This assessment used custom configuration" in md_content

            # Should show custom weights
            assert "📊 **Custom weights**: 2 attributes" in md_content

            # Should show excluded attributes
            assert "⊘ **Excluded attributes**" in md_content
            assert "dependency_freshness" in md_content
            assert "lock_files" in md_content

            # Should show output directory
            assert "📁 **Output directory**: `./custom-output`" in md_content

            # Should show language overrides
            assert "🔧 **Language overrides**: 2 languages" in md_content

            # Should show theme
            assert "🎨 **Theme**: dark" in md_content

        finally:
            output_path.unlink()

    def test_markdown_no_config_section_when_no_config(
        self, assessment_without_config
    ):
        """Markdown report should not include config section when no config used."""
        reporter = MarkdownReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = Path(f.name)

        try:
            reporter.generate(assessment_without_config, output_path)

            # Read generated Markdown
            md_content = output_path.read_text()

            # Should NOT include config summary section
            assert "## ⚙️ Configuration Used" not in md_content
            assert "This assessment used custom configuration" not in md_content

        finally:
            output_path.unlink()

    def test_markdown_config_section_ordering(self, assessment_with_config):
        """Config section should appear after certification ladder."""
        reporter = MarkdownReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = Path(f.name)

        try:
            reporter.generate(assessment_with_config, output_path)

            # Read generated Markdown
            md_content = output_path.read_text()

            # Find positions
            cert_ladder_pos = md_content.find("## 🎖️ Certification Ladder")
            config_pos = md_content.find("## ⚙️ Configuration Used")
            findings_pos = md_content.find("## 📋 Detailed Findings")

            # Config should be between cert ladder and findings
            assert cert_ladder_pos < config_pos < findings_pos

        finally:
            output_path.unlink()


class TestConfigSectionContent:
    """Test specific content formatting in config sections."""

    def test_config_with_minimal_customization(self, sample_repository, sample_attribute):
        """Test config section with minimal customization."""
        # Create config with only theme changed
        minimal_config = Config(report_theme="light")

        finding = Finding.create_pass(
            attribute=sample_attribute,
            evidence=["Test"],
            measured_value="Present",
        )

        assessment = Assessment(
            repository=sample_repository,
            findings=[finding],
            timestamp=datetime.now(timezone.utc),
            duration_seconds=1.0,
            config=minimal_config,
            version="1.0.0",
        )

        # Generate markdown report
        reporter = MarkdownReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = Path(f.name)

        try:
            reporter.generate(assessment, output_path)
            md_content = output_path.read_text()

            # Should only show theme (no weights, excluded, etc.)
            assert "🎨 **Theme**: light" in md_content
            assert "Custom weights" not in md_content
            assert "Excluded attributes" not in md_content

        finally:
            output_path.unlink()

    def test_config_with_empty_lists(self, sample_repository, sample_attribute):
        """Test config section handles empty weights/exclusions gracefully."""
        # Create config with empty weights and exclusions
        empty_config = Config(
            weights={},
            excluded_attributes=[],
            report_theme="default",
        )

        finding = Finding.create_pass(
            attribute=sample_attribute,
            evidence=["Test"],
            measured_value="Present",
        )

        assessment = Assessment(
            repository=sample_repository,
            findings=[finding],
            timestamp=datetime.now(timezone.utc),
            duration_seconds=1.0,
            config=empty_config,
            version="1.0.0",
        )

        # Generate markdown report
        reporter = MarkdownReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = Path(f.name)

        try:
            reporter.generate(assessment, output_path)
            md_content = output_path.read_text()

            # Should show config section but not empty lists
            assert "## ⚙️ Configuration Used" in md_content
            assert "Custom weights" not in md_content  # Empty, not shown
            assert "Excluded attributes" not in md_content  # Empty, not shown
            assert "🎨 **Theme**: default" in md_content  # Theme always shown

        finally:
            output_path.unlink()


class TestConfigIntegration:
    """Test config reporting integrates properly with full assessment flow."""

    def test_config_displayed_consistently_across_formats(
        self, assessment_with_config
    ):
        """Config info should be consistent in HTML and Markdown."""
        html_reporter = HTMLReporter()
        md_reporter = MarkdownReporter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as hf:
            html_path = Path(hf.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as mf:
            md_path = Path(mf.name)

        try:
            # Generate both reports
            html_reporter.generate(assessment_with_config, html_path)
            md_reporter.generate(assessment_with_config, md_path)

            html_content = html_path.read_text()
            md_content = md_path.read_text()

            # Key information should appear in both
            for key_info in [
                "Configuration Used",
                "custom configuration",
                "2 attributes",  # Custom weights count
                "dependency_freshness",  # Excluded attribute
                "dark",  # Theme
            ]:
                assert key_info in html_content, f"Missing '{key_info}' in HTML"
                assert key_info in md_content, f"Missing '{key_info}' in Markdown"

        finally:
            html_path.unlink()
            md_path.unlink()

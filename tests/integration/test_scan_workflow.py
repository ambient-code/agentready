"""Integration tests for complete scan workflow."""

from pathlib import Path

from agentready.assessors.documentation import CLAUDEmdAssessor, READMEAssessor
from agentready.models.config import Config
from agentready.models.theme import Theme
from agentready.reporters.html import HTMLReporter
from agentready.reporters.markdown import MarkdownReporter
from agentready.services.scanner import Scanner


class TestScanWorkflow:
    """Test end-to-end scanning workflow."""

    def test_scan_current_repository(self):
        """Test scanning the agentready repository itself."""
        repo_path = Path(__file__).parent.parent.parent

        # Create scanner
        scanner = Scanner(repo_path, config=None)

        # Use minimal assessors for faster test
        assessors = [CLAUDEmdAssessor(), READMEAssessor()]

        # Run scan
        assessment = scanner.scan(assessors, verbose=False)

        # Verify assessment structure
        assert assessment.repository.name == "agentready"
        assert assessment.overall_score >= 0.0
        assert assessment.overall_score <= 100.0
        assert assessment.attributes_total == len(assessors)
        assert assessment.certification_level in [
            "Platinum",
            "Gold",
            "Silver",
            "Bronze",
            "Needs Improvement",
        ]

    def test_html_report_generation(self, tmp_path):
        """Test HTML report generation."""
        repo_path = Path(__file__).parent.parent.parent

        scanner = Scanner(repo_path, config=None)
        assessors = [CLAUDEmdAssessor()]
        assessment = scanner.scan(assessors, verbose=False)

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "test_report.html"
        result = reporter.generate(assessment, output_file)

        # Verify file was created
        assert result.exists()
        assert result.stat().st_size > 0

        # Verify HTML content
        with open(result, "r") as f:
            content = f.read()
            assert "AgentReady Assessment Report" in content
            assert assessment.repository.name in content

    def test_markdown_report_generation(self, tmp_path):
        """Test Markdown report generation."""
        repo_path = Path(__file__).parent.parent.parent

        scanner = Scanner(repo_path, config=None)
        assessors = [CLAUDEmdAssessor()]
        assessment = scanner.scan(assessors, verbose=False)

        # Generate Markdown report
        reporter = MarkdownReporter()
        output_file = tmp_path / "test_report.md"
        result = reporter.generate(assessment, output_file)

        # Verify file was created
        assert result.exists()
        assert result.stat().st_size > 0

        # Verify Markdown content
        with open(result, "r") as f:
            content = f.read()
            assert "# 🤖 AgentReady Assessment Report" in content
            assert "## 📊 Summary" in content
            assert assessment.repository.name in content

    def test_html_report_with_light_theme(self, tmp_path):
        """Test HTML report generation with light theme."""
        repo_path = Path(__file__).parent.parent.parent

        # Create config with light theme
        config = Config(
            weights={},
            excluded_attributes=[],
            language_overrides={},
            output_dir=None,
            report_theme="light",
        )

        scanner = Scanner(repo_path, config=config)
        assessors = [CLAUDEmdAssessor()]
        assessment = scanner.scan(assessors, verbose=False)

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "test_report_light.html"
        result = reporter.generate(assessment, output_file)

        # Verify file was created
        assert result.exists()

        # Verify light theme is applied
        with open(result, "r") as f:
            content = f.read()
            assert 'data-theme="light"' in content
            assert "#f8fafc" in content  # Light background color

    def test_html_report_with_dark_theme(self, tmp_path):
        """Test HTML report generation with dark theme."""
        repo_path = Path(__file__).parent.parent.parent

        # Create config with dark theme
        config = Config(
            weights={},
            excluded_attributes=[],
            language_overrides={},
            output_dir=None,
            report_theme="dark",
        )

        scanner = Scanner(repo_path, config=config)
        assessors = [CLAUDEmdAssessor()]
        assessment = scanner.scan(assessors, verbose=False)

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "test_report_dark.html"
        result = reporter.generate(assessment, output_file)

        # Verify file was created
        assert result.exists()

        # Verify dark theme is applied
        with open(result, "r") as f:
            content = f.read()
            assert 'data-theme="dark"' in content
            assert "#0f172a" in content  # Dark background color

    def test_html_report_with_custom_theme(self, tmp_path):
        """Test HTML report generation with custom theme."""
        repo_path = Path(__file__).parent.parent.parent

        # Create config with custom theme
        custom_colors = {
            "background": "#1a1a2e",
            "surface": "#16213e",
            "surface_elevated": "#0f3460",
            "primary": "#e94560",
            "primary_light": "#ff6b6b",
            "primary_dark": "#c72c41",
            "text_primary": "#eaeaea",
            "text_secondary": "#d4d4d4",
            "text_muted": "#a0a0a0",
            "success": "#4ecca3",
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "neutral": "#95a5a6",
            "border": "#34495e",
            "shadow": "rgba(0, 0, 0, 0.6)",
        }

        config = Config(
            weights={},
            excluded_attributes=[],
            language_overrides={},
            output_dir=None,
            custom_theme=custom_colors,
        )

        scanner = Scanner(repo_path, config=config)
        assessors = [CLAUDEmdAssessor()]
        assessment = scanner.scan(assessors, verbose=False)

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "test_report_custom.html"
        result = reporter.generate(assessment, output_file)

        # Verify file was created
        assert result.exists()

        # Verify custom colors are applied
        with open(result, "r") as f:
            content = f.read()
            assert "#1a1a2e" in content  # Custom background
            assert "#e94560" in content  # Custom primary

    def test_html_report_theme_switcher_present(self, tmp_path):
        """Test HTML report includes theme switcher."""
        repo_path = Path(__file__).parent.parent.parent

        scanner = Scanner(repo_path, config=None)
        assessors = [CLAUDEmdAssessor()]
        assessment = scanner.scan(assessors, verbose=False)

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "test_report_switcher.html"
        result = reporter.generate(assessment, output_file)

        # Verify theme switcher elements are present
        with open(result, "r") as f:
            content = f.read()
            assert 'id="theme-select"' in content
            assert "Theme:" in content
            assert "const THEMES = " in content
            assert "applyTheme" in content
            assert "localStorage" in content

    def test_html_report_all_themes_embedded(self, tmp_path):
        """Test HTML report embeds all available themes."""
        repo_path = Path(__file__).parent.parent.parent

        scanner = Scanner(repo_path, config=None)
        assessors = [CLAUDEmdAssessor()]
        assessment = scanner.scan(assessors, verbose=False)

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "test_report_themes.html"
        result = reporter.generate(assessment, output_file)

        # Verify all themes are embedded
        with open(result, "r") as f:
            content = f.read()
            for theme_name in Theme.get_available_themes():
                assert theme_name in content

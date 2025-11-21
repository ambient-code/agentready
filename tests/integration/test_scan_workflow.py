"""Integration tests for complete scan workflow."""

from pathlib import Path


from agentready.assessors.documentation import CLAUDEmdAssessor, READMEAssessor
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

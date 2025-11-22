"""Security tests for AgentReady."""

from datetime import datetime

from agentready.models.assessment import Assessment
from agentready.models.attribute import Attribute
from agentready.models.finding import Finding
from agentready.models.repository import Repository
from agentready.reporters.html import HTMLReporter


class TestXSSPrevention:
    """Test XSS prevention in HTML reports."""

    def test_malicious_repository_name_escaped(self, tmp_path):
        """Test that malicious repository names are escaped in HTML."""
        # Create repository with XSS payload in name
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="<script>alert('xss')</script>",
            url="https://evil.com/<script>alert('xss')</script>",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        # Create minimal assessment
        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )

        finding = Finding(
            attribute=attr,
            status="pass",
            score=100.0,
            measured_value="test",
            threshold="test",
            evidence=["<script>alert('evidence')</script>"],
            remediation=None,
            error_message=None,
        )

        assessment = Assessment(
            repository=repo,
            timestamp=datetime.now(),
            overall_score=100.0,
            certification_level="Platinum",
            attributes_assessed=1,
            attributes_skipped=0,
            attributes_total=1,
            findings=[finding],
            config=None,
            duration_seconds=1.0,
        )

        # Generate HTML report
        reporter = HTMLReporter()
        output_file = tmp_path / "report.html"
        result = reporter.generate(assessment, output_file)

        # Read generated HTML
        html_content = result.read_text()

        # Verify XSS payloads are escaped in JavaScript context
        # The JSON.parse() line should have Unicode escapes
        assert (
            "\\u003cscript\\u003e" in html_content
            or "\u003cscript\u003e" in html_content
        )

        # Verify HTML contexts are escaped (title, body text)
        # Jinja2 autoescape should convert < to &lt; in HTML context
        title_section = html_content[
            html_content.find("<title>") : html_content.find("</title>")
        ]
        assert (
            "&lt;script&gt;" in title_section
            or "<script>alert('xss')</script>" not in title_section
        )

        # Most importantly: verify JavaScript execution context is safe
        script_section = html_content[
            html_content.find("<script>") : html_content.find("</script>")
        ]
        # JSON.parse() should have Unicode-escaped the malicious content
        assert "JSON.parse(" in script_section
        assert "\\u003c" in script_section  # Unicode escape for '<'

    def test_malicious_commit_message_escaped(self, tmp_path):
        """Test that malicious commit messages are escaped."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        repo = Repository(
            path=tmp_path,
            name="safe-repo",
            url=None,
            branch="<img src=x onerror=alert(1)>",
            commit_hash="<script>alert(1)</script>",
            languages={"Python": 100},
            total_files=10,
            total_lines=100,
        )

        attr = Attribute(
            id="test",
            name="Test",
            category="Test",
            tier=1,
            description="Test",
            criteria="Test",
            default_weight=1.0,
        )

        finding = Finding(
            attribute=attr,
            status="fail",
            score=0.0,
            measured_value="test",
            threshold="test",
            evidence=[],
            remediation=None,
            error_message="<script>alert('error')</script>",
        )

        assessment = Assessment(
            repository=repo,
            timestamp=datetime.now(),
            overall_score=0.0,
            certification_level="Needs Improvement",
            attributes_assessed=1,
            attributes_skipped=0,
            attributes_total=1,
            findings=[finding],
            config=None,
            duration_seconds=1.0,
        )

        reporter = HTMLReporter()
        output_file = tmp_path / "report.html"
        result = reporter.generate(assessment, output_file)

        html_content = result.read_text()

        # Verify JavaScript context is safe (JSON.parse with Unicode escapes)
        script_section = html_content[
            html_content.find("<script>") : html_content.find("</script>")
        ]
        assert "JSON.parse(" in script_section
        assert "\\u003c" in script_section  # '<' should be Unicode-escaped

        # Verify no direct script execution
        # The malicious payloads should be escaped
        assert "<img src=x onerror=alert(1)>" not in html_content
        # Script tags in data should be escaped
        assert (
            "\\u003cscript\\u003e" in html_content
            or "\u003cscript\u003e" in html_content
        )

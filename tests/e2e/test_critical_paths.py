"""E2E tests for critical user journeys.

These tests run the actual CLI commands and verify core functionality.
They MUST pass for any PR to be merged.

Characteristics:
- No mocking (tests real execution)
- Fast (<1 minute total)
- Platform-agnostic
- Test primary user journeys
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

# Configurable timeout for subprocess tests (default: 90s)
# Can be overridden via AGENTREADY_TEST_TIMEOUT environment variable
DEFAULT_TIMEOUT = int(os.getenv("AGENTREADY_TEST_TIMEOUT", "90"))


class TestCriticalAssessmentFlow:
    """Test the primary assessment workflow end-to-end."""

    def test_assess_current_repository(self):
        """E2E: Assess AgentReady repository itself.

        This is the most common usage pattern - users running
        'agentready assess .' in their repository.
        """
        # Use temp directory for output to avoid conflicts
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"

            # Run assessment on current repository
            result = subprocess.run(
                ["agentready", "assess", ".", "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )

            # Verify success
            assert result.returncode == 0, f"Assessment failed: {result.stderr}"
            assert "Assessment complete" in result.stdout

            # Verify required output indicators
            assert "Score:" in result.stdout
            assert "Assessed:" in result.stdout
            assert "Reports generated:" in result.stdout

    def test_assess_generates_all_output_files(self):
        """E2E: Verify all expected output files are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"

            # Run assessment
            result = subprocess.run(
                ["agentready", "assess", ".", "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )

            assert result.returncode == 0

            # Verify timestamped files exist
            json_files = list(output_dir.glob("assessment-*.json"))
            html_files = list(output_dir.glob("report-*.html"))
            md_files = list(output_dir.glob("report-*.md"))

            assert len(json_files) >= 1, "No JSON assessment files created"
            assert len(html_files) >= 1, "No HTML report files created"
            assert len(md_files) >= 1, "No Markdown report files created"

            # Verify latest symlinks exist
            assert (output_dir / "assessment-latest.json").exists()
            assert (output_dir / "report-latest.html").exists()
            assert (output_dir / "report-latest.md").exists()

    def test_assess_json_output_is_valid(self):
        """E2E: Verify JSON output structure and completeness."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"

            # Run assessment
            result = subprocess.run(
                ["agentready", "assess", ".", "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )

            assert result.returncode == 0

            # Load and validate JSON
            json_file = output_dir / "assessment-latest.json"
            with open(json_file) as f:
                data = json.load(f)

            # Verify required top-level fields
            required_fields = [
                "overall_score",
                "certification_level",
                "attributes_assessed",
                "attributes_total",
                "findings",
                "timestamp",
                "schema_version",
                "metadata",
            ]

            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Verify metadata contains version info
            assert "agentready_version" in data["metadata"]

            # Verify overall_score is valid
            assert isinstance(data["overall_score"], (int, float))
            assert 0 <= data["overall_score"] <= 100

            # Verify certification_level is valid
            valid_levels = [
                "Platinum",
                "Gold",
                "Silver",
                "Bronze",
                "Needs Improvement",
            ]
            assert data["certification_level"] in valid_levels

            # Verify findings array
            assert isinstance(data["findings"], list)
            assert len(data["findings"]) > 0, "No findings in assessment"

            # Verify each finding has required fields
            finding = data["findings"][0]
            required_finding_fields = ["attribute", "status", "score"]
            for field in required_finding_fields:
                assert field in finding, f"Finding missing field: {field}"

    def test_assess_html_report_generated(self):
        """E2E: Verify HTML report is generated and non-empty."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"

            # Run assessment
            result = subprocess.run(
                ["agentready", "assess", ".", "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )

            assert result.returncode == 0

            # Verify HTML report exists and has content
            html_file = output_dir / "report-latest.html"
            html_content = html_file.read_text()

            assert len(html_content) > 1000, "HTML report is suspiciously small"
            assert "<html" in html_content
            assert "AgentReady" in html_content
            assert "Overall Score" in html_content or "overall" in html_content.lower()

    def test_assess_markdown_report_generated(self):
        """E2E: Verify Markdown report is generated and non-empty."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"

            # Run assessment
            result = subprocess.run(
                ["agentready", "assess", ".", "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )

            assert result.returncode == 0

            # Verify Markdown report exists and has content
            md_file = output_dir / "report-latest.md"
            md_content = md_file.read_text()

            assert len(md_content) > 500, "Markdown report is suspiciously small"
            assert "#" in md_content, "No markdown headers"
            assert "Score" in md_content or "score" in md_content


class TestCriticalCLICommands:
    """Test critical CLI commands work correctly."""

    def test_help_command(self):
        """E2E: Verify help command works."""
        result = subprocess.run(
            ["agentready", "--help"], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "AgentReady" in result.stdout
        assert "assess" in result.stdout

    def test_version_command(self):
        """E2E: Verify version command works."""
        result = subprocess.run(
            ["agentready", "--version"], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "AgentReady" in result.stdout
        # Should show version number (format: X.Y.Z or "unknown")
        assert (
            any(char.isdigit() for char in result.stdout)
            or "unknown" in result.stdout.lower()
        )

    def test_research_version_command(self):
        """E2E: Verify research-version command works."""
        result = subprocess.run(
            ["agentready", "research-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Research Report Version:" in result.stdout
        assert "Attributes:" in result.stdout


class TestCriticalErrorHandling:
    """Test critical error cases are handled gracefully."""

    def test_assess_nonexistent_directory(self):
        """E2E: Verify graceful failure for nonexistent directory."""
        result = subprocess.run(
            ["agentready", "assess", "/nonexistent/directory/that/does/not/exist"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail gracefully
        assert result.returncode != 0
        # Should show helpful error message (not crash)
        assert len(result.stderr) > 0 or len(result.stdout) > 0

    def test_assess_invalid_config(self):
        """E2E: Verify graceful failure for invalid config file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create invalid config file
            config_file = Path(tmp_dir) / "invalid.yaml"
            config_file.write_text("invalid: yaml: content: here: :::")

            result = subprocess.run(
                ["agentready", "assess", ".", "--config", str(config_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should fail gracefully
            assert result.returncode != 0
            # Should show error message (not crash)
            assert len(result.stderr) > 0 or len(result.stdout) > 0


class TestCriticalConfigHandling:
    """Test configuration loading works correctly."""

    def test_assess_with_valid_config(self):
        """E2E: Verify assessment works with valid config file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create valid config file
            # Note: Use a valid attribute ID (openapi_specs) for excluded_attributes
            config_file = Path(tmp_dir) / "config.yaml"
            config_file.write_text("""
weights:
  claude_md_file: 2.0
excluded_attributes:
  - openapi_specs
""")

            output_dir = Path(tmp_dir) / "output"

            result = subprocess.run(
                [
                    "agentready",
                    "assess",
                    ".",
                    "--config",
                    str(config_file),
                    "--output-dir",
                    str(output_dir),
                ],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT,
            )

            assert result.returncode == 0
            assert "Assessment complete" in result.stdout

            # Verify config was applied (openapi_specs should be excluded)
            json_file = output_dir / "assessment-latest.json"
            with open(json_file) as f:
                data = json.load(f)

            # Check that openapi_specs is not in findings
            finding_ids = [f["attribute"]["id"] for f in data["findings"]]
            assert "openapi_specs" not in finding_ids


class TestCriticalSecurityFeatures:
    """Test critical security features work end-to-end."""

    def test_assess_blocks_sensitive_directories(self):
        """E2E: Verify sensitive directory scanning is blocked.

        Critical security feature: AgentReady should warn users before
        scanning sensitive system directories and allow them to decline.
        """
        # Test with /etc directory (common sensitive directory)
        result = subprocess.run(
            ["agentready", "assess", "/etc"],
            capture_output=True,
            text=True,
            timeout=10,
            input="n\n",  # Decline to continue
        )

        # Should fail when user declines
        assert result.returncode != 0, "Should fail when user declines to scan /etc"

        # Should show warning message about sensitive directory
        output = result.stdout + result.stderr
        assert (
            "sensitive" in output.lower() or "warning" in output.lower()
        ), f"No warning about sensitive directory in output: {output[:500]}"

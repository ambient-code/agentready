"""E2E tests for critical user journeys - SIMPLIFIED VERSION.

These tests run the actual CLI commands and verify core functionality.
They MUST pass for any PR to be merged.

Characteristics:
- No mocking (tests real execution)
- Fast (<1 minute total)
- Platform-agnostic
- Test primary user journeys
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


class AssessmentTestHelper:
    """Helper class to reduce duplication in assessment tests."""

    @staticmethod
    def run_assessment(
        output_dir: Path, extra_args: list = None
    ) -> subprocess.CompletedProcess:
        """Run assessment command with standard configuration."""
        cmd = ["agentready", "assess", ".", "--output-dir", str(output_dir)]
        if extra_args:
            cmd.extend(extra_args)

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

    @staticmethod
    def verify_output_files(output_dir: Path):
        """Verify all expected output files exist."""
        # Check timestamped files
        for pattern, name in [
            ("assessment-*.json", "JSON assessment"),
            ("report-*.html", "HTML report"),
            ("report-*.md", "Markdown report"),
        ]:
            files = list(output_dir.glob(pattern))
            assert len(files) >= 1, f"No {name} files created"

        # Check symlinks
        for filename in [
            "assessment-latest.json",
            "report-latest.html",
            "report-latest.md",
        ]:
            assert (output_dir / filename).exists(), f"{filename} not created"

    @staticmethod
    def load_assessment_json(output_dir: Path) -> dict:
        """Load and return the latest assessment JSON."""
        with open(output_dir / "assessment-latest.json") as f:
            return json.load(f)


@pytest.fixture
def temp_output_dir():
    """Fixture providing a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir) / "output"


class TestCriticalAssessmentFlow:
    """Test the primary assessment workflow end-to-end."""

    def test_complete_assessment_workflow(self, temp_output_dir):
        """E2E: Complete assessment workflow with all validations.

        Combines multiple related tests into one comprehensive test
        to reduce redundancy while maintaining full coverage.
        """
        helper = AssessmentTestHelper()

        # Run assessment
        result = helper.run_assessment(temp_output_dir)

        # Verify success
        assert result.returncode == 0, f"Assessment failed: {result.stderr}"
        assert "Assessment complete" in result.stdout

        # Verify console output indicators
        required_output = ["Score:", "Assessed:", "Reports generated:"]
        for indicator in required_output:
            assert indicator in result.stdout, f"Missing output indicator: {indicator}"

        # Verify all files generated
        helper.verify_output_files(temp_output_dir)

        # Verify JSON structure and content
        data = helper.load_assessment_json(temp_output_dir)
        self._validate_json_structure(data)

        # Verify HTML report
        html_content = (temp_output_dir / "report-latest.html").read_text()
        assert len(html_content) > 1000, "HTML report too small"
        assert all(text in html_content for text in ["<html", "AgentReady"])

        # Verify Markdown report
        md_content = (temp_output_dir / "report-latest.md").read_text()
        assert len(md_content) > 500, "Markdown report too small"
        assert "#" in md_content, "No markdown headers"

    def _validate_json_structure(self, data: dict):
        """Validate JSON assessment structure."""
        # Check required fields
        required_fields = {
            "overall_score": lambda v: isinstance(v, (int, float)) and 0 <= v <= 100,
            "certification_level": lambda v: v
            in ["Platinum", "Gold", "Silver", "Bronze", "Needs Improvement"],
            "attributes_assessed": lambda v: isinstance(v, int),
            "attributes_total": lambda v: isinstance(v, int),
            "findings": lambda v: isinstance(v, list) and len(v) > 0,
            "timestamp": lambda v: v is not None,
            "schema_version": lambda v: v is not None,
            "metadata": lambda v: isinstance(v, dict) and "agentready_version" in v,
        }

        for field, validator in required_fields.items():
            assert field in data, f"Missing required field: {field}"
            assert validator(data[field]), f"Invalid value for field: {field}"

        # Validate findings structure
        if data["findings"]:
            finding = data["findings"][0]
            for field in ["attribute", "status", "score"]:
                assert field in finding, f"Finding missing field: {field}"


class TestCriticalCLICommands:
    """Test critical CLI commands work correctly."""

    @pytest.mark.parametrize(
        "command,expected_output",
        [
            (["--help"], ["AgentReady", "assess"]),
            (["--version"], ["AgentReady"]),
            (["research-version"], ["Research Report Version:", "Attributes:"]),
        ],
    )
    def test_cli_commands(self, command, expected_output):
        """E2E: Verify CLI commands work correctly."""
        result = subprocess.run(
            ["agentready"] + command, capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        for expected in expected_output:
            assert expected in result.stdout

        # Special check for version command
        if "--version" in command:
            assert (
                any(char.isdigit() for char in result.stdout)
                or "unknown" in result.stdout.lower()
            )


class TestCriticalErrorHandling:
    """Test critical error cases are handled gracefully."""

    def test_error_handling(self):
        """E2E: Verify graceful failure for various error conditions."""
        test_cases = [
            # Nonexistent directory
            (
                ["agentready", "assess", "/nonexistent/directory/that/does/not/exist"],
                "Should fail for nonexistent directory",
            ),
        ]

        for command, description in test_cases:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)

            # Should fail gracefully
            assert (
                result.returncode != 0
            ), f"{description}: should have non-zero exit code"
            # Should show error message (not crash)
            assert (
                len(result.stderr) > 0 or len(result.stdout) > 0
            ), f"{description}: no error output"

    def test_invalid_config_handling(self, temp_output_dir):
        """E2E: Verify graceful failure for invalid config file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create invalid config
            config_file = Path(tmp_dir) / "invalid.yaml"
            config_file.write_text("invalid: yaml: content: here: :::")

            result = subprocess.run(
                ["agentready", "assess", ".", "--config", str(config_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert result.returncode != 0
            assert len(result.stderr) > 0 or len(result.stdout) > 0


class TestCriticalConfigHandling:
    """Test configuration loading works correctly."""

    def test_valid_config_application(self, temp_output_dir):
        """E2E: Verify assessment works with valid config file."""
        helper = AssessmentTestHelper()

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create valid config
            config_file = Path(tmp_dir) / "config.yaml"
            config_file.write_text("""
weights:
  claude_md: 2.0
excluded_attributes:
  - repomix_config
""")

            # Run assessment with config
            result = helper.run_assessment(
                temp_output_dir, extra_args=["--config", str(config_file)]
            )

            assert result.returncode == 0
            assert "Assessment complete" in result.stdout

            # Verify config was applied
            data = helper.load_assessment_json(temp_output_dir)
            finding_ids = [f["attribute"]["id"] for f in data["findings"]]
            assert (
                "repomix_config" not in finding_ids
            ), "Excluded attribute should not be in findings"

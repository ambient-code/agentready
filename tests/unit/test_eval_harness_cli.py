"""Unit tests for eval harness CLI commands.

Note: These tests focus on CLI structure and argument handling.
Service-level testing is handled in test_eval_harness_services.py.
"""

import pytest
from click.testing import CliRunner

from agentready.cli.eval_harness import eval_harness


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


class TestEvalHarnessGroup:
    """Test eval-harness command group."""

    def test_eval_harness_help(self, runner):
        """Test eval-harness command group help."""
        result = runner.invoke(eval_harness, ["--help"])

        # Should show help
        assert result.exit_code == 0
        assert "baseline" in result.output
        assert "test-assessor" in result.output
        assert "run-tier" in result.output
        assert "summarize" in result.output
        assert "dashboard" in result.output

    def test_baseline_help(self, runner):
        """Test baseline subcommand help."""
        result = runner.invoke(eval_harness, ["baseline", "--help"])

        # Should show baseline help
        assert result.exit_code == 0
        assert "Establish baseline" in result.output
        assert "--iterations" in result.output

    def test_test_assessor_help(self, runner):
        """Test test-assessor subcommand help."""
        result = runner.invoke(eval_harness, ["test-assessor", "--help"])

        # Should show test-assessor help
        assert result.exit_code == 0
        assert "--assessor-id" in result.output
        assert "--iterations" in result.output

    def test_run_tier_help(self, runner):
        """Test run-tier subcommand help."""
        result = runner.invoke(eval_harness, ["run-tier", "--help"])

        # Should show run-tier help
        assert result.exit_code == 0
        assert "--tier" in result.output
        assert "--iterations" in result.output

    def test_summarize_help(self, runner):
        """Test summarize subcommand help."""
        result = runner.invoke(eval_harness, ["summarize", "--help"])

        # Should show summarize help
        assert result.exit_code == 0
        assert "Aggregate and display" in result.output

    def test_dashboard_help(self, runner):
        """Test dashboard subcommand help."""
        result = runner.invoke(eval_harness, ["dashboard", "--help"])

        # Should show dashboard help
        assert result.exit_code == 0
        assert "Generate dashboard" in result.output
        assert "--docs-dir" in result.output

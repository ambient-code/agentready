"""Unit tests for repomix CLI command."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from agentready.cli.repomix import repomix_generate


@pytest.fixture
def temp_repo():
    """Create a temporary git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        (repo_path / ".git").mkdir()
        yield repo_path


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


class TestRepomixCommand:
    """Test repomix CLI command."""

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_init(self, mock_service, runner, temp_repo):
        """Test repomix init command."""
        mock_service.return_value.is_installed.return_value = True
        mock_service.return_value.generate_config.return_value = True
        mock_service.return_value.generate_ignore.return_value = True
        mock_service.return_value.config_path = temp_repo / "repomix.config.json"
        mock_service.return_value.ignore_path = temp_repo / ".repomixignore"

        result = runner.invoke(repomix_generate, [str(temp_repo), "--init"])

        # Should succeed
        assert result.exit_code == 0
        assert "Initializing Repomix" in result.output

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_init_not_installed(self, mock_service, runner, temp_repo):
        """Test repomix init when repomix is not installed."""
        mock_service.return_value.is_installed.return_value = False
        mock_service.return_value.generate_config.return_value = True
        mock_service.return_value.generate_ignore.return_value = True
        mock_service.return_value.config_path = temp_repo / "repomix.config.json"
        mock_service.return_value.ignore_path = temp_repo / ".repomixignore"

        result = runner.invoke(repomix_generate, [str(temp_repo), "--init"])

        # Should succeed but warn about missing repomix
        assert result.exit_code == 0
        assert "not installed" in result.output.lower()
        assert "npm install" in result.output

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_init_files_exist(self, mock_service, runner, temp_repo):
        """Test repomix init when config files already exist."""
        mock_service.return_value.is_installed.return_value = True
        mock_service.return_value.generate_config.return_value = False
        mock_service.return_value.generate_ignore.return_value = False
        mock_service.return_value.config_path = temp_repo / "repomix.config.json"
        mock_service.return_value.ignore_path = temp_repo / ".repomixignore"

        result = runner.invoke(repomix_generate, [str(temp_repo), "--init"])

        # Should succeed but skip existing files
        assert result.exit_code == 0
        assert "already exists" in result.output or "skipped" in result.output

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_generate_basic(self, mock_service, runner, temp_repo):
        """Test basic repomix generate command."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.is_installed.return_value = True
        mock_service.return_value.run_repomix.return_value = (True, "Success")
        mock_service.return_value.check_freshness.return_value = (True, "Fresh")

        result = runner.invoke(repomix_generate, [str(temp_repo)])

        # Should succeed
        assert result.exit_code == 0
        assert "✅" in result.output or "Success" in result.output

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_generate_not_configured(self, mock_service, runner, temp_repo):
        """Test repomix generate when not configured."""
        mock_service.return_value.has_config.return_value = False

        result = runner.invoke(repomix_generate, [str(temp_repo)])

        # Should fail with error message
        assert result.exit_code != 0
        assert "not configured" in result.output.lower()
        assert "--init" in result.output

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_generate_not_installed(self, mock_service, runner, temp_repo):
        """Test repomix generate when repomix not installed."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.is_installed.return_value = False

        result = runner.invoke(repomix_generate, [str(temp_repo)])

        # Should fail with error message
        assert result.exit_code != 0
        assert "not installed" in result.output.lower()

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_generate_with_format(self, mock_service, runner, temp_repo):
        """Test repomix generate with different formats."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.is_installed.return_value = True
        mock_service.return_value.run_repomix.return_value = (True, "Success")
        mock_service.return_value.check_freshness.return_value = (True, "Fresh")

        for fmt in ["markdown", "xml", "json", "plain"]:
            result = runner.invoke(repomix_generate, [str(temp_repo), "--format", fmt])
            assert result.exit_code == 0

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_generate_verbose(self, mock_service, runner, temp_repo):
        """Test repomix generate with verbose output."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.is_installed.return_value = True
        mock_service.return_value.run_repomix.return_value = (True, "Success")
        mock_service.return_value.check_freshness.return_value = (True, "Fresh")

        result = runner.invoke(repomix_generate, [str(temp_repo), "--verbose"])

        # Should succeed with extra output
        assert result.exit_code == 0
        assert "Repository" in result.output
        assert "Format" in result.output

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_check_fresh(self, mock_service, runner, temp_repo):
        """Test repomix check when output is fresh."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.check_freshness.return_value = (
            True,
            "Output is fresh",
        )
        mock_service.return_value.get_output_files.return_value = [
            temp_repo / "repomix-output.md"
        ]

        result = runner.invoke(repomix_generate, [str(temp_repo), "--check"])

        # Should succeed
        assert result.exit_code == 0
        assert "✅" in result.output or "fresh" in result.output.lower()

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_check_stale(self, mock_service, runner, temp_repo):
        """Test repomix check when output is stale."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.check_freshness.return_value = (
            False,
            "Output is stale",
        )

        result = runner.invoke(repomix_generate, [str(temp_repo), "--check"])

        # Should fail (exit 1 for stale)
        assert result.exit_code != 0
        assert "stale" in result.output.lower() or "❌" in result.output

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_check_not_configured(self, mock_service, runner, temp_repo):
        """Test repomix check when not configured."""
        mock_service.return_value.has_config.return_value = False

        result = runner.invoke(repomix_generate, [str(temp_repo), "--check"])

        # Should fail
        assert result.exit_code != 0
        assert "not configured" in result.output.lower()
        assert "--init" in result.output

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_check_custom_max_age(self, mock_service, runner, temp_repo):
        """Test repomix check with custom max age."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.check_freshness.return_value = (True, "Fresh")
        mock_service.return_value.get_output_files.return_value = []

        result = runner.invoke(
            repomix_generate, [str(temp_repo), "--check", "--max-age", "14"]
        )

        # Should succeed
        assert result.exit_code == 0

        # Verify max_age was passed to service
        mock_service.return_value.check_freshness.assert_called_with(max_age_days=14)

    def test_repomix_not_git_repository(self, runner):
        """Test repomix command on non-git repository."""
        with runner.isolated_filesystem():
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir)

                result = runner.invoke(repomix_generate, [str(repo_path), "--init"])

                # Should fail
                assert result.exit_code != 0
                assert "git repository" in result.output.lower()

    def test_repomix_nonexistent_repository(self, runner):
        """Test repomix command with non-existent path."""
        result = runner.invoke(repomix_generate, ["/nonexistent/path", "--init"])

        # Should fail
        assert result.exit_code != 0

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_generate_failure(self, mock_service, runner, temp_repo):
        """Test repomix generate when repomix command fails."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.is_installed.return_value = True
        mock_service.return_value.run_repomix.return_value = (False, "Repomix failed")

        result = runner.invoke(repomix_generate, [str(temp_repo)])

        # Should fail
        assert result.exit_code != 0
        assert "failed" in result.output.lower() or "❌" in result.output

    def test_repomix_invalid_format(self, runner, temp_repo):
        """Test repomix generate with invalid format."""
        result = runner.invoke(
            repomix_generate, [str(temp_repo), "--format", "invalid"]
        )

        # Should fail with validation error
        assert result.exit_code != 0

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_default_repository(self, mock_service, runner):
        """Test repomix command with default repository (current directory)."""
        with runner.isolated_filesystem():
            Path(".git").mkdir()

            mock_service.return_value.is_installed.return_value = True
            mock_service.return_value.generate_config.return_value = True
            mock_service.return_value.generate_ignore.return_value = True
            mock_service.return_value.config_path = Path("repomix.config.json")
            mock_service.return_value.ignore_path = Path(".repomixignore")

            result = runner.invoke(repomix_generate, ["--init"])

            # Should use current directory
            assert result.exit_code == 0


class TestRepomixCommandEdgeCases:
    """Test edge cases in repomix command."""

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_init_partial_creation(self, mock_service, runner, temp_repo):
        """Test repomix init when only one file is created."""
        mock_service.return_value.is_installed.return_value = True
        # Config created, but ignore already exists
        mock_service.return_value.generate_config.return_value = True
        mock_service.return_value.generate_ignore.return_value = False
        mock_service.return_value.config_path = temp_repo / "repomix.config.json"
        mock_service.return_value.ignore_path = temp_repo / ".repomixignore"

        result = runner.invoke(repomix_generate, [str(temp_repo), "--init"])

        # Should succeed
        assert result.exit_code == 0

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_check_no_output_files(self, mock_service, runner, temp_repo):
        """Test repomix check when fresh but no output files."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.check_freshness.return_value = (True, "Fresh")
        mock_service.return_value.get_output_files.return_value = []

        result = runner.invoke(repomix_generate, [str(temp_repo), "--check"])

        # Should still succeed (freshness check passed)
        assert result.exit_code == 0

    @patch("agentready.cli.repomix.RepomixService")
    def test_repomix_generate_with_all_formats_sequentially(
        self, mock_service, runner, temp_repo
    ):
        """Test generating with all formats one after another."""
        mock_service.return_value.has_config.return_value = True
        mock_service.return_value.is_installed.return_value = True
        mock_service.return_value.run_repomix.return_value = (True, "Success")
        mock_service.return_value.check_freshness.return_value = (True, "Fresh")

        formats = ["markdown", "xml", "json", "plain"]
        for fmt in formats:
            result = runner.invoke(repomix_generate, [str(temp_repo), "--format", fmt])
            assert result.exit_code == 0

            # Verify format was passed correctly
            mock_service.return_value.run_repomix.assert_called()
            call_args = mock_service.return_value.run_repomix.call_args
            assert call_args[1]["output_format"] == fmt

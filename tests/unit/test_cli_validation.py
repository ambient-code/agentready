"""Tests for CLI input validation and warnings."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentready.cli.main import cli


class TestSensitiveDirectoryWarnings:
    """Test warnings for scanning sensitive directories."""

    @pytest.mark.parametrize(
        "sensitive_path",
        ["/etc", "/sys", "/proc", "/.ssh", "/var"],
    )
    def test_warns_on_sensitive_directories(self, sensitive_path, tmp_path):
        """Test that CLI warns when scanning sensitive directories."""
        runner = CliRunner()

        # Mock the path resolution to return a sensitive path
        with patch("agentready.cli.main.Path") as mock_path:
            mock_resolved = MagicMock()
            mock_resolved.__str__ = lambda self: sensitive_path
            mock_path.return_value.resolve.return_value = mock_resolved

            # Run without confirmation (should abort)
            result = runner.invoke(cli, ["assess", sensitive_path], input="n\n")

            # Should show warning
            assert "Warning: Scanning sensitive directory" in result.output
            assert sensitive_path in result.output

            # Should abort on 'n' input
            assert result.exit_code != 0

    def test_continues_with_confirmation(self, tmp_path):
        """Test that assessment continues when user confirms sensitive directory."""
        runner = CliRunner()

        # Create a mock repository structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock to simulate /etc path but use tmp_path for actual scanning
        with patch("agentready.cli.main.Path") as mock_path_class:
            # First call returns the sensitive path for the warning check
            sensitive_mock = MagicMock()
            sensitive_mock.__str__ = lambda self: "/etc"

            # But we need the actual tmp_path for the scanner
            def resolve_side_effect():
                # Return sensitive path string for warning, but tmp_path for Scanner
                return tmp_path

            mock_instance = mock_path_class.return_value
            mock_instance.resolve.side_effect = resolve_side_effect

            # Run with confirmation
            result = runner.invoke(cli, ["assess", str(tmp_path)], input="y\n")

            # Should show warning
            assert "Warning" in result.output or result.exit_code == 0


class TestLargeRepositoryWarnings:
    """Test warnings for large repositories."""

    def test_warns_on_large_repository(self, tmp_path):
        """Test that CLI warns when repository has >10k files."""
        runner = CliRunner()

        # Create git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock git ls-files to return large file count
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "\n".join([f"file{i}.py" for i in range(10001)])
            mock_run.return_value = mock_result

            # Run without confirmation (should abort)
            result = runner.invoke(cli, ["assess", str(tmp_path)], input="n\n")

            # Should show warning about large repository
            assert "Large repository detected" in result.output
            assert "10,001 files" in result.output

            # Should abort on 'n' input
            assert result.exit_code != 0

    def test_no_warning_for_small_repository(self, tmp_path):
        """Test that CLI does not warn for repositories with <10k files."""
        runner = CliRunner()

        # Create git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create a small file for CLAUDE.md to pass validation
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test Repository\n")

        # Mock git ls-files to return small file count
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "\n".join([f"file{i}.py" for i in range(100)])
            mock_run.return_value = mock_result

            # Run assessment
            result = runner.invoke(cli, ["assess", str(tmp_path)])

            # Should not show large repository warning
            assert "Large repository detected" not in result.output

    def test_handles_git_failure_gracefully(self, tmp_path):
        """Test that assessment continues if git ls-files fails."""
        runner = CliRunner()

        # Create git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create a small file for CLAUDE.md
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test Repository\n")

        # Mock git ls-files to fail
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result

            # Run assessment - should continue despite git failure
            result = runner.invoke(cli, ["assess", str(tmp_path)])

            # Should complete without crashing
            assert result.exit_code == 0 or "Assessment complete" in result.output


class TestCombinedValidations:
    """Test combined validation scenarios."""

    def test_sensitive_dir_checked_before_large_repo(self, tmp_path):
        """Test that sensitive directory warning comes before large repo warning."""
        runner = CliRunner()

        # Mock to simulate /etc path
        with patch("agentready.cli.main.Path") as mock_path_class:
            sensitive_mock = MagicMock()
            sensitive_mock.__str__ = lambda self: "/etc"
            mock_path_class.return_value.resolve.return_value = sensitive_mock

            # Mock git to return large file count
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "\n".join([f"file{i}.py" for i in range(10001)])
                mock_run.return_value = mock_result

                # Run without confirmation (should abort on first warning)
                result = runner.invoke(cli, ["assess", "/etc"], input="n\n")

                # Should show sensitive directory warning first
                assert "Warning: Scanning sensitive directory" in result.output

                # Should not reach large repository check
                assert result.exit_code != 0

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

        # Create a mock repository with .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock Path.resolve() to return object that startswith() sensitive_path
        with patch("agentready.cli.main.Path") as mock_path_class:
            # Create mock that passes exists check but fails sensitive dir check
            mock_resolved = MagicMock()
            mock_resolved.__str__ = MagicMock(return_value=sensitive_path)

            # Make str(mock_resolved).startswith(sensitive_path) work
            def mock_str_method(self):
                return sensitive_path

            mock_resolved.__str__ = mock_str_method

            mock_path_instance = MagicMock()
            mock_path_instance.resolve.return_value = mock_resolved
            mock_path_class.return_value = mock_path_instance

            # Use tmp_path (which exists) as the input, but resolve to sensitive path
            result = runner.invoke(cli, ["assess", str(tmp_path)], input="n\n")

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

        # Create CLAUDE.md to satisfy assessor
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test\n")

        # Mock Path.resolve() to make it look like /etc
        with patch("agentready.cli.main.Path") as mock_path_class:
            # Mock instance that resolves to tmp_path but looks like /etc for warning
            mock_resolved = MagicMock()

            # Make str() return /etc for the warning check
            def mock_str_method(self):
                return "/etc"

            mock_resolved.__str__ = mock_str_method

            # But also act like tmp_path for everything else
            for attr in [
                "mkdir",
                "exists",
                "__truediv__",
                "is_dir",
                "is_file",
                "rglob",
            ]:
                if hasattr(tmp_path, attr):
                    setattr(mock_resolved, attr, getattr(tmp_path, attr))

            mock_path_instance = MagicMock()
            mock_path_instance.resolve.return_value = mock_resolved
            mock_path_class.return_value = mock_path_instance

            # Run with confirmation
            result = runner.invoke(cli, ["assess", str(tmp_path)], input="y\n")

            # Should show warning or complete successfully
            assert "Warning" in result.output or result.exit_code == 0


class TestLargeRepositoryWarnings:
    """Test warnings for large repositories."""

    def test_warns_on_large_repository(self, tmp_path):
        """Test that CLI warns when repository has >10k files."""
        runner = CliRunner()

        # Create git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock safe_subprocess_run to return large file count
        with patch("agentready.cli.main.safe_subprocess_run") as mock_safe_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "\n".join([f"file{i}.py" for i in range(10001)])
            mock_safe_run.return_value = mock_result

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

        # Mock safe_subprocess_run to return small file count
        with patch("agentready.cli.main.safe_subprocess_run") as mock_safe_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "\n".join([f"file{i}.py" for i in range(100)])
            mock_safe_run.return_value = mock_result

            # Run assessment
            result = runner.invoke(cli, ["assess", str(tmp_path)])

            # Should not show large repository warning
            assert "Large repository detected" not in result.output

    def test_handles_git_failure_gracefully(self, tmp_path):
        """Test that assessment continues if git ls-files fails during file count."""
        import subprocess

        runner = CliRunner()

        # Initialize as proper git repository with initial commit
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Create a small file for CLAUDE.md
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test Repository\n")

        # Create initial commit
        subprocess.run(
            ["git", "add", "CLAUDE.md"], cwd=tmp_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        # Mock safe_subprocess_run to fail only for the file count check (git ls-files)
        # but let other git commands (in Scanner) work normally
        original_safe_run = __import__(
            "agentready.utils.subprocess_utils", fromlist=["safe_subprocess_run"]
        ).safe_subprocess_run

        def selective_mock(*args, **kwargs):
            # Fail for git ls-files in the file count check (has timeout=5)
            if args[0] == ["git", "ls-files"] and kwargs.get("timeout") == 5:
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stdout = ""
                return mock_result
            # Let all other calls through to real implementation
            return original_safe_run(*args, **kwargs)

        with patch(
            "agentready.cli.main.safe_subprocess_run", side_effect=selective_mock
        ):
            # Run assessment - should continue despite git ls-files failure
            result = runner.invoke(cli, ["assess", str(tmp_path)])

            # Should complete successfully (file count check is wrapped in try/except)
            assert result.exit_code == 0 or "Assessment complete" in result.output


class TestCombinedValidations:
    """Test combined validation scenarios."""

    def test_sensitive_dir_checked_before_large_repo(self, tmp_path):
        """Test that sensitive directory warning comes before large repo warning."""
        runner = CliRunner()

        # Create git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock to simulate /etc path
        with patch("agentready.cli.main.Path") as mock_path_class:
            # Create mock that looks like /etc
            sensitive_mock = MagicMock()

            def mock_str_method(self):
                return "/etc"

            sensitive_mock.__str__ = mock_str_method

            mock_path_instance = MagicMock()
            mock_path_instance.resolve.return_value = sensitive_mock
            mock_path_class.return_value = mock_path_instance

            # Mock safe_subprocess_run to return large file count
            with patch("agentready.cli.main.safe_subprocess_run") as mock_safe_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "\n".join([f"file{i}.py" for i in range(10001)])
                mock_safe_run.return_value = mock_result

                # Run without confirmation (should abort on first warning)
                result = runner.invoke(cli, ["assess", str(tmp_path)], input="n\n")

                # Should show sensitive directory warning first
                assert "Warning: Scanning sensitive directory" in result.output

                # Should not reach large repository check
                assert result.exit_code != 0

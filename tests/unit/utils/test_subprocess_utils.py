"""Unit tests for subprocess utilities."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentready.utils.subprocess_utils import (
    MAX_OUTPUT_SIZE,
    SUBPROCESS_TIMEOUT,
    SubprocessSecurityError,
    safe_subprocess_run,
    sanitize_subprocess_error,
    validate_repository_path,
)


class TestValidateRepositoryPath:
    """Test repository path validation."""

    def test_validate_valid_git_repository(self, tmp_path):
        """Test validation of valid git repository."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        result = validate_repository_path(repo)
        assert result == repo.resolve()

    def test_validate_git_file_worktree(self, tmp_path):
        """Test validation of git worktree (with .git file)."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").write_text("gitdir: /path/to/worktree")

        result = validate_repository_path(repo)
        assert result == repo.resolve()

    def test_validate_non_git_directory(self, tmp_path):
        """Test validation fails for non-git directory."""
        repo = tmp_path / "not-a-repo"
        repo.mkdir()

        with pytest.raises(SubprocessSecurityError, match="Not a git repository"):
            validate_repository_path(repo)

    def test_validate_forbidden_etc(self, tmp_path):
        """Test validation blocks /etc directory."""
        # Create a mock path that starts with /etc
        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value = Path("/etc/project")

            with pytest.raises(
                SubprocessSecurityError, match="Cannot access sensitive directory"
            ):
                validate_repository_path(Path("/etc/project"))

    def test_validate_forbidden_sys(self, tmp_path):
        """Test validation blocks /sys directory."""
        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value = Path("/sys/project")

            with pytest.raises(
                SubprocessSecurityError, match="Cannot access sensitive directory"
            ):
                validate_repository_path(Path("/sys/project"))

    def test_validate_forbidden_proc(self, tmp_path):
        """Test validation blocks /proc directory."""
        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value = Path("/proc/project")

            with pytest.raises(
                SubprocessSecurityError, match="Cannot access sensitive directory"
            ):
                validate_repository_path(Path("/proc/project"))

    def test_validate_forbidden_root_ssh(self, tmp_path):
        """Test validation blocks /.ssh directory."""
        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value = Path("/.ssh")

            with pytest.raises(
                SubprocessSecurityError, match="Cannot access sensitive directory"
            ):
                validate_repository_path(Path("/.ssh"))

    def test_validate_symlink_resolution(self, tmp_path):
        """Test that symlinks are resolved to actual path."""
        real_repo = tmp_path / "real-repo"
        real_repo.mkdir()
        (real_repo / ".git").mkdir()

        symlink = tmp_path / "symlink-repo"
        symlink.symlink_to(real_repo)

        result = validate_repository_path(symlink)
        assert result == real_repo.resolve()

    def test_validate_resolve_error(self, tmp_path):
        """Test handling of path resolution errors."""
        with patch.object(Path, "resolve", side_effect=OSError("Cannot resolve")):
            with pytest.raises(SubprocessSecurityError, match="Cannot resolve path"):
                validate_repository_path(Path("/nonexistent"))

    def test_validate_runtime_error(self, tmp_path):
        """Test handling of runtime errors during resolution."""
        with patch.object(Path, "resolve", side_effect=RuntimeError("Runtime issue")):
            with pytest.raises(SubprocessSecurityError, match="Cannot resolve path"):
                validate_repository_path(Path("/test"))


class TestSanitizeSubprocessError:
    """Test subprocess error sanitization."""

    def test_sanitize_basic_error(self):
        """Test basic error message sanitization."""
        error = Exception("Command failed")
        result = sanitize_subprocess_error(error)
        assert result == "Command failed"

    def test_sanitize_repo_path(self, tmp_path):
        """Test repository path redaction."""
        repo = tmp_path / "project"
        repo.mkdir()
        error = Exception(f"Error in {repo}/src/file.py")

        result = sanitize_subprocess_error(error, repo_path=repo)
        assert "<repo>" in result
        assert str(repo) not in result

    def test_sanitize_home_directory(self):
        """Test home directory redaction."""
        home = Path.home()
        error = Exception(f"Error in {home}/project")

        result = sanitize_subprocess_error(error)
        assert "<home>" in result
        assert str(home) not in result

    @patch("pathlib.Path.home")
    def test_sanitize_home_directory_error(self, mock_home):
        """Test home directory error handling."""
        mock_home.side_effect = RuntimeError("No home")
        error = Exception("Error occurred")

        # Should not crash
        result = sanitize_subprocess_error(error)
        assert result == "Error occurred"

    @patch("getpass.getuser")
    def test_sanitize_username_unix(self, mock_user):
        """Test username redaction in Unix paths."""
        mock_user.return_value = "testuser"
        error = Exception("Error in /home/testuser/project")

        result = sanitize_subprocess_error(error)
        assert "testuser" not in result or "/<user>/" in result

    @patch("getpass.getuser")
    def test_sanitize_username_windows(self, mock_user):
        """Test username redaction in Windows paths."""
        mock_user.return_value = "testuser"
        error = Exception("Error in C:\\Users\\testuser\\project")

        result = sanitize_subprocess_error(error)
        assert "testuser" not in result or "\\<user>\\" in result

    @patch("getpass.getuser")
    def test_sanitize_username_error(self, mock_user):
        """Test username error handling."""
        mock_user.side_effect = Exception("No username")
        error = Exception("Error occurred")

        # Should not crash
        result = sanitize_subprocess_error(error)
        assert result == "Error occurred"

    def test_sanitize_long_error(self):
        """Test long error message truncation."""
        long_message = "Error: " + ("x" * 1000)
        error = Exception(long_message)

        result = sanitize_subprocess_error(error)
        assert len(result) <= 550  # 500 + "... (truncated)"
        assert "truncated" in result

    def test_sanitize_combined_patterns(self, tmp_path):
        """Test multiple patterns in error message."""
        repo = tmp_path / "project"
        repo.mkdir()
        home = Path.home()
        error = Exception(f"Failed in {repo} and {home}")

        result = sanitize_subprocess_error(error, repo_path=repo)
        assert str(repo) not in result
        assert str(home) not in result


class TestSafeSubprocessRun:
    """Test safe subprocess execution."""

    def test_run_simple_command(self):
        """Test successful command execution."""
        result = safe_subprocess_run(["echo", "hello"], capture_output=True, text=True)

        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_run_failed_command(self):
        """Test failed command execution."""
        # Use 'false' command which always fails
        result = safe_subprocess_run(["false"])
        assert result.returncode != 0

    def test_run_with_custom_timeout(self):
        """Test command with custom timeout."""
        # Quick command should complete within short timeout
        result = safe_subprocess_run(
            ["echo", "test"],
            timeout=1,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_run_timeout_expired(self):
        """Test command timeout."""
        with pytest.raises(subprocess.TimeoutExpired):
            safe_subprocess_run(["sleep", "10"], timeout=0.1)

    def test_run_default_timeout(self):
        """Test default timeout is enforced."""
        # Verify default timeout constant exists
        assert SUBPROCESS_TIMEOUT == 120

        # Quick command should work with default timeout
        result = safe_subprocess_run(["echo", "test"], capture_output=True, text=True)
        assert result.returncode == 0

    def test_run_with_cwd(self, tmp_path):
        """Test command execution with working directory."""
        # Create a git repo
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        result = safe_subprocess_run(
            ["pwd"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert str(repo) in result.stdout

    def test_run_with_non_git_cwd(self, tmp_path):
        """Test command with non-git working directory."""
        # Non-git directory should work (validation is skipped)
        non_git = tmp_path / "non-git"
        non_git.mkdir()

        result = safe_subprocess_run(
            ["echo", "test"],
            cwd=non_git,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_run_shell_forbidden(self):
        """Test that shell=True is blocked."""
        with pytest.raises(SubprocessSecurityError, match="shell=True is forbidden"):
            safe_subprocess_run(["echo test"], shell=True)

    def test_run_output_size_limit_stdout(self):
        """Test stdout size limit enforcement."""
        # Create command that outputs too much data
        large_output = "x" * (MAX_OUTPUT_SIZE + 1000)

        with patch("subprocess.run") as mock_run:
            # Mock successful run with large output
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = large_output.encode()
            mock_result.stderr = b""
            mock_run.return_value = mock_result

            with pytest.raises(SubprocessSecurityError, match="output too large"):
                safe_subprocess_run(["echo", "test"], capture_output=True)

    def test_run_output_size_limit_stderr(self):
        """Test stderr size limit enforcement."""
        large_error = "x" * (MAX_OUTPUT_SIZE + 1000)

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = b""
            mock_result.stderr = large_error.encode()
            mock_run.return_value = mock_result

            with pytest.raises(SubprocessSecurityError, match="stderr too large"):
                safe_subprocess_run(["cmd"], capture_output=True)

    def test_run_output_size_within_limit(self):
        """Test output within size limit passes."""
        result = safe_subprocess_run(
            ["echo", "small output"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert len(result.stdout) < MAX_OUTPUT_SIZE

    def test_run_captures_called_process_error(self):
        """Test CalledProcessError is handled."""
        with pytest.raises(subprocess.CalledProcessError):
            safe_subprocess_run(["false"], check=True)

    def test_run_with_additional_kwargs(self):
        """Test passing additional subprocess.run kwargs."""
        result = safe_subprocess_run(
            ["echo", "test"],
            capture_output=True,
            text=True,
            env={"TEST_VAR": "value"},
        )
        assert result.returncode == 0

    @patch("subprocess.run")
    def test_run_logs_execution(self, mock_run, tmp_path):
        """Test that subprocess execution is logged."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"test"
        mock_result.stderr = b""
        mock_run.return_value = mock_result

        with patch("agentready.utils.subprocess_utils.logger") as mock_logger:
            safe_subprocess_run(["test", "cmd"], cwd=repo)
            mock_logger.debug.assert_called()

    def test_run_validates_git_repo_path(self, tmp_path):
        """Test that git repo paths are validated."""
        # Create a git repo in forbidden location (simulate)
        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value = Path("/etc/evil-repo")

            repo = tmp_path / "repo"
            repo.mkdir()
            (repo / ".git").mkdir()

            # Should log debug and continue (validation is skipped on failure)
            result = safe_subprocess_run(
                ["echo", "test"],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            # Should still execute since validation is only logged
            assert result.returncode == 0

    def test_run_timeout_in_kwargs(self):
        """Test timeout can be passed in kwargs."""
        result = safe_subprocess_run(
            ["echo", "test"],
            timeout=5,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_run_command_not_found(self):
        """Test handling of command not found error."""
        with pytest.raises(FileNotFoundError):
            safe_subprocess_run(["nonexistent-command-12345"])

    def test_run_with_bytes_output(self):
        """Test command with bytes output."""
        result = safe_subprocess_run(["echo", "test"], capture_output=True)
        assert result.returncode == 0
        assert isinstance(result.stdout, bytes)

    def test_run_with_text_output(self):
        """Test command with text output."""
        result = safe_subprocess_run(
            ["echo", "test"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert isinstance(result.stdout, str)


class TestSecurityConstants:
    """Test security constants are properly defined."""

    def test_subprocess_timeout_defined(self):
        """Test SUBPROCESS_TIMEOUT is defined."""
        assert SUBPROCESS_TIMEOUT == 120

    def test_max_output_size_defined(self):
        """Test MAX_OUTPUT_SIZE is defined."""
        assert MAX_OUTPUT_SIZE == 10_000_000

    def test_subprocess_security_error_defined(self):
        """Test SubprocessSecurityError exception exists."""
        error = SubprocessSecurityError("test")
        assert isinstance(error, Exception)
        assert str(error) == "test"

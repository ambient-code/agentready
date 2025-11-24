"""Unit tests for privacy utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from agentready.utils.privacy import (
    sanitize_command_args,
    sanitize_error_message,
    sanitize_metadata,
    sanitize_path,
    shorten_commit_hash,
)


class TestSanitizePath:
    """Test path sanitization for public display."""

    def test_sanitize_path_with_relative_to(self, tmp_path):
        """Test relative path calculation."""
        base = tmp_path / "base"
        base.mkdir()
        target = base / "subdir" / "file.txt"
        target.parent.mkdir(parents=True)
        target.touch()

        result = sanitize_path(target, relative_to=base)
        assert result == str(Path("subdir") / "file.txt")

    def test_sanitize_path_not_relative_to(self, tmp_path):
        """Test path not relative to specified directory."""
        base = tmp_path / "base"
        base.mkdir()
        other = tmp_path / "other" / "file.txt"
        other.parent.mkdir(parents=True)
        other.touch()

        # Should fallback to home directory replacement
        result = sanitize_path(other, relative_to=base)
        assert str(other) in result or "~" in result

    def test_sanitize_path_home_directory(self):
        """Test home directory replacement."""
        home = Path.home()
        test_path = home / "project" / "src"

        result = sanitize_path(test_path)
        assert result.startswith("~")
        assert "project" in result

    @patch("pathlib.Path.home")
    def test_sanitize_path_home_error(self, mock_home, tmp_path):
        """Test home directory error handling."""
        mock_home.side_effect = RuntimeError("No home directory")
        test_path = tmp_path / "project"

        # Should not crash, just return path without home replacement
        result = sanitize_path(test_path)
        assert isinstance(result, str)

    @patch("getpass.getuser")
    def test_sanitize_path_username_unix(self, mock_user):
        """Test username redaction on Unix paths."""
        mock_user.return_value = "testuser"
        path = "/home/testuser/project/src"

        result = sanitize_path(path)
        assert result == "~/project/src"

    @patch("getpass.getuser")
    def test_sanitize_path_username_macos(self, mock_user):
        """Test username redaction on macOS paths."""
        mock_user.return_value = "testuser"
        path = "/Users/testuser/project/src"

        result = sanitize_path(path)
        assert result == "~/project/src"

    @patch("getpass.getuser")
    def test_sanitize_path_username_windows(self, mock_user):
        """Test username redaction on Windows paths."""
        mock_user.return_value = "testuser"
        path = "C:\\Users\\testuser\\project\\src"

        result = sanitize_path(path)
        assert result == "~\\project\\src"

    @patch("getpass.getuser")
    def test_sanitize_path_username_in_middle(self, mock_user):
        """Test username redaction in middle of path."""
        mock_user.return_value = "testuser"
        path = "/var/testuser/data"

        result = sanitize_path(path)
        assert "testuser" not in result or result == "/var/<user>/data"

    @patch("getpass.getuser")
    def test_sanitize_path_username_error(self, mock_user, tmp_path):
        """Test username error handling."""
        mock_user.side_effect = Exception("No username")
        test_path = tmp_path / "project"

        # Should not crash, just return path without username replacement
        result = sanitize_path(test_path)
        assert isinstance(result, str)

    def test_sanitize_path_string_input(self):
        """Test string path input."""
        path_str = "/tmp/test/file.txt"
        result = sanitize_path(path_str)
        assert isinstance(result, str)

    def test_sanitize_path_path_object(self, tmp_path):
        """Test Path object input."""
        path_obj = tmp_path / "test"
        result = sanitize_path(path_obj)
        assert isinstance(result, str)


class TestSanitizeCommandArgs:
    """Test command-line argument sanitization."""

    def test_sanitize_basic_args(self):
        """Test basic arguments pass through."""
        args = ["agentready", "assess", "."]
        result = sanitize_command_args(args)
        assert result == args

    def test_sanitize_config_flag(self):
        """Test --config flag redaction."""
        args = ["agentready", "assess", ".", "--config", "/secret/config.yaml"]
        result = sanitize_command_args(args)

        assert "--config" in result
        assert "<redacted>" in result
        assert "/secret/config.yaml" not in result

    @pytest.mark.parametrize(
        "flag",
        ["--config", "-c", "--api-key", "--token", "--password"],
    )
    def test_sanitize_sensitive_flags(self, flag):
        """Test various sensitive flags are redacted."""
        args = ["cmd", flag, "secret-value"]
        result = sanitize_command_args(args)

        assert flag in result
        assert "<redacted>" in result
        assert "secret-value" not in result

    def test_sanitize_absolute_path_unix(self):
        """Test absolute Unix path sanitization."""
        args = ["agentready", "assess", "/home/user/project"]
        result = sanitize_command_args(args)

        # Path should be sanitized
        assert result[0] == "agentready"
        assert result[1] == "assess"
        # Third arg should be sanitized path (contains ~)
        assert "~" in result[2] or "<" in result[2]

    def test_sanitize_absolute_path_windows(self):
        """Test absolute Windows path sanitization."""
        args = ["agentready", "assess", "C:\\Users\\test\\project"]
        result = sanitize_command_args(args)

        # Path should be sanitized
        assert result[0] == "agentready"
        assert result[1] == "assess"
        assert "~" in result[2] or "<" in result[2]

    def test_sanitize_tilde_path(self):
        """Test tilde path sanitization."""
        args = ["agentready", "assess", "~/project"]
        result = sanitize_command_args(args)

        # Tilde path should be sanitized
        assert "~" in result[2] or "<" in result[2]

    def test_sanitize_api_key_in_arg(self):
        """Test API key in argument value."""
        args = ["cmd", "--key", "sk-ant-api03-1234567890abcdefghij"]
        result = sanitize_command_args(args)

        assert result == ["cmd", "--key", "<redacted>"]

    def test_sanitize_api_key_pattern(self):
        """Test API key pattern detection."""
        args = ["authenticate", "sk-test-1234567890abcdefghij"]
        result = sanitize_command_args(args)

        assert "<api-key>" in result
        assert "sk-test" not in result

    def test_sanitize_mixed_args(self):
        """Test mixed sensitive and safe arguments."""
        args = [
            "agentready",
            "assess",
            "/home/user/project",
            "--config",
            "config.yaml",
            "--verbose",
        ]
        result = sanitize_command_args(args)

        assert result[0] == "agentready"
        assert result[1] == "assess"
        assert "--config" in result
        assert "<redacted>" in result
        assert "--verbose" in result

    def test_sanitize_empty_args(self):
        """Test empty arguments list."""
        args = []
        result = sanitize_command_args(args)
        assert result == []


class TestSanitizeErrorMessage:
    """Test error message sanitization."""

    def test_sanitize_empty_message(self):
        """Test empty message handling."""
        result = sanitize_error_message("")
        assert result == ""

    def test_sanitize_none_message(self):
        """Test None message handling."""
        result = sanitize_error_message(None)
        assert result is None

    def test_sanitize_repo_path(self, tmp_path):
        """Test repository path redaction."""
        repo = tmp_path / "project"
        repo.mkdir()
        message = f"Error in {repo}/src/file.py"

        result = sanitize_error_message(message, repo_path=repo)
        assert "<repo>" in result
        assert str(repo) not in result

    def test_sanitize_home_directory(self):
        """Test home directory redaction."""
        home = Path.home()
        message = f"Error in {home}/project/file.py"

        result = sanitize_error_message(message)
        assert "<home>" in result
        assert str(home) not in result

    @patch("pathlib.Path.home")
    def test_sanitize_home_directory_error(self, mock_home):
        """Test home directory error handling."""
        mock_home.side_effect = RuntimeError("No home")
        message = "Error occurred"

        # Should not crash
        result = sanitize_error_message(message)
        assert result == "Error occurred"

    @patch("getpass.getuser")
    def test_sanitize_username_unix(self, mock_user):
        """Test username redaction in Unix paths."""
        mock_user.return_value = "testuser"
        message = "Error in /home/testuser/project"

        result = sanitize_error_message(message)
        assert "testuser" not in result or "/<user>/" in result

    @patch("getpass.getuser")
    def test_sanitize_username_windows(self, mock_user):
        """Test username redaction in Windows paths."""
        mock_user.return_value = "testuser"
        message = "Error in C:\\Users\\testuser\\project"

        result = sanitize_error_message(message)
        assert "testuser" not in result or "\\<user>\\" in result

    @patch("getpass.getuser")
    def test_sanitize_username_error(self, mock_user):
        """Test username error handling."""
        mock_user.side_effect = Exception("No username")
        message = "Error occurred"

        # Should not crash
        result = sanitize_error_message(message)
        assert result == "Error occurred"

    def test_sanitize_absolute_paths(self):
        """Test absolute path redaction."""
        message = "Error in /var/log/app.log and C:\\Windows\\System32\\file.dll"

        result = sanitize_error_message(message)
        assert "/var/log/app.log" not in result
        assert "C:\\Windows\\System32" not in result
        assert "<path>" in result

    def test_sanitize_anthropic_api_key(self):
        """Test Anthropic API key redaction."""
        message = "Auth failed: sk-ant-api03-abcdefghij1234567890"

        result = sanitize_error_message(message)
        assert "sk-ant" not in result
        assert "<api-key>" in result

    def test_sanitize_generic_api_key(self):
        """Test generic API key redaction."""
        message = "Invalid key: sk-test-1234567890abcdefghijklmnop"

        result = sanitize_error_message(message)
        assert "sk-test" not in result
        assert "<api-key>" in result

    def test_sanitize_email_address(self):
        """Test email address redaction."""
        message = "Contact user@example.com or admin@company.co.uk"

        result = sanitize_error_message(message)
        assert "user@example.com" not in result
        assert "admin@company.co.uk" not in result
        assert "<email>" in result

    def test_sanitize_multiple_emails(self):
        """Test multiple email redaction."""
        message = "Contact john.doe@example.com or jane_smith+test@domain.io"

        result = sanitize_error_message(message)
        assert "@" not in result or result.count("<email>") >= 2

    def test_sanitize_long_message(self):
        """Test long message truncation."""
        message = "Error: " + ("x" * 2000)

        result = sanitize_error_message(message)
        assert len(result) <= 1100  # 1000 + "... (truncated)"
        assert "truncated" in result

    def test_sanitize_combined_patterns(self):
        """Test multiple patterns in one message."""
        message = (
            "Error in /home/user/project: "
            "sk-ant-api03-test123456 "
            "contact admin@example.com"
        )

        result = sanitize_error_message(message)
        assert "/home/user" not in result
        assert "sk-ant" not in result
        assert "admin@example.com" not in result
        assert "<path>" in result or "<home>" in result
        assert "<api-key>" in result
        assert "<email>" in result


class TestShortenCommitHash:
    """Test git commit hash shortening."""

    def test_shorten_full_hash(self):
        """Test shortening full 40-character hash."""
        hash_full = "abc123def456789012345678901234567890abcd"
        result = shorten_commit_hash(hash_full)
        assert result == "abc123de"

    def test_shorten_short_hash(self):
        """Test shortening already short hash."""
        hash_short = "abc123"
        result = shorten_commit_hash(hash_short)
        assert result == "abc123"

    def test_shorten_8_char_hash(self):
        """Test shortening exactly 8-character hash."""
        hash_8 = "abc12345"
        result = shorten_commit_hash(hash_8)
        assert result == "abc12345"

    def test_shorten_empty_hash(self):
        """Test empty hash handling."""
        result = shorten_commit_hash("")
        assert result == ""

    def test_shorten_none_hash(self):
        """Test None hash handling."""
        result = shorten_commit_hash(None)
        assert result is None


class TestSanitizeMetadata:
    """Test metadata dictionary sanitization."""

    def test_sanitize_empty_metadata(self):
        """Test empty metadata."""
        metadata = {}
        result = sanitize_metadata(metadata)
        assert result == {}

    def test_sanitize_command_field(self):
        """Test command field sanitization."""
        metadata = {
            "command": "agentready assess /home/user/project --config secret.yaml"
        }
        result = sanitize_metadata(metadata)

        assert "command" in result
        assert "/home/user/project" not in result["command"]
        assert "<redacted>" in result["command"]

    def test_sanitize_path_like_string(self):
        """Test path-like string sanitization."""
        metadata = {"file_path": "/home/user/project/src/file.py"}
        result = sanitize_metadata(metadata)

        assert "file_path" in result
        # Should be sanitized with ~ or <user>
        assert "~" in result["file_path"] or "<" in result["file_path"]

    def test_sanitize_windows_path(self):
        """Test Windows path sanitization."""
        metadata = {"path": "C:\\Users\\test\\project\\file.py"}
        result = sanitize_metadata(metadata)

        assert "path" in result
        assert "~" in result["path"] or "<" in result["path"]

    def test_sanitize_non_path_strings(self):
        """Test non-path strings pass through."""
        metadata = {
            "name": "test-project",
            "version": "1.0.0",
            "status": "success",
        }
        result = sanitize_metadata(metadata)
        assert result == metadata

    def test_sanitize_mixed_metadata(self):
        """Test mixed metadata with paths and values."""
        metadata = {
            "name": "project",
            "path": "/home/user/project",
            "command": "assess /secret --config api.yaml",
            "count": 42,
        }
        result = sanitize_metadata(metadata)

        assert result["name"] == "project"
        assert result["count"] == 42
        assert "/home/user" not in result["path"]
        assert "/secret" not in result["command"]
        assert "<redacted>" in result["command"]

    def test_sanitize_nested_values(self):
        """Test that nested structures are not deeply sanitized."""
        metadata = {
            "simple": "value",
            "path": "/home/user/file",
        }
        result = sanitize_metadata(metadata)

        assert result["simple"] == "value"
        assert "~" in result["path"] or "<" in result["path"]

    def test_sanitize_preserves_types(self):
        """Test non-string types are preserved."""
        metadata = {
            "count": 42,
            "ratio": 3.14,
            "enabled": True,
            "items": None,
        }
        result = sanitize_metadata(metadata)
        assert result == metadata

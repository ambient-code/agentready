"""Unit tests for repository manager."""

from pathlib import Path
from tempfile import TemporaryDirectory

from agentready.services.repository_manager import RepositoryManager


class TestRepositoryManager:
    """Test RepositoryManager class."""

    def test_validate_https_url(self):
        """Test validation of HTTPS URLs."""
        manager = RepositoryManager(Path("/tmp/cache"))
        is_valid, error = manager.validate_url("https://github.com/user/repo")
        assert is_valid is True
        assert error is None

    def test_validate_http_url_rejected(self):
        """Test that HTTP URLs are rejected."""
        manager = RepositoryManager(Path("/tmp/cache"))
        is_valid, error = manager.validate_url("http://github.com/user/repo")
        assert is_valid is False
        assert "HTTP is not secure" in error

    def test_validate_git_url(self):
        """Test validation of git:// URLs."""
        manager = RepositoryManager(Path("/tmp/cache"))
        is_valid, error = manager.validate_url("git://github.com/user/repo")
        assert is_valid is True
        assert error is None

    def test_validate_invalid_protocol(self):
        """Test rejection of invalid protocols."""
        manager = RepositoryManager(Path("/tmp/cache"))
        is_valid, error = manager.validate_url("ftp://example.com/repo")
        assert is_valid is False
        assert "Unsupported protocol" in error

    def test_validate_malformed_url(self):
        """Test rejection of malformed URLs."""
        manager = RepositoryManager(Path("/tmp/cache"))
        is_valid, error = manager.validate_url("not-a-valid-url")
        assert is_valid is False

    def test_validate_local_path_exists(self):
        """Test validation of existing local paths."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            git_dir = repo_path / ".git"
            git_dir.mkdir()

            manager = RepositoryManager(Path(tmpdir) / "cache")
            is_valid, error = manager.validate_url(str(repo_path))
            assert is_valid is True
            assert error is None

    def test_validate_local_path_not_exists(self):
        """Test rejection of non-existent local paths."""
        manager = RepositoryManager(Path("/tmp/cache"))
        is_valid, error = manager.validate_url("/nonexistent/path")
        assert is_valid is False

    def test_get_repository_name_from_https_url(self):
        """Test extracting repository name from HTTPS URL."""
        manager = RepositoryManager(Path("/tmp/cache"))
        name = manager.get_repository_name_from_url(
            "https://github.com/user/my-repo.git"
        )
        assert name == "my-repo"

    def test_get_repository_name_from_url_without_git_suffix(self):
        """Test extracting repository name from URL without .git suffix."""
        manager = RepositoryManager(Path("/tmp/cache"))
        name = manager.get_repository_name_from_url("https://github.com/user/my-repo")
        assert name == "my-repo"

    def test_get_repository_name_from_local_path(self):
        """Test extracting repository name from local path."""
        manager = RepositoryManager(Path("/tmp/cache"))
        name = manager.get_repository_name_from_url("/home/user/my-repo")
        assert name == "my-repo"

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        with TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()

            manager = RepositoryManager(cache_dir)

            # Try to escape the cache directory
            success, path, error = manager.clone_repository(
                "https://github.com/user/repo",
                target_dir=Path("/") / "etc" / "passwd",  # Outside cache dir
            )

            assert success is False
            assert "outside cache directory" in error.lower()

    def test_cleanup_repository(self):
        """Test repository cleanup."""
        with TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo"
            repo_path.mkdir()
            test_file = repo_path / "test.txt"
            test_file.write_text("test")

            manager = RepositoryManager(Path(tmpdir) / "cache")
            success = manager.cleanup_repository(repo_path)

            assert success is True
            assert not repo_path.exists()

    def test_cleanup_nonexistent_repository(self):
        """Test cleanup of non-existent repository."""
        manager = RepositoryManager(Path("/tmp/cache"))
        success = manager.cleanup_repository(Path("/nonexistent/path"))

        # Should return True even if directory doesn't exist
        assert success is True

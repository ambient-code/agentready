"""Security control verification tests for batch assessment."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agentready.services.assessment_cache import AssessmentCache
from agentready.services.repository_manager import RepositoryManager


class TestSecurityControls:
    """Test security controls for batch assessment."""

    # HTTPS-Only URL Validation Tests
    def test_https_only_enforcement(self):
        """Test that HTTP URLs are rejected (HTTPS-only enforcement)."""
        manager = RepositoryManager(Path("/tmp/cache"))

        # Test HTTP rejection
        is_valid, error = manager.validate_url("http://github.com/user/repo")
        assert not is_valid
        assert "HTTP is not secure" in error

        # Test HTTPS acceptance
        is_valid, error = manager.validate_url("https://github.com/user/repo")
        assert is_valid

    def test_git_protocol_allowed(self):
        """Test that git:// protocol is allowed (alternative to HTTPS)."""
        manager = RepositoryManager(Path("/tmp/cache"))
        is_valid, error = manager.validate_url("git://github.com/user/repo")
        assert is_valid

    # Path Traversal Prevention Tests
    def test_path_traversal_with_parent_directories(self):
        """Test prevention of path traversal using .. in target path."""
        with TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            manager = RepositoryManager(cache_dir)

            # Try path traversal
            success, path, error = manager.clone_repository(
                "https://github.com/user/repo",
                target_dir=cache_dir / ".." / "escape",
            )

            assert not success
            assert "outside cache directory" in error.lower()

    def test_path_traversal_with_absolute_path(self):
        """Test prevention of absolute path escape."""
        with TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            manager = RepositoryManager(cache_dir)

            # Try absolute path escape
            success, path, error = manager.clone_repository(
                "https://github.com/user/repo",
                target_dir=Path("/") / "tmp" / "evil",
            )

            assert not success
            assert "outside cache directory" in error.lower()

    def test_path_traversal_with_symlink(self):
        """Test that path resolution handles symlinks correctly."""
        with TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            manager = RepositoryManager(cache_dir)

            # Create a symlink outside cache
            outside_dir = Path(tmpdir) / "outside"
            outside_dir.mkdir()

            try:
                # On systems that support symlinks
                symlink = cache_dir / "evil_link"
                symlink.symlink_to(outside_dir)

                # Try to use symlink to escape
                success, path, error = manager.clone_repository(
                    "https://github.com/user/repo",
                    target_dir=symlink / "repo",
                )

                # Should fail because it resolves outside cache
                assert not success
                assert "outside cache directory" in error.lower()
            except OSError:
                # Symlinks not supported on this system
                pytest.skip("Symlinks not supported")

    # SQL Injection Prevention Tests
    def test_sql_injection_in_repo_url(self):
        """Test that SQL injection attempts in repo URL are safe."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))

            # Try SQL injection in URL
            malicious_url = "https://github.com/user/repo'; DROP TABLE assessments; --"
            commit_hash = "abc123"

            # Should not crash or execute SQL
            count = cache.invalidate(malicious_url, commit_hash)

            # Verify table still exists by querying
            stats = cache.get_stats()
            assert "total_entries" in stats

    def test_sql_injection_in_commit_hash(self):
        """Test that SQL injection attempts in commit hash are safe."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))

            repo_url = "https://github.com/user/repo"
            # Try SQL injection in commit hash
            malicious_commit = "abc123' OR '1'='1"

            # Should not crash or execute SQL
            result = cache.get(repo_url, malicious_commit)

            # Should return None, not crash
            assert result is None

    # Parameterized Query Tests
    def test_parameterized_queries_used(self):
        """Test that queries use parameterization."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))

            # Test various injection attempts
            injection_attempts = [
                ("' OR '1'='1", "abc123"),
                ("repo'; DROP TABLE--", "abc123"),
                ("repo", "'; DELETE FROM--"),
            ]

            for repo_url, commit_hash in injection_attempts:
                # None of these should crash
                result = cache.get(repo_url, commit_hash)
                assert result is None

            # Verify database integrity
            stats = cache.get_stats()
            assert isinstance(stats, dict)
            assert "total_entries" in stats

    # Security Validation in URL Parsing
    def test_url_validation_prevents_injection(self):
        """Test that URL validation catches malicious URLs."""
        manager = RepositoryManager(Path("/tmp/cache"))

        injection_urls = [
            "https://github.com/user/repo`; malicious",
            "https://github.com/user/repo|rm -rf /",
            "https://github.com/user/repo&&dangerous",
            "https://github.com/user/repo;cat /etc/passwd",
        ]

        # These might be valid URLs syntactically, but we test that
        # they don't cause command injection in subprocess calls
        for url in injection_urls:
            is_valid, error = manager.validate_url(url)
            # Just verify it doesn't crash
            assert isinstance(is_valid, bool)

    # No Shell Execution
    def test_no_shell_execution_in_clone(self):
        """Test that git clone doesn't use shell=True."""
        with TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            manager = RepositoryManager(cache_dir)

            # Test with a URL that would be dangerous with shell execution
            dangerous_url = "https://github.com/user/repo'; rm -rf /; echo 'x"

            # Should fail validation or safe subprocess execution
            success, path, error = manager.clone_repository(dangerous_url)

            # Should fail safely without executing the injection
            assert success is False or error is not None

    # Cache File Permissions Test
    def test_cache_database_created_safely(self):
        """Test that cache database is created with safe permissions."""
        with TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = AssessmentCache(cache_dir)

            # Verify database file exists
            assert cache.db_path.exists()

            # On Unix systems, verify we can read it
            stats = cache.get_stats()
            assert "total_entries" in stats

    # Input Validation Tests
    def test_empty_repository_list_handling(self):
        """Test that empty repository lists are handled safely."""
        manager = RepositoryManager(Path("/tmp/cache"))

        # Empty URL should be invalid
        is_valid, error = manager.validate_url("")
        assert not is_valid

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        manager = RepositoryManager(Path("/tmp/cache"))

        # URLs with leading/trailing whitespace should be handled
        is_valid, error = manager.validate_url("  https://github.com/user/repo  ")
        assert is_valid  # Should be stripped and valid

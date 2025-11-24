"""Unit tests for assessment cache."""

from pathlib import Path
from tempfile import TemporaryDirectory


from agentready.services.assessment_cache import AssessmentCache


class TestAssessmentCache:
    """Test AssessmentCache class."""

    def test_initialize_cache(self):
        """Test cache initialization."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))
            assert cache.db_path.exists()
            assert cache.db_path.name == "assessments.db"

    def test_cache_directory_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "deep" / "nested" / "cache"
            cache = AssessmentCache(cache_dir)
            assert cache_dir.exists()

    def test_get_cache_stats_empty(self):
        """Test cache stats for empty cache."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))
            stats = cache.get_stats()

            assert stats["total_entries"] == 0
            assert stats["valid_entries"] == 0
            assert stats["unique_repositories"] == 0
            assert stats["ttl_days"] == 7

    def test_invalidate_by_repo_url(self):
        """Test invalidation by repository URL."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))

            # Invalidate (even though nothing is cached)
            count = cache.invalidate("https://github.com/user/repo")
            assert count == 0

    def test_invalidate_by_commit(self):
        """Test invalidation by specific commit."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir))

            # Invalidate (even though nothing is cached)
            count = cache.invalidate(
                "https://github.com/user/repo",
                "abc123def456",
            )
            assert count == 0

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir), ttl_days=0)  # Expire immediately
            count = cache.cleanup_expired()
            # No entries to clean up
            assert count == 0

    def test_ttl_configuration(self):
        """Test TTL configuration."""
        with TemporaryDirectory() as tmpdir:
            cache = AssessmentCache(Path(tmpdir), ttl_days=14)
            assert cache.ttl_days == 14

            stats = cache.get_stats()
            assert stats["ttl_days"] == 14

    def test_cache_path_isolation(self):
        """Test that different caches use different databases."""
        with TemporaryDirectory() as tmpdir:
            cache1_dir = Path(tmpdir) / "cache1"
            cache2_dir = Path(tmpdir) / "cache2"

            cache1 = AssessmentCache(cache1_dir)
            cache2 = AssessmentCache(cache2_dir)

            assert cache1.db_path != cache2.db_path

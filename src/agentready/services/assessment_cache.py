"""SQLite-based cache for assessment results."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..models import Assessment


class AssessmentCache:
    """SQLite-backed cache for assessment results with TTL support.

    Schema: assessments(repository_url, commit_hash, overall_score,
            assessment_json, cached_at, expires_at)
    """

    def __init__(self, cache_dir: Path, ttl_days: int = 7):
        """Initialize assessment cache.

        Args:
            cache_dir: Directory for cache database
            ttl_days: Time-to-live in days (default: 7)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "assessments.db"
        self.ttl_days = ttl_days
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS assessments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        repository_url TEXT NOT NULL,
                        commit_hash TEXT NOT NULL,
                        overall_score REAL,
                        assessment_json TEXT NOT NULL,
                        cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        UNIQUE(repository_url, commit_hash)
                    )
                    """
                )

                # Create index for faster queries
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_repo_commit
                    ON assessments(repository_url, commit_hash)
                    """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_expires_at
                    ON assessments(expires_at)
                    """
                )

                conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to initialize cache database: {e}")

    def get(self, repository_url: str, commit_hash: str) -> Optional[Assessment]:
        """Get cached assessment if available and not expired.

        Security: Uses parameterized queries to prevent SQL injection.

        Args:
            repository_url: Repository URL
            commit_hash: Git commit hash

        Returns:
            Assessment if found and valid, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT assessment_json, expires_at FROM assessments
                    WHERE repository_url = ? AND commit_hash = ?
                    """,
                    (repository_url, commit_hash),
                )
                row = cursor.fetchone()

                if not row:
                    return None

                assessment_json, expires_at = row

                # Check if expired
                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_dt:
                        # Delete expired entry
                        conn.execute(
                            """
                            DELETE FROM assessments
                            WHERE repository_url = ? AND commit_hash = ?
                            """,
                            (repository_url, commit_hash),
                        )
                        conn.commit()
                        return None

                # Parse and return assessment
                assessment_data = json.loads(assessment_json)
                return self._deserialize_assessment(assessment_data)

        except (sqlite3.Error, json.JSONDecodeError, ValueError):
            return None

    def set(
        self,
        repository_url: str,
        commit_hash: str,
        assessment: Assessment,
    ) -> bool:
        """Cache an assessment.

        Security: Uses parameterized queries to prevent SQL injection.

        Args:
            repository_url: Repository URL
            commit_hash: Git commit hash
            assessment: Assessment to cache

        Returns:
            True if successful, False otherwise
        """
        try:
            assessment_json = json.dumps(assessment.to_dict())
            expires_at = datetime.now() + timedelta(days=self.ttl_days)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO assessments
                    (repository_url, commit_hash, overall_score, assessment_json, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        repository_url,
                        commit_hash,
                        assessment.overall_score,
                        assessment_json,
                        expires_at.isoformat(),
                    ),
                )
                conn.commit()
            return True

        except (sqlite3.Error, TypeError):
            return False

    def invalidate(self, repository_url: str, commit_hash: Optional[str] = None) -> int:
        """Invalidate cache entries.

        Args:
            repository_url: Repository URL
            commit_hash: Specific commit hash (if None, invalidates all for repo)

        Returns:
            Number of entries deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if commit_hash:
                    cursor = conn.execute(
                        """
                        DELETE FROM assessments
                        WHERE repository_url = ? AND commit_hash = ?
                        """,
                        (repository_url, commit_hash),
                    )
                else:
                    cursor = conn.execute(
                        """
                        DELETE FROM assessments
                        WHERE repository_url = ?
                        """,
                        (repository_url,),
                    )
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error:
            return 0

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of entries deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM assessments
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                    """,
                    (datetime.now().isoformat(),),
                )
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error:
            return 0

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM assessments")
                total = cursor.fetchone()[0]

                cursor = conn.execute(
                    "SELECT COUNT(*) FROM assessments WHERE expires_at > ?",
                    (datetime.now().isoformat(),),
                )
                valid = cursor.fetchone()[0]

                cursor = conn.execute(
                    "SELECT COUNT(DISTINCT repository_url) FROM assessments"
                )
                unique_repos = cursor.fetchone()[0]

                return {
                    "total_entries": total,
                    "valid_entries": valid,
                    "expired_entries": total - valid,
                    "unique_repositories": unique_repos,
                    "database_path": str(self.db_path),
                    "ttl_days": self.ttl_days,
                }
        except sqlite3.Error:
            return {}

    @staticmethod
    def _deserialize_assessment(data: dict) -> Assessment:
        """Deserialize assessment from JSON data.

        Args:
            data: Assessment dictionary from cache

        Returns:
            Assessment object
        """
        # This is a simplified deserialization
        # In practice, you'd need full deserialization logic
        # For now, we'll use a placeholder that assumes the cached JSON
        # has the correct structure

        # Note: This is a simplified approach. In production, you'd need
        # proper deserialization that reconstructs all nested objects
        raise NotImplementedError(
            "Full assessment deserialization not yet implemented. "
            "Consider caching assessment JSON directly and providing "
            "a proper deserializer factory."
        )

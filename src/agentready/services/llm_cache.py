"""LLM response caching to avoid redundant API calls."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from agentready.models import DiscoveredSkill

logger = logging.getLogger(__name__)


class LLMCache:
    """Caches LLM enrichment responses."""

    def __init__(self, cache_dir: Path, ttl_days: int = 7):
        """Initialize cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_days: Time-to-live in days (default: 7)
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_days = ttl_days

    def get(self, cache_key: str) -> DiscoveredSkill | None:
        """Get cached skill if exists and not expired.

        Args:
            cache_key: Unique cache key

        Returns:
            Cached DiscoveredSkill or None if miss/expired
        """
        # Security: Validate cache_key to prevent path traversal
        cache_file = self._get_safe_cache_path(cache_key)
        if cache_file is None:
            logger.warning(f"Invalid cache key rejected: {cache_key}")
            return None

        if not cache_file.exists():
            logger.debug(f"Cache miss: {cache_key}")
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check expiration
            cached_at = datetime.fromisoformat(data["cached_at"])
            if datetime.now() - cached_at > timedelta(days=self.ttl_days):
                logger.info(f"Cache expired: {cache_key}")
                cache_file.unlink()  # Delete expired cache
                return None

            logger.info(f"Cache hit: {cache_key}")
            return DiscoveredSkill(**data["skill"])

        except Exception as e:
            logger.warning(f"Cache read error for {cache_key}: {e}")
            return None

    def set(self, cache_key: str, skill: DiscoveredSkill):
        """Save skill to cache.

        Args:
            cache_key: Unique cache key
            skill: DiscoveredSkill to cache
        """
        # Security: Validate cache_key to prevent path traversal
        cache_file = self._get_safe_cache_path(cache_key)
        if cache_file is None:
            logger.warning(f"Invalid cache key rejected: {cache_key}")
            return

        try:
            data = {
                "cached_at": datetime.now().isoformat(),
                "skill": skill.to_dict(),
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Cached: {cache_key}")

        except Exception as e:
            logger.warning(f"Cache write error for {cache_key}: {e}")

    def _get_safe_cache_path(self, cache_key: str) -> Path | None:
        """Validate cache key and return safe path.

        Security: Prevents path traversal attacks by validating cache_key
        contains no directory separators and resolves within cache_dir.

        Args:
            cache_key: Cache key to validate

        Returns:
            Validated Path or None if invalid
        """
        # Reject keys with path separators (/, \)
        if "/" in cache_key or "\\" in cache_key:
            return None

        # Reject keys with null bytes or other dangerous characters
        if "\0" in cache_key or ".." in cache_key:
            return None

        # Construct path and resolve to canonical form
        cache_file = (self.cache_dir / f"{cache_key}.json").resolve()

        # Ensure resolved path is within cache directory
        try:
            cache_file.relative_to(self.cache_dir.resolve())
        except ValueError:
            # Path is outside cache_dir
            return None

        return cache_file

    @staticmethod
    def generate_key(attribute_id: str, score: float, evidence_hash: str) -> str:
        """Generate cache key from finding attributes.

        Args:
            attribute_id: Attribute ID (e.g., "claude_md_file")
            score: Finding score
            evidence_hash: Hash of evidence list

        Returns:
            Cache key string
        """
        key_data = f"{attribute_id}_{score}_{evidence_hash}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

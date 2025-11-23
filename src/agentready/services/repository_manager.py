"""Secure repository manager for cloning and validating repositories."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from ..models import Repository
from ..models.batch_assessment import FailureTracker


class RepositoryManager:
    """Manages secure cloning and preparation of repositories for assessment.

    Security Features:
    - HTTPS-only URL validation
    - Path traversal prevention
    - Shallow cloning for efficiency (depth=1)
    - Disabled Git hooks during clone
    - Parameterized validation
    """

    # Allowed protocols for cloning
    ALLOWED_PROTOCOLS = {"https", "git"}

    def __init__(self, cache_dir: Path):
        """Initialize repository manager.

        Args:
            cache_dir: Directory where repositories will be cloned
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def validate_url(self, url: str) -> tuple[bool, Optional[str]]:
        """Validate repository URL for security.

        Args:
            url: Repository URL or local path

        Returns:
            Tuple of (is_valid, error_message)
        """
        url = url.strip()

        # Empty URL is invalid
        if not url:
            return False, "URL cannot be empty"

        # Check if it looks like a URL with protocol
        if "://" in url:
            # For URLs, require HTTPS (git:// also allowed but prefer HTTPS)
            try:
                parsed = urlparse(url)
                if parsed.scheme == "http":
                    return (
                        False,
                        f"HTTP is not secure; use HTTPS instead: {url}",
                    )
                if parsed.scheme not in self.ALLOWED_PROTOCOLS:
                    return False, f"Unsupported protocol: {parsed.scheme}"

                # Basic hostname validation
                if not parsed.netloc:
                    return False, f"Invalid URL format: {url}"

                return True, None
            except Exception as e:
                return False, f"Invalid URL: {url} ({str(e)})"
        else:
            # Treat as local path
            path = Path(url).resolve()
            if path.exists() and (path / ".git").exists():
                return True, None
            return False, f"Local path does not exist or is not a git repository: {url}"

    def get_repository_name_from_url(self, url: str) -> str:
        """Extract repository name from URL.

        Args:
            url: Repository URL or path

        Returns:
            Repository name
        """
        url = url.strip()

        # For local paths
        if not url.startswith(("http://", "https://", "git://")):
            return Path(url).name

        # For URLs, extract from the last part of the path
        # https://github.com/user/repo.git -> repo
        parsed = urlparse(url)
        path = parsed.path.rstrip("/").rstrip(".git")
        return Path(path).name or "repository"

    def clone_repository(
        self,
        url: str,
        target_dir: Optional[Path] = None,
    ) -> tuple[bool, Path, Optional[str]]:
        """Clone repository securely.

        Security: Uses shallow clone (depth=1) and disables Git hooks.

        Args:
            url: Repository URL or local path
            target_dir: Target directory (if None, uses cache_dir)

        Returns:
            Tuple of (success, repo_path, error_message)
        """
        # Validate URL
        is_valid, error = self.validate_url(url)
        if not is_valid:
            return False, Path(), error

        # For local paths, just return the path
        if not url.startswith(("http://", "https://", "git://")):
            return True, Path(url).resolve(), None

        # Determine target directory
        if target_dir is None:
            repo_name = self.get_repository_name_from_url(url)
            target_dir = self.cache_dir / repo_name
        else:
            target_dir = Path(target_dir).resolve()

        # Prevent path traversal
        try:
            target_dir.resolve().relative_to(self.cache_dir.resolve())
        except ValueError:
            return (
                False,
                Path(),
                f"Target directory is outside cache directory: {target_dir}",
            )

        # Skip if already cloned
        if (target_dir / ".git").exists():
            return True, target_dir, None

        # Create parent directories
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        # Clone with security settings
        try:
            # Use subprocess with explicit arguments (no shell=True)
            cmd = [
                "git",
                "clone",
                "--depth=1",  # Shallow clone for efficiency
                "--no-hooks",  # Disable Git hooks
                url,
                str(target_dir),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5-minute timeout
            )

            if result.returncode != 0:
                # Clean up partial clone
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                return False, Path(), f"Clone failed: {result.stderr}"

            return True, target_dir, None

        except subprocess.TimeoutExpired:
            # Clean up partial clone
            if target_dir.exists():
                shutil.rmtree(target_dir)
            return False, Path(), "Clone operation timed out"
        except Exception as e:
            # Clean up partial clone
            if target_dir.exists():
                shutil.rmtree(target_dir)
            return False, Path(), f"Clone error: {str(e)}"

    def prepare_repository(
        self,
        url: str,
    ) -> tuple[bool, Repository, Optional[FailureTracker]]:
        """Clone and prepare repository for assessment.

        Args:
            url: Repository URL or local path

        Returns:
            Tuple of (success, Repository_model, failure_tracker)
        """
        # Clone repository
        success, repo_path, error = self.clone_repository(url)
        if not success:
            failure = FailureTracker(
                repository_url=url,
                error_type="clone_error",
                error_message=error or "Unknown error during cloning",
                can_retry=True,
            )
            return False, None, failure

        # Build Repository model
        try:
            # Get git information
            git_cmd = ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"]
            branch_result = subprocess.run(
                git_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            branch = (
                branch_result.stdout.strip()
                if branch_result.returncode == 0
                else "HEAD"
            )

            commit_cmd = ["git", "-C", str(repo_path), "rev-parse", "HEAD"]
            commit_result = subprocess.run(
                commit_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            commit_hash = (
                commit_result.stdout.strip()
                if commit_result.returncode == 0
                else "unknown"
            )

            # Build Repository model (Scanner will handle language detection, etc.)
            repository = Repository(
                path=repo_path.resolve(),
                name=repo_path.name,
                url=url,
                branch=branch,
                commit_hash=commit_hash,
                languages={},  # Will be populated by Scanner
                total_files=0,  # Will be populated by Scanner
                total_lines=0,  # Will be populated by Scanner
            )

            return True, repository, None

        except Exception as e:
            failure = FailureTracker(
                repository_url=url,
                error_type="validation_error",
                error_message=f"Failed to prepare repository: {str(e)}",
                can_retry=False,
            )
            return False, None, failure

    def cleanup_repository(self, repo_path: Path) -> bool:
        """Clean up cloned repository.

        Args:
            repo_path: Path to repository to clean up

        Returns:
            True if cleanup successful
        """
        try:
            if repo_path.exists():
                shutil.rmtree(repo_path)
            return True
        except Exception:
            return False

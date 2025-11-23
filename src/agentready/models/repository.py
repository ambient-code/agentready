"""Repository model representing the target git repository being assessed."""

from dataclasses import dataclass
from pathlib import Path

from ..utils.privacy import sanitize_path, shorten_commit_hash


@dataclass
class Repository:
    """Represents a git repository being assessed.

    Attributes:
        path: Absolute path to repository root
        name: Repository name (derived from path)
        url: Remote origin URL if available
        branch: Current branch name
        commit_hash: Current HEAD commit SHA
        languages: Detected languages with file counts (e.g., {"Python": 42})
        total_files: Total files in repository (respecting .gitignore)
        total_lines: Total lines of code
    """

    path: Path
    name: str
    url: str | None
    branch: str
    commit_hash: str
    languages: dict[str, int]
    total_files: int
    total_lines: int

    def __post_init__(self):
        """Validate repository data after initialization."""
        # Convert string paths to Path objects for runtime type safety
        if isinstance(self.path, str):
            object.__setattr__(self, "path", Path(self.path))

        if not self.path.exists():
            raise ValueError(f"Repository path does not exist: {self.path}")

        if not (self.path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.path}")

        if self.total_files < 0:
            raise ValueError(f"Total files must be non-negative: {self.total_files}")

        if self.total_lines < 0:
            raise ValueError(f"Total lines must be non-negative: {self.total_lines}")

    def get_sanitized_path(self) -> str:
        """Get sanitized path for public display.

        Security: Redacts usernames and home directories.

        Returns:
            Sanitized path string safe for sharing
        """
        return sanitize_path(self.path)

    def get_short_commit_hash(self) -> str:
        """Get shortened commit hash.

        Security: Returns 8-character hash instead of full 40 characters.

        Returns:
            Shortened commit hash
        """
        return shorten_commit_hash(self.commit_hash)

    def to_dict(self, privacy_mode: bool = False) -> dict:
        """Convert to dictionary for JSON serialization.

        Args:
            privacy_mode: If True, sanitize sensitive data

        Returns:
            Dictionary representation
        """
        if privacy_mode:
            return {
                "path": self.get_sanitized_path(),
                "name": self.name,
                "url": None,  # Redact URL in privacy mode
                "branch": self.branch,
                "commit_hash": self.get_short_commit_hash(),
                "languages": self.languages,
                "total_files": self.total_files,
                "total_lines": self.total_lines,
            }
        else:
            return {
                "path": str(self.path),
                "name": self.name,
                "url": self.url,
                "branch": self.branch,
                "commit_hash": self.commit_hash,
                "languages": self.languages,
                "total_files": self.total_files,
                "total_lines": self.total_lines,
            }

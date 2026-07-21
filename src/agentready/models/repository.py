"""Repository model representing the target git repository being assessed."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from ..utils.privacy import sanitize_path, shorten_commit_hash

if TYPE_CHECKING:
    from ..services.git_aware_file_index import GitAwareFileIndex
    from .config import Config


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
        config: Optional Config instance for eval harness parameters
    """

    path: Path
    name: str
    url: str | None
    branch: str
    commit_hash: str
    languages: dict[str, int]
    total_files: int
    total_lines: int
    config: "Config | None" = None
    _file_index: "GitAwareFileIndex | None" = field(
        default=None, repr=False, compare=False
    )

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

    @property
    def file_index(self) -> "GitAwareFileIndex":
        """Git-ignore-aware file index scoped to this repository.

        Lazy-built and cached for the lifetime of this Repository instance so
        assessors share one ignore boundary without process-global state.
        """
        if self._file_index is None:
            from ..services.git_aware_file_index import GitAwareFileIndex

            self._file_index = GitAwareFileIndex(self.path)
        return self._file_index

    def assessment_files(self, pattern: str | None = None) -> list[Path]:
        """Return absolute paths of assessment-eligible files (optionally matched).

        On Git index failure, returns an empty list (fail closed — never scan
        ignored trees via unfiltered ``rglob``).
        """
        from ..services.git_aware_file_index import GitAwareFileIndexError

        try:
            return self.file_index.absolute_paths(pattern)
        except GitAwareFileIndexError:
            return []

    def assessment_exists(self, relative: str | Path) -> bool:
        """True when a score-relevant path exists and is not ignore-excluded.

        On Git index failure, returns False (fail closed).
        """
        from ..services.git_aware_file_index import GitAwareFileIndexError

        try:
            return self.file_index.exists(relative)
        except GitAwareFileIndexError:
            return False

    def assessment_match_any(self, patterns: list[str]) -> list[str]:
        """Return relative paths matching any pattern via the assessment file set."""
        from ..services.git_aware_file_index import GitAwareFileIndexError

        try:
            return self.file_index.match_any(patterns)
        except GitAwareFileIndexError:
            return []

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

    @classmethod
    def from_dict(cls, data: dict) -> "Repository":
        """Create Repository from dictionary.

        Skips filesystem validation so cached assessments remain readable
        even if the original repository path no longer exists on disk.
        """
        repo = object.__new__(cls)
        repo.path = Path(data["path"])
        repo.name = data["name"]
        repo.url = data.get("url")
        repo.branch = data["branch"]
        repo.commit_hash = data["commit_hash"]
        repo.languages = data.get("languages", {})
        repo.total_files = data.get("total_files", 0)
        repo.total_lines = data.get("total_lines", 0)
        repo.config = None
        repo._file_index = None
        return repo

    @property
    def primary_language(self) -> str:
        """Get the primary programming language (most files).

        Returns:
            Primary language name, or "Unknown" if no languages detected
        """
        if not self.languages:
            return "Unknown"
        return max(self.languages, key=self.languages.get)

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

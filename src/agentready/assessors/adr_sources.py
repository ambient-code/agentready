"""ADR source abstractions for AdrFrontmatterAssessor.

LocalAdrSource scans the assessed repo's filesystem.
CentralAdrSource reads from a locally cloned central ADR repository,
filtering by applies_to.
"""

from pathlib import Path

from ..models.repository import Repository
from ._adr_utils import parse_frontmatter

# Priority-ordered candidate directories for LocalAdrSource.
_LOCAL_ADR_CANDIDATES: list[str] = [
    "ADR",  # Uppercase — Konflux style, first priority
    "docs/adr",
    "adr",
    "decisions",
    "doc/adr",
]


class LocalAdrSource:
    """Scan the assessed repo filesystem for ADR files.

    Searches candidate directories in priority order and returns the
    first one that contains at least one .md file.
    """

    def find_adr_dir(self, repository: Repository) -> Path | None:
        """Return the first candidate directory containing .md files.

        Args:
            repository: Repository being assessed.

        Returns:
            Path to the ADR directory, or None if not found.
        """
        for candidate in _LOCAL_ADR_CANDIDATES:
            path = repository.path / candidate
            if path.is_dir() and self.get_adr_files(path):
                return path
        return None

    def get_adr_files(self, adr_dir: Path) -> list[Path]:
        """Return all .md files directly in adr_dir (non-recursive).

        Args:
            adr_dir: Directory to search.

        Returns:
            Sorted list of .md Path objects (empty if none found).
        """
        try:
            return sorted(
                p for p in adr_dir.iterdir() if p.suffix == ".md" and p.is_file()
            )
        except OSError:
            return []


def _applies_to_matches(applies_to: str | list, repo_name: str) -> bool:
    """Check whether an applies_to value matches the given repo_name.

    Matching rules:
    - "*" matches everything.
    - A string matches if it equals repo_name, or repo_name ends with /<value>.
    - A list matches if any element matches by the above rules.
    """
    if isinstance(applies_to, list):
        return any(_applies_to_matches(item, repo_name) for item in applies_to)
    if not isinstance(applies_to, str):
        return False
    if applies_to == "*":
        return True
    if applies_to == repo_name:
        return True
    # Full org/repo in applies_to ("org/repo") matched by short name ("repo")
    if applies_to.endswith(f"/{repo_name}"):
        return True
    # Short name in applies_to ("repo") matched by full name ("org/repo")
    if repo_name.endswith(f"/{applies_to}"):
        return True
    return False


class CentralAdrSource:
    """Scan a locally cloned central ADR repo, filtering by applies_to.

    The central repo is expected to be pre-cloned at local_path.
    No network access is performed.

    Args:
        local_path: Root directory of the cloned central ADR repository.
        adr_path: Relative path within local_path containing ADR .md files
                  (e.g. "ADR" or "ADR/"). Trailing slashes are stripped.
    """

    def __init__(self, local_path: Path, adr_path: str) -> None:
        """Initialise CentralAdrSource.

        Args:
            local_path: Root directory of the cloned central ADR repository.
            adr_path: Relative path within local_path containing ADR .md files.

        Raises:
            ValueError: If adr_path is absolute or contains path-traversal ('..').
        """
        stripped = adr_path.rstrip("/")
        if not stripped:
            raise ValueError(
                f"adr_path must be a non-empty relative subpath, got: {adr_path!r}"
            )
        p = Path(stripped)
        if p.is_absolute() or ".." in p.parts:
            raise ValueError(
                f"adr_path must be a relative subpath with no traversal, got: {adr_path!r}"
            )
        self._local_path = local_path
        self._adr_path = stripped

    @property
    def adr_dir(self) -> Path:
        """Absolute path to the ADR subdirectory inside the central repo."""
        return self._local_path / self._adr_path

    def get_matching_adr_files(self, repo_name: str) -> list[Path]:
        """Return ADR files from the central repo that match repo_name.

        A file matches if its applies_to frontmatter field matches repo_name
        by name (short name, full org/repo, list, or wildcard "*").

        Args:
            repo_name: Repository name to match against applies_to.
                       Can be short ("build-service") or full ("org/build-service").

        Returns:
            Sorted list of matching Path objects. Returns [] if local_path
            does not exist or the adr directory is missing/unreadable.
        """
        if not self._local_path.exists():
            return []

        adr_dir = self.adr_dir
        if not adr_dir.is_dir():
            return []

        try:
            md_files = sorted(
                p for p in adr_dir.iterdir() if p.suffix == ".md" and p.is_file()
            )
        except OSError:
            return []

        matched = []
        for f in md_files:
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = parse_frontmatter(content)
            if fm is None:
                continue
            applies_to = fm.get("applies_to")
            if applies_to is None:
                continue
            if _applies_to_matches(applies_to, repo_name):
                matched.append(f)

        return matched

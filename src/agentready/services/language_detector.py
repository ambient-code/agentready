"""Language detection service using file extension analysis."""

import logging
from collections import defaultdict
from pathlib import Path

from .git_aware_file_index import GitAwareFileIndex, GitAwareFileIndexError

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detects programming languages in a repository.

    Uses file extension mapping and respects .gitignore patterns via the
    shared :class:`GitAwareFileIndex` (never an unfiltered ``rglob`` fallback).
    """

    # Extension to language mapping
    EXTENSION_MAP = {
        ".py": "Python",
        ".pyx": "Python",
        ".pyi": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".mjs": "JavaScript",
        ".cjs": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".go": "Go",
        ".java": "Java",
        ".kt": "Kotlin",
        ".kts": "Kotlin",
        ".c": "C",
        ".h": "C",  # Ambiguous but default to C
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".hpp": "C++",
        ".hxx": "C++",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".r": "R",
        ".R": "R",
        ".cs": "C#",
        ".scala": "Scala",
        ".sh": "Shell",
        ".bash": "Shell",
        ".zsh": "Shell",
        ".sql": "SQL",
        ".md": "Markdown",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".json": "JSON",
        ".toml": "TOML",
        ".xml": "XML",
    }

    def __init__(
        self,
        repository_path: Path,
        file_index: GitAwareFileIndex | None = None,
    ):
        """Initialize language detector for repository.

        Args:
            repository_path: Path to git repository root
            file_index: Optional shared index (created if omitted)
        """
        self.repository_path = repository_path
        self.file_index = file_index or GitAwareFileIndex(repository_path)
        self.minimum_file_threshold = 3  # Need 3+ files to count as "using language"

    def _assessment_files(self) -> list[str]:
        try:
            return list(self.file_index.iter_files())
        except GitAwareFileIndexError as exc:
            # Fail closed: do not scan ignored trees via rglob.
            logger.error("Language detection unavailable: %s", exc)
            return []

    def detect_languages(self) -> dict[str, int]:
        """Detect languages in repository with file counts.

        Returns:
            Dictionary mapping language name to file count
            (e.g., {"Python": 42, "JavaScript": 18})

        Only includes languages with >= minimum_file_threshold files.
        """
        language_counts: defaultdict[str, int] = defaultdict(int)

        for file_path in self._assessment_files():
            if not file_path.strip():
                continue

            path = Path(file_path)
            suffix = path.suffix.lower()

            if suffix in self.EXTENSION_MAP:
                language = self.EXTENSION_MAP[suffix]
                language_counts[language] += 1

        # Filter by minimum threshold
        return {
            lang: count
            for lang, count in language_counts.items()
            if count >= self.minimum_file_threshold
        }

    def count_total_files(self) -> int:
        """Count total files in repository (respecting .gitignore).

        Returns:
            Total file count
        """
        return len(self._assessment_files())

    def count_total_lines(self) -> int:
        """Count total lines of code in repository.

        Returns:
            Total line count (excluding empty lines and comments)

        Note: This is a simple implementation. For production use,
        consider using a dedicated tool like cloc or tokei.
        """
        total_lines = 0

        for file_path in self._assessment_files():
            if not file_path.strip():
                continue

            full_path = self.repository_path / file_path

            # Only count text files (skip binaries)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    total_lines += sum(1 for line in f if line.strip())
            except (OSError, UnicodeDecodeError):
                # Skip binary files or unreadable files
                continue

        return total_lines

"""Base assessor interface for attribute evaluation."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models.finding import Finding
from ..models.repository import Repository


class BaseAssessor(ABC):
    """Abstract base class for all attribute assessors.

    Each assessor evaluates one or more related attributes and returns
    structured findings with evidence, scores, and remediation guidance.

    Assessors follow the strategy pattern and are stateless for easy testing
    and parallel execution.
    """

    @property
    @abstractmethod
    def attribute_id(self) -> str:
        """Unique attribute identifier (e.g., 'claude_md_file').

        Must be lowercase snake_case matching the attribute ID in the
        research report and default-weights.yaml.
        """
        pass

    @property
    @abstractmethod
    def tier(self) -> int:
        """Tier 1-4 from research report (1=Essential, 4=Advanced)."""
        pass

    @abstractmethod
    def assess(self, repository: Repository) -> Finding:
        """Execute assessment and return Finding with score, evidence, remediation.

        Args:
            repository: Repository entity with path, languages, metadata

        Returns:
            Finding with status (pass/fail/skipped/error/not_applicable),
            score (0-100 if applicable), evidence, and remediation

        Raises:
            This method should NOT raise exceptions. Handle errors gracefully
            and return Finding.error() or Finding.skipped() instead.
        """
        pass

    def is_applicable(self, repository: Repository) -> bool:
        """Check if attribute applies to this repository.

        Default implementation returns True (attribute applies to all repos).
        Override for language-specific or conditional attributes.

        Args:
            repository: Repository entity with detected languages

        Returns:
            True if attribute should be assessed, False to skip

        Examples:
            - Python-specific check: return "Python" in repository.languages
            - API check: return any openapi/swagger files exist
        """
        return True

    # Root-level manifest files that strongly signal the project's primary language.
    # When file counts are close, these break the tie.
    _LANG_ROOT_MANIFESTS: dict[str, list[str]] = {
        "Go": ["go.mod"],
        "Python": ["pyproject.toml", "setup.py", "setup.cfg"],
        "JavaScript": ["package.json"],
        "TypeScript": ["package.json", "tsconfig.json"],
        "Java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "Rust": ["Cargo.toml"],
        "Ruby": ["Gemfile"],
        "PHP": ["composer.json"],
        "C#": ["*.csproj", "*.sln"],
    }

    def _primary_language(
        self,
        repository: Repository,
        candidates: set[str],
    ) -> str | None:
        """Return the primary programming language among candidates.

        First checks for root-level project manifests.
        If exactly one language is detected by these manifest files, returns it immediately.

        Otherwise, uses file count as the base signal, but when counts are within 30%
        of each other, a root-level project manifest (go.mod, pyproject.toml,
        package.json) acts as tiebreaker — the language whose manifest sits
        at the repo root is treated as primary.

        This handles repos like Go operators with a Python SDK subdirectory,
        where Python may have slightly more files but Go owns the root.
        """

        def has_manifest(lang: str) -> bool:
            """Check if language has root manifest file(s)."""
            manifests = self._LANG_ROOT_MANIFESTS.get(lang, [])
            for manifest in manifests:
                if "*" in manifest:
                    if list(repository.path.glob(manifest)):
                        return True
                else:
                    if (repository.path / manifest).exists():
                        return True
            return False

        # First, check for project files in root
        detected_by_manifest = [lang for lang in candidates if has_manifest(lang)]

        # If exactly one language detected by manifests, return it
        if len(detected_by_manifest) == 1:
            return detected_by_manifest[0]

        # Special handling for JavaScript/TypeScript (share package.json)
        if set(detected_by_manifest) == {"JavaScript", "TypeScript"}:
            # TypeScript projects have tsconfig.json - stronger signal than file count
            if (repository.path / "tsconfig.json").exists():
                return "TypeScript"
            # Otherwise determine by file count
            js_count = repository.languages.get("JavaScript", 0)
            ts_count = repository.languages.get("TypeScript", 0)
            if js_count > ts_count:
                return "JavaScript"
            elif ts_count > js_count:
                return "TypeScript"

        # Use file counts to detect primary language
        lang_counts = {
            lang: repository.languages.get(lang, 0)
            for lang in candidates
            if repository.languages.get(lang, 0) > 0
        }
        if not lang_counts:
            return None

        top_lang = max(lang_counts, key=lambda k: (lang_counts[k], k))
        top_count = lang_counts[top_lang]

        if top_count == 0:
            return None

        # Check if any other candidate is close enough to contest
        close_langs = {
            lang for lang, count in lang_counts.items() if count >= top_count * 0.7
        }
        if len(close_langs) > 1:
            manifest_winners = [
                lang for lang in sorted(close_langs) if has_manifest(lang)
            ]
            if len(manifest_winners) == 1:
                return manifest_winners[0]

        return top_lang

    def _find_go_module_roots(self, repository: Repository) -> list[Path]:
        """Find directories containing go.mod (Go module roots).

        Supports both single-module repos (go.mod at root) and monorepos
        (go.mod in subdirectories at any depth). Excludes vendor and
        testdata directories.
        """
        roots: list[Path] = []
        if (repository.path / "go.mod").exists():
            roots.append(repository.path)
        for gomod in repository.path.rglob("go.mod"):
            if "vendor" in gomod.parts or "testdata" in gomod.parts:
                continue
            if gomod.parent == repository.path:
                continue
            roots.append(gomod.parent)
        return sorted(set(roots))

    def calculate_proportional_score(
        self,
        measured_value: float,
        threshold: float,
        higher_is_better: bool = True,
    ) -> float:
        """Calculate proportional score for partial compliance.

        Uses linear interpolation to score values between 0 and threshold.

        Args:
            measured_value: The measured value (e.g., 65 for coverage %)
            threshold: The target threshold (e.g., 80 for coverage %)
            higher_is_better: True for metrics like coverage, False for complexity

        Returns:
            Score from 0-100

        Examples:
            - Test coverage: 65% measured, 80% threshold, higher_is_better=True
              → 65/80 * 100 = 81.25 score
            - File length: 450 lines measured, 300 threshold, higher_is_better=False
              → 100 - ((450-300)/300)*100 = 50 score
        """
        if higher_is_better:
            # Want higher values (e.g., test coverage, type annotation %)
            if measured_value >= threshold:
                return 100.0
            elif measured_value <= 0:
                return 0.0
            else:
                return min(100.0, (measured_value / threshold) * 100.0)
        else:
            # Want lower values (e.g., complexity, file length)
            if measured_value <= threshold:
                return 100.0
            elif threshold == 0:
                return 0.0  # Avoid division by zero
            else:
                # Degrade linearly, cap at 0
                penalty = ((measured_value - threshold) / threshold) * 100.0
                return max(0.0, 100.0 - penalty)

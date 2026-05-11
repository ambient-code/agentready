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

    def _primary_language(
        self,
        repository: Repository,
        candidates: set[str],
    ) -> str | None:
        """Return the candidate language with the most files in the repo.

        Solves the dispatch problem for multi-language repos: if a repo has
        102 Go files and 11 Python files, Go-specific assessment should run.
        """
        best_lang = None
        best_count = -1
        for lang in candidates:
            count = repository.languages.get(lang, 0)
            if count > best_count:
                best_count = count
                best_lang = lang
        return best_lang if best_count > 0 else None

    def _find_go_module_roots(self, repository: Repository) -> list[Path]:
        """Find directories containing go.mod (Go module roots).

        Supports both single-module repos (go.mod at root) and monorepos
        (go.mod in subdirectories like maas-api/, services/auth/, etc.).
        Excludes vendor directories.
        """
        roots = []
        if (repository.path / "go.mod").exists():
            roots.append(repository.path)
        for gomod in repository.path.glob("*/go.mod"):
            roots.append(gomod.parent)
        return roots

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

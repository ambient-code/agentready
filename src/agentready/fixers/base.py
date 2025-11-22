"""Base fixer interface for automated remediation."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models.finding import Finding
from ..models.fix import Fix
from ..models.repository import Repository


class BaseFixer(ABC):
    """Abstract base class for all attribute fixers.

    Each fixer knows how to automatically remediate a specific failing attribute
    by generating files, modifying configurations, or executing commands.

    Fixers follow the strategy pattern and are stateless for easy testing.
    """

    @property
    @abstractmethod
    def attribute_id(self) -> str:
        """Unique attribute identifier (e.g., 'claude_md_file').

        Must match the attribute ID from assessors.
        """
        pass

    @abstractmethod
    def can_fix(self, finding: Finding) -> bool:
        """Check if this fixer can fix the given finding.

        Args:
            finding: Assessment finding for the attribute

        Returns:
            True if this fixer can generate a fix, False otherwise
        """
        pass

    @abstractmethod
    def generate_fix(self, repository: Repository, finding: Finding) -> Optional[Fix]:
        """Generate a fix for the failing attribute.

        Args:
            repository: Repository entity with path, languages, metadata
            finding: Failing finding to remediate

        Returns:
            Fix object if one can be generated, None if cannot be fixed automatically

        Raises:
            This method should NOT raise exceptions. Return None on errors.
        """
        pass

    def estimate_score_improvement(self, finding: Finding) -> float:
        """Estimate score points gained if fix is applied.

        Args:
            finding: Failing finding

        Returns:
            Estimated points (0-100) that would be gained

        Default implementation: Use attribute default_weight from finding.
        """
        if finding.status == "fail" and finding.attribute.default_weight:
            # Full weight if currently failing (0 points)
            return finding.attribute.default_weight * 100
        return 0.0

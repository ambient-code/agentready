"""Service for orchestrating automated fixes."""

from dataclasses import dataclass
from typing import Callable, List, Optional

from ..fixers.base import BaseFixer
from ..fixers.documentation import CLAUDEmdFixer, GitignoreFixer
from ..fixers.testing import PrecommitHooksFixer
from ..models.assessment import Assessment
from ..models.fix import Fix
from ..models.repository import Repository


@dataclass
class FixPlan:
    """Plan for applying fixes to a repository.

    Attributes:
        fixes: List of fixes to apply
        current_score: Current assessment score
        projected_score: Score after applying fixes
        points_gained: Total points that would be gained
    """

    fixes: List[Fix]
    current_score: float
    projected_score: float
    points_gained: float


class FixerService:
    """Orchestrates automated remediation of failing attributes."""

    def __init__(self):
        """Initialize with all available fixers."""
        self.fixers: List[BaseFixer] = [
            CLAUDEmdFixer(),
            GitignoreFixer(),
            PrecommitHooksFixer(),
        ]

    def generate_fix_plan(
        self,
        assessment: Assessment,
        repository: Repository,
        attribute_ids: List[str] = None,
    ) -> FixPlan:
        """Generate a plan for fixing failing attributes.

        Args:
            assessment: Current assessment results
            repository: Repository to fix
            attribute_ids: Optional list of specific attribute IDs to fix.
                          If None, attempts to fix all failing attributes.

        Returns:
            FixPlan with fixes and score projections
        """
        fixes = []

        # Identify failing findings
        failing_findings = [f for f in assessment.findings if f.status == "fail"]

        # Filter by attribute IDs if specified
        if attribute_ids:
            failing_findings = [
                f for f in failing_findings if f.attribute.id in attribute_ids
            ]

        # Generate fixes for each failing finding
        for finding in failing_findings:
            # Find fixer for this attribute
            fixer = self._find_fixer(finding.attribute.id)
            if fixer and fixer.can_fix(finding):
                fix = fixer.generate_fix(repository, finding)
                if fix:
                    fixes.append(fix)

        # Calculate score projection
        points_gained = sum(f.points_gained for f in fixes)
        projected_score = min(100.0, assessment.overall_score + points_gained)

        return FixPlan(
            fixes=fixes,
            current_score=assessment.overall_score,
            projected_score=projected_score,
            points_gained=points_gained,
        )

    def apply_fixes(
        self,
        fixes: List[Fix],
        dry_run: bool = False,
        progress_callback: Optional[
            Callable[[Fix, str, Optional[bool]], None]
        ] = None,
    ) -> dict:
        """Apply a list of fixes.

        Args:
            fixes: Fixes to apply
            dry_run: If True, don't make changes
            progress_callback: Optional callback(fix, phase, success) where
                phase is "before" or "after", and success is set only for "after".

        Returns:
            Dict with success counts and failures
        """
        results = {"succeeded": 0, "failed": 0, "failures": []}

        for fix in fixes:
            if progress_callback:
                progress_callback(fix, "before", None)
            try:
                success = fix.apply(dry_run=dry_run)
                if progress_callback:
                    progress_callback(fix, "after", success)
                if success:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1
                    results["failures"].append(
                        f"{fix.description}: Unable to apply fix"
                    )
            except Exception as e:
                if progress_callback:
                    progress_callback(fix, "after", False)
                results["failed"] += 1
                results["failures"].append(f"{fix.description}: {str(e)}")

        return results

    def _find_fixer(self, attribute_id: str) -> BaseFixer:
        """Find fixer for attribute ID."""
        for fixer in self.fixers:
            if fixer.attribute_id == attribute_id:
                return fixer
        return None

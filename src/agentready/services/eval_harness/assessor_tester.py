"""Service for testing individual assessor impact on Terminal-Bench."""

import shutil
import statistics
import tempfile
from pathlib import Path
from typing import List

from scipy import stats

from ...assessors import create_all_assessors
from ...models.eval_harness import AssessorImpact, BaselineMetrics, TbenchResult
from ...services.fixer_service import FixerService
from ...services.scanner import Scanner
from .tbench_runner import TbenchRunner


class AssessorTester:
    """Test a single assessor's impact on Terminal-Bench performance.

    This is the core A/B testing logic that:
    1. Clones the repo to a temp directory (fresh copy)
    2. Runs assessment with ONLY the specified assessor
    3. Applies fixes using FixerService (align command)
    4. Runs tbench post-remediation
    5. Calculates delta, p-value, and effect size (Cohen's d)
    6. Returns AssessorImpact with statistical significance
    """

    def __init__(self, tbench_runner: TbenchRunner = None):
        """Initialize with optional tbench runner.

        Args:
            tbench_runner: TbenchRunner instance (defaults to mocked)
        """
        self.tbench_runner = tbench_runner or TbenchRunner(mock=True)
        self.fixer_service = FixerService()

    def test_assessor(
        self,
        assessor_id: str,
        repo_path: Path,
        baseline: BaselineMetrics,
        iterations: int = 5,
        output_dir: Path = None,
    ) -> AssessorImpact:
        """Test single assessor and measure impact against baseline.

        Args:
            assessor_id: ID of assessor to test (e.g., "claude_md_file")
            repo_path: Path to repository to test
            baseline: Baseline metrics for comparison
            iterations: Number of tbench runs post-remediation
            output_dir: Directory to save results (optional)

        Returns:
            AssessorImpact with delta score and statistical significance

        Raises:
            ValueError: If assessor_id is not found
        """
        # 1. Find the assessor
        all_assessors = create_all_assessors()
        assessor = next(
            (a for a in all_assessors if a.attribute_id == assessor_id), None
        )
        if not assessor:
            valid_ids = [a.attribute_id for a in all_assessors]
            raise ValueError(
                f"Assessor '{assessor_id}' not found. Valid IDs: {', '.join(valid_ids)}"
            )

        # 2. Clone repo to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_repo = Path(temp_dir) / "repo"
            shutil.copytree(repo_path, temp_repo, symlinks=True)

            # 3. Run assessment with single assessor
            scanner = Scanner(temp_repo)
            assessment = scanner.scan([assessor], verbose=False)

            # 4. Apply remediation using FixerService
            fix_plan = self.fixer_service.generate_fix_plan(
                assessment, assessment.repository, attribute_ids=[assessor_id]
            )
            remediation_log = []
            if fix_plan.fixes:
                results = self.fixer_service.apply_fixes(fix_plan.fixes, dry_run=False)
                remediation_log = [f.description for f in fix_plan.fixes]
                fixes_applied = results["succeeded"]
            else:
                fixes_applied = 0
                remediation_log = ["No fixes available for this assessor"]

            # 5. Run tbench post-remediation
            post_results: List[TbenchResult] = []
            for i in range(iterations):
                result = self.tbench_runner.run_benchmark(temp_repo)
                post_results.append(result)

                # Save individual run if output_dir provided
                if output_dir:
                    from ...services.eval_harness.baseline import save_to_json

                    run_file = output_dir / f"run_{i+1:03d}.json"
                    save_to_json(result, run_file)

        # 6. Calculate statistics
        post_scores = [r.score for r in post_results]
        baseline_scores = [r.score for r in baseline.raw_results]

        # Mean scores
        baseline_score = baseline.mean_score
        post_score = statistics.mean(post_scores)
        delta_score = post_score - baseline_score

        # Statistical significance (two-sample t-test)
        if len(baseline_scores) > 1 and len(post_scores) > 1:
            t_stat, p_value = stats.ttest_ind(baseline_scores, post_scores)
        else:
            # Not enough samples for t-test
            p_value = 1.0

        # Effect size (Cohen's d)
        effect_size = self._calculate_cohens_d(baseline_scores, post_scores)

        # Significance: p < 0.05 AND effect size > 0.2 (small effect)
        is_significant = p_value < 0.05 and abs(effect_size) > 0.2

        # 7. Save impact results if output_dir provided
        impact = AssessorImpact(
            assessor_id=assessor_id,
            assessor_name=assessor.attribute.name,
            tier=assessor.attribute.tier,
            baseline_score=baseline_score,
            post_remediation_score=post_score,
            delta_score=delta_score,
            p_value=p_value,
            effect_size=effect_size,
            is_significant=is_significant,
            iterations=iterations,
            fixes_applied=fixes_applied,
            remediation_log=remediation_log,
        )

        if output_dir:
            from ...services.eval_harness.baseline import save_to_json

            impact_file = output_dir / "impact.json"
            save_to_json(impact, impact_file)

        return impact

    @staticmethod
    def _calculate_cohens_d(group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size.

        Cohen's d measures the standardized difference between two means.

        Interpretation:
        - |d| < 0.2: negligible
        - 0.2 <= |d| < 0.5: small
        - 0.5 <= |d| < 0.8: medium
        - |d| >= 0.8: large

        Args:
            group1: Baseline scores
            group2: Post-remediation scores

        Returns:
            Cohen's d effect size (positive = improvement, negative = regression)
        """
        if len(group1) < 2 or len(group2) < 2:
            return 0.0

        mean1 = statistics.mean(group1)
        mean2 = statistics.mean(group2)
        std1 = statistics.stdev(group1)
        std2 = statistics.stdev(group2)

        # Pooled standard deviation
        n1 = len(group1)
        n2 = len(group2)
        pooled_std = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
        pooled_std = pooled_std**0.5

        if pooled_std == 0:
            return 0.0

        # Cohen's d = (mean2 - mean1) / pooled_std
        return (mean2 - mean1) / pooled_std

"""Service for aggregating evaluation results from multiple assessor tests."""

from datetime import datetime
from pathlib import Path
from typing import List

from ...models.eval_harness import (
    AssessorImpact,
    BaselineMetrics,
    EvalSummary,
    load_from_json,
    save_to_json,
)


class ResultsAggregator:
    """Aggregate results from multiple assessor tests into summary.

    Responsibilities:
    - Load baseline metrics
    - Discover and load all assessor impact files
    - Create EvalSummary with tier-level statistics
    - Rank assessors by impact
    - Save summary.json
    """

    def aggregate(
        self, eval_harness_dir: Path, output_file: Path = None
    ) -> EvalSummary:
        """Aggregate all evaluation results into summary.

        Args:
            eval_harness_dir: Directory containing baseline and assessors subdirs
                              (e.g., .agentready/eval_harness/)
            output_file: Optional path to save summary.json
                        (defaults to eval_harness_dir/summary.json)

        Returns:
            EvalSummary with complete aggregation

        Raises:
            FileNotFoundError: If baseline or no assessor results found
            ValueError: If eval_harness_dir structure is invalid
        """
        # Validate directory structure
        if not eval_harness_dir.exists():
            raise FileNotFoundError(
                f"Eval harness directory not found: {eval_harness_dir}"
            )

        baseline_dir = eval_harness_dir / "baseline"
        assessors_dir = eval_harness_dir / "assessors"

        if not baseline_dir.exists():
            raise FileNotFoundError(
                f"Baseline directory not found: {baseline_dir}. "
                "Run 'agentready eval-harness baseline' first."
            )

        # Load baseline
        baseline = self._load_baseline(baseline_dir)

        # Load all assessor impacts
        impacts = self._load_assessor_impacts(assessors_dir)

        if not impacts:
            raise FileNotFoundError(
                f"No assessor results found in {assessors_dir}. "
                "Run 'agentready eval-harness test-assessor' or 'run-tier' first."
            )

        # Create summary
        summary = EvalSummary.from_impacts(
            baseline=baseline, impacts=impacts, timestamp=datetime.now()
        )

        # Save summary if output path provided
        if output_file is None:
            output_file = eval_harness_dir / "summary.json"

        save_to_json(summary, output_file)

        return summary

    def _load_baseline(self, baseline_dir: Path) -> BaselineMetrics:
        """Load baseline metrics from directory.

        Args:
            baseline_dir: Directory containing summary.json

        Returns:
            BaselineMetrics

        Raises:
            FileNotFoundError: If summary.json not found
        """
        summary_file = baseline_dir / "summary.json"

        if not summary_file.exists():
            raise FileNotFoundError(
                f"Baseline summary not found: {summary_file}. "
                "Run 'agentready eval-harness baseline' first."
            )

        return load_from_json(BaselineMetrics, summary_file)

    def _load_assessor_impacts(self, assessors_dir: Path) -> List[AssessorImpact]:
        """Load all assessor impact files from assessors directory.

        Args:
            assessors_dir: Directory containing assessor subdirectories
                          (e.g., assessors/claude_md_file/impact.json)

        Returns:
            List of AssessorImpact objects

        Note:
            Silently skips directories without impact.json files.
        """
        impacts = []

        if not assessors_dir.exists():
            return impacts

        # Scan all subdirectories for impact.json
        for assessor_dir in assessors_dir.iterdir():
            if not assessor_dir.is_dir():
                continue

            impact_file = assessor_dir / "impact.json"
            if impact_file.exists():
                try:
                    impact = load_from_json(AssessorImpact, impact_file)
                    impacts.append(impact)
                except Exception as e:
                    # Log warning but continue (don't fail entire aggregation)
                    print(
                        f"Warning: Failed to load {impact_file}: {e}",
                        file=__import__("sys").stderr,
                    )

        return impacts

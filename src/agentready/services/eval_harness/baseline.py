"""Baseline establishment for Terminal-Bench eval harness.

Establishes baseline performance by running Terminal-Bench multiple times
on an unmodified repository and calculating statistical metrics.
"""

import json
from pathlib import Path

from ...models.eval_harness import BaselineMetrics, TbenchResult, save_to_json
from .tbench_runner import TbenchRunner


class BaselineEstablisher:
    """Establishes baseline Terminal-Bench performance.

    Runs tbench multiple times on an unmodified repository to establish
    the starting point for measuring assessor impact. Calculates mean,
    std dev, median, min, max for statistical comparisons.
    """

    def __init__(self, tbench_runner: TbenchRunner = None):
        """Initialize establisher.

        Args:
            tbench_runner: TbenchRunner instance (defaults to mocked)
        """
        self.tbench_runner = tbench_runner or TbenchRunner(mock=True)

    def establish_baseline(
        self, repo_path: Path, iterations: int = 5, output_dir: Path = None
    ) -> BaselineMetrics:
        """Run tbench multiple times and calculate baseline metrics.

        Args:
            repo_path: Path to repository to benchmark
            iterations: Number of tbench runs to perform (default: 5)
            output_dir: Optional directory to save results
                       (default: repo_path/.agentready/eval_harness/baseline)

        Returns:
            BaselineMetrics with calculated statistics

        Raises:
            ValueError: If repo_path is invalid or iterations < 1
        """
        # Validate inputs
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        if iterations < 1:
            raise ValueError(f"Iterations must be >= 1, got {iterations}")

        # Set default output directory
        if output_dir is None:
            output_dir = repo_path / ".agentready" / "eval_harness" / "baseline"

        output_dir.mkdir(parents=True, exist_ok=True)

        # Run tbench multiple times
        results: list[TbenchResult] = []
        for i in range(iterations):
            result = self.tbench_runner.run_benchmark(repo_path)
            results.append(result)

            # Save individual run
            run_file = output_dir / f"run_{i+1:03d}.json"
            save_to_json(result, run_file)

        # Calculate baseline metrics
        baseline = BaselineMetrics.from_results(results)

        # Save baseline summary
        summary_file = output_dir / "summary.json"
        save_to_json(baseline, summary_file)

        return baseline

    def load_baseline(self, baseline_dir: Path) -> BaselineMetrics:
        """Load previously established baseline from directory.

        Args:
            baseline_dir: Directory containing baseline results

        Returns:
            BaselineMetrics loaded from summary.json

        Raises:
            FileNotFoundError: If baseline_dir or summary.json doesn't exist
        """
        summary_file = baseline_dir / "summary.json"

        if not summary_file.exists():
            raise FileNotFoundError(
                f"Baseline summary not found: {summary_file}\n"
                f"Run 'agentready eval-harness baseline' first"
            )

        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return BaselineMetrics.from_dict(data)

"""Compare experiment results."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


@dataclass
class ExperimentResult:
    """Single experiment result."""

    config_name: str
    agent: str
    agentready_score: float
    swebench_score: float
    solved: int
    total: int


class ExperimentComparer:
    """Compare multiple experiment results."""

    def load_result(self, result_file: Path) -> ExperimentResult:
        """Load single experiment result."""
        with open(result_file) as f:
            data = json.load(f)

        return ExperimentResult(**data)

    def compare(self, result_files: List[Path], output_file: Path = None) -> dict:
        """
        Compare multiple experiment results.

        Args:
            result_files: List of result JSON files
            output_file: Where to save comparison

        Returns:
            Comparison dict with summary and deltas
        """
        results = [self.load_result(f) for f in result_files]

        # Find baseline (config_name="baseline")
        baseline_by_agent = {}
        for r in results:
            if r.config_name == "baseline":
                baseline_by_agent[r.agent] = r.swebench_score

        # Calculate deltas from baseline
        comparison = {
            "experiments": [asdict(r) for r in results],
            "summary": {},
            "deltas": {},
        }

        for result in results:
            key = f"{result.config_name}_{result.agent}"
            comparison["summary"][key] = result.swebench_score

            baseline_score = baseline_by_agent.get(result.agent)
            if baseline_score and result.config_name != "baseline":
                delta = result.swebench_score - baseline_score
                comparison["deltas"][f"{key}_vs_baseline"] = delta

        if output_file:
            with open(output_file, "w") as f:
                json.dump(comparison, f, indent=2)

        return comparison

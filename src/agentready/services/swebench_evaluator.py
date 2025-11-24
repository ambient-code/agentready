"""SWE-bench evaluation harness wrapper."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EvaluationResult:
    """SWE-bench evaluation results."""

    dataset: str
    total_instances: int
    resolved_instances: int
    pass_rate: float
    predictions_file: Path
    results_file: Path


class SWEBenchEvaluator:
    """Run SWE-bench evaluation harness."""

    def evaluate(
        self, predictions_file: Path, dataset: str = "lite", output_dir: Path = None
    ) -> EvaluationResult:
        """
        Evaluate predictions using SWE-bench harness.

        Args:
            predictions_file: Path to predictions.jsonl
            dataset: "lite" or "full"
            output_dir: Where to save evaluation results

        Returns:
            EvaluationResult with scores
        """
        if output_dir is None:
            output_dir = predictions_file.parent / "evaluation"
        output_dir.mkdir(parents=True, exist_ok=True)

        dataset_name = f"princeton-nlp/SWE-bench_{dataset.capitalize()}"

        cmd = [
            "python",
            "-m",
            "swebench.harness.run_evaluation",
            "--dataset_name",
            dataset_name,
            "--predictions_path",
            str(predictions_file),
            "--max_workers",
            "8",
            "--cache_level",
            "env",
            "--run_id",
            predictions_file.stem,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=output_dir,
            timeout=14400,  # 4 hour timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"Evaluation failed: {result.stderr}")

        # Parse results
        results_file = output_dir / "results.json"
        with open(results_file) as f:
            results = json.load(f)

        total = results["total_instances"]
        resolved = results["resolved_instances"]

        return EvaluationResult(
            dataset=dataset,
            total_instances=total,
            resolved_instances=resolved,
            pass_rate=resolved / total * 100,
            predictions_file=predictions_file,
            results_file=results_file,
        )

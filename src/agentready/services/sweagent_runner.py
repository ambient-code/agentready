"""SWE-agent batch execution wrapper."""

import subprocess
from pathlib import Path
from typing import Optional


class SWEAgentRunner:
    """Run SWE-bench tasks using SWE-agent."""

    def __init__(
        self,
        model: str = "anthropic/claude-sonnet-4.5",
        max_iterations: int = 30,
        config_file: str = "config/default.yaml",
    ):
        self.model = model
        self.max_iterations = max_iterations
        self.config_file = config_file

    def run_batch(
        self,
        repo_path: Path,
        dataset: str = "lite",
        max_instances: Optional[int] = None,
        output_file: Optional[Path] = None,
    ) -> Path:
        """
        Run SWE-agent on SWE-bench tasks.

        Args:
            repo_path: Path to repository
            dataset: "lite" (300 tasks) or "full" (2,294 tasks)
            max_instances: Optional limit on number of tasks
            output_file: Where to save predictions.jsonl

        Returns:
            Path to predictions.jsonl file
        """
        if output_file is None:
            output_file = Path(f"predictions_sweagent_{dataset}.jsonl")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "sweagent",
            "run-batch",
            "--config",
            self.config_file,
            "--agent.model.name",
            self.model,
            "--instances.type",
            "swe_bench",
            "--instances.subset",
            dataset,
            "--repo_path",
            str(repo_path),
            "--output_dir",
            str(output_file.parent),
        ]

        if max_instances:
            cmd += ["--instances.slice", f":{max_instances}"]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=7200  # 2 hour timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"SWE-agent failed: {result.stderr}")

        return output_file

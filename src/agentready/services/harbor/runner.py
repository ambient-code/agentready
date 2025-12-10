"""Service for executing Harbor benchmarks via CLI."""

import json
import subprocess
from pathlib import Path
from typing import List


class HarborNotInstalledError(Exception):
    """Raised when Harbor framework is not installed."""

    pass


class HarborRunner:
    """Execute Harbor benchmarks via subprocess and capture results."""

    def __init__(self):
        """Initialize Harbor runner and verify installation."""
        self._verify_harbor_installed()

    def _verify_harbor_installed(self) -> None:
        """Verify Harbor CLI is installed and accessible.

        Raises:
            HarborNotInstalledError: If Harbor is not installed or not in PATH
        """
        try:
            subprocess.run(
                ["harbor", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
        except FileNotFoundError:
            raise HarborNotInstalledError(
                "Harbor framework not installed.\n"
                "Install with: uv tool install harbor\n"
                "See: https://harborframework.com/docs/getting-started"
            )
        except subprocess.CalledProcessError as e:
            raise HarborNotInstalledError(f"Harbor CLI error: {e.stderr}")

    def run_benchmark(
        self,
        task_names: List[str],
        output_dir: Path,
        dataset: str = "terminal-bench",
        dataset_version: str = "2.0",
        model: str = "anthropic/claude-sonnet-4-5",
        agent: str = "claude-code",
        n_concurrent: int = 1,
        verbose: bool = True,
    ) -> Path:
        """Run Harbor benchmark and return results directory.

        Args:
            task_names: List of task names to run (e.g., ['adaptive-rejection-sampler'])
            output_dir: Directory to store results
            dataset: Dataset name (default: 'terminal-bench')
            dataset_version: Dataset version (default: '2.0')
            model: Model identifier (default: 'anthropic/claude-sonnet-4-5')
            agent: Agent identifier (default: 'claude-code')
            n_concurrent: Number of concurrent tasks (default: 1)
            verbose: Print Harbor output to console (default: True)

        Returns:
            Path to results directory containing result.json files

        Raises:
            HarborNotInstalledError: If Harbor is not installed
            subprocess.CalledProcessError: If Harbor command fails
            ValueError: If no tasks completed successfully
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build Harbor command
        cmd = [
            "harbor",
            "run",
            "-d",
            f"{dataset}@{dataset_version}",
            "-m",
            model,
            "-a",
            agent,
            "-n",
            str(n_concurrent),
        ]

        # Add task selection if specified
        if task_names:
            # Harbor uses config JSON for task selection
            config_file = output_dir / "config.json"
            config = {
                "datasets": [
                    {
                        "name": dataset,
                        "version": dataset_version,
                        "task_names": task_names,
                    }
                ],
                "agents": [{"name": agent, "model_name": model}],
            }
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            # Use config file instead of CLI args
            cmd = ["harbor", "run", "-c", str(config_file)]

        # Execute Harbor benchmark
        if verbose:
            print(f"Running Harbor benchmark: {' '.join(cmd)}")
            print(f"Tasks: {', '.join(task_names) if task_names else 'all'}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(output_dir),
                capture_output=not verbose,
                text=True,
                check=True,
                timeout=None,  # No timeout for long-running benchmarks
            )

            if verbose and result.stdout:
                print(result.stdout)

        except subprocess.CalledProcessError as e:
            error_msg = f"Harbor benchmark failed: {e.stderr if e.stderr else str(e)}"
            raise subprocess.CalledProcessError(
                e.returncode, e.cmd, e.output, error_msg
            )

        # Find results directory (Harbor creates timestamped subdirectory)
        results_dirs = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime)
        if not results_dirs:
            raise ValueError(f"No results found in {output_dir}")

        results_dir = results_dirs[-1]  # Most recent run

        if verbose:
            print(f"Results stored in: {results_dir}")

        return results_dir

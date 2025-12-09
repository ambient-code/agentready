"""
Terminal-Bench runner with Harbor framework integration.

This module provides functionality to execute real Terminal-Bench evaluations
via the Harbor framework subprocess interface.
"""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentready.services.eval_harness.harbor_config import HarborConfig

# Constants for Harbor subprocess configuration
DEFAULT_TIMEOUT = 3600  # 1 hour timeout per benchmark
DEFAULT_N_CONCURRENT = 1  # Sequential execution (parallelism managed externally)


@dataclass
class TbenchResult:
    """
    Result from a Terminal-Bench evaluation.

    Attributes:
        score: Benchmark accuracy score (0.0 to 1.0)
        task_solved: Whether any tasks were successfully resolved
        is_mocked: True for mocked results, False for real Harbor runs
        resolved_trials: Number of successfully completed tasks
        unresolved_trials: Number of failed tasks
        pass_at_1: Single-attempt success rate
        pass_at_3: Success rate within 3 attempts
    """

    score: float
    task_solved: bool
    is_mocked: bool
    resolved_trials: int = 0
    unresolved_trials: int = 0
    pass_at_1: float = 0.0
    pass_at_3: float = 0.0

    def __post_init__(self):
        """Validate score ranges and trial counts"""
        # Validate score range [0.0, 1.0]
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Score must be 0.0-1.0, got {self.score}")

        # Validate pass rates [0.0, 1.0]
        if not (0.0 <= self.pass_at_1 <= 1.0):
            raise ValueError(f"pass_at_1 must be 0.0-1.0, got {self.pass_at_1}")
        if not (0.0 <= self.pass_at_3 <= 1.0):
            raise ValueError(f"pass_at_3 must be 0.0-1.0, got {self.pass_at_3}")

        # Validate non-negative trial counts
        if self.resolved_trials < 0 or self.unresolved_trials < 0:
            raise ValueError("Trial counts cannot be negative")


def _real_tbench_result(repo_path: Path, config: HarborConfig) -> TbenchResult:
    """
    Execute real Terminal-Bench evaluation via Harbor framework.

    Args:
        repo_path: Path to repository being evaluated
        config: HarborConfig with Harbor subprocess parameters

    Returns:
        TbenchResult with real benchmark metrics

    Raises:
        RuntimeError: If Harbor subprocess times out or fails
        ValueError: If results path validation fails (path traversal)
    """

    # 2. Build harbor run command
    if config.smoketest:
        # SMOKETEST MODE: Use --path to point directly to downloaded task
        # Task path is dynamically discovered by preflight check
        if not config.task_path:
            raise RuntimeError(
                "Smoketest mode requires task_path to be set. "
                "Ensure preflight checks are enabled."
            )
        cmd = [
            "harbor",
            "run",
            "--path",
            str(config.task_path),
            "--agent",
            config.agent,
            "--model",
            config.model,
            "--jobs-dir",
            str(config.jobs_dir),
            "--n-concurrent",
            str(config.n_concurrent),
            "--quiet",  # Reduce output noise
        ]
    else:
        # Full benchmark: use dataset reference
        cmd = [
            "harbor",
            "run",
            "--dataset",
            "terminal-bench@2.0",
            "--agent",
            config.agent,
            "--model",
            config.model,
            "--jobs-dir",
            str(config.jobs_dir),
            "--n-concurrent",
            str(config.n_concurrent),
        ]

    # 3. Prepare environment variables
    # Pass through current environment but ensure API key is set
    # Harbor's claude-code agent expects ANTHROPIC_AUTH_TOKEN (not ANTHROPIC_API_KEY)
    clean_env = os.environ.copy()
    clean_env["ANTHROPIC_API_KEY"] = config.api_key
    clean_env["ANTHROPIC_AUTH_TOKEN"] = config.api_key  # Harbor uses this

    # 4. Execute subprocess with timeout
    try:
        subprocess.run(
            cmd,
            env=clean_env,
            timeout=config.timeout,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Benchmark timed out after {config.timeout}s")
    except subprocess.CalledProcessError as e:
        # Include stderr in error message for debugging
        error_msg = f"Harbor command failed: {e}"
        if e.stderr:
            error_msg += f"\nStderr: {e.stderr}"
        raise RuntimeError(error_msg)

    # 5. Find timestamped results directory created by Harbor
    # Harbor creates: jobs_dir/YYYY-MM-DD__HH-MM-SS/result.json
    result_dirs = sorted(config.jobs_dir.glob("20*"))  # Find timestamped dirs
    if not result_dirs:
        raise RuntimeError(f"No Harbor results directory found in {config.jobs_dir}")

    latest_dir = result_dirs[-1]  # Use most recent
    results_path = latest_dir / "result.json"  # Note: singular "result.json"

    # SECURITY: Path validation (FR-005)
    if not results_path.is_relative_to(config.jobs_dir):
        raise ValueError(f"Invalid results path: {results_path}")

    if not results_path.exists():
        raise FileNotFoundError(f"Harbor results file not found: {results_path}")

    return parse_harbor_results(results_path)


def parse_harbor_results(results_path: Path) -> TbenchResult:
    """
    Parse Harbor framework JSON output.

    Args:
        results_path: Path to Harbor result.json file

    Returns:
        TbenchResult with metrics from Harbor output

    Raises:
        json.JSONDecodeError: If result.json is invalid JSON
        KeyError: If required fields missing from results
    """
    with open(results_path) as f:
        data = json.load(f)

    # Harbor structure: stats.evals.<eval_name>.{n_trials, n_errors, metrics}
    stats = data["stats"]
    evals = stats["evals"]
    n_total_trials = data["n_total_trials"]

    # Get the first (and typically only) eval result
    eval_key = list(evals.keys())[0]
    eval_data = evals[eval_key]

    mean_score = eval_data["metrics"][0]["mean"]

    # In Terminal-Bench: mean_score represents fraction of tasks solved
    # reward_stats shows which tasks got reward > 0
    # Count tasks with reward > 0 as resolved
    reward_stats = eval_data.get("reward_stats", {}).get("reward", {})
    n_solved = sum(
        len(tasks) for reward, tasks in reward_stats.items() if float(reward) > 0
    )

    return TbenchResult(
        score=mean_score,
        task_solved=n_solved > 0,
        is_mocked=False,
        resolved_trials=n_solved,
        unresolved_trials=n_total_trials - n_solved,
        pass_at_1=mean_score,  # Mean score is pass rate
        pass_at_3=0.0,  # Terminal-Bench doesn't provide pass@3
    )

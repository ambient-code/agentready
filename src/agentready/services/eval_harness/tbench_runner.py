"""
Terminal-Bench runner with Harbor framework integration.

This module provides functionality to execute real Terminal-Bench evaluations
via the Harbor framework subprocess interface.
"""

import json
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentready.services.eval_harness.harbor_config import HarborConfig

logger = logging.getLogger(__name__)

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
        trajectory_path: Path to agent trajectory.json file (if available)
    """

    score: float
    task_solved: bool
    is_mocked: bool
    resolved_trials: int = 0
    unresolved_trials: int = 0
    pass_at_1: float = 0.0
    pass_at_3: float = 0.0
    trajectory_path: Path | None = None

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
    # Harbor's claude-code agent has MiniMax API hardcoded - override it
    clean_env = os.environ.copy()

    # Define agent-specific environment variable configurations
    # Structure: (Env Key, Env Value, Is Sensitive)
    agent_env_configs = {
        "claude-code": [
            ("ANTHROPIC_API_KEY", config.api_key, True),
            ("ANTHROPIC_AUTH_TOKEN", config.api_key, True),
            ("ANTHROPIC_BASE_URL", "https://api.anthropic.com", False),
            ("ANTHROPIC_API_BASE", "https://api.anthropic.com", False),
        ],
        "cursor-cli": [
            ("CURSOR_API_KEY", config.api_key, True),
        ],
    }

    if config.agent not in agent_env_configs:
        raise ValueError(f"Invalid agent: {config.agent}")

    # Set environment variables and build display/copyable lists
    env_vars_display = []
    env_vars_copyable = []

    for var_name, var_value, is_sensitive in agent_env_configs[config.agent]:
        clean_env[var_name] = var_value

        # Build display string (truncate sensitive values)
        if is_sensitive:
            display_value = f"{var_value[:20]}..."
        else:
            display_value = var_value
        env_vars_display.append(f"{var_name}={display_value}")

        # Build copyable string (use variable reference for sensitive values)
        if is_sensitive:
            copyable_value = f"${var_name}"
        else:
            copyable_value = var_value
        env_vars_copyable.append(f"{var_name}={copyable_value}")

    # Clear MiniMax settings if present
    clean_env.pop("MINIMAX_API_KEY", None)

    # Print Harbor command for debugging and manual execution
    shell_cmd = " ".join(shlex.quote(arg) for arg in cmd)
    full_cmd_copyable = " ".join(env_vars_copyable) + " " + shell_cmd

    print(f"\n{'=' * 70}")
    print("Harbor Command (Copy/Paste Ready)")
    print(f"{'=' * 70}")
    print(f"\n{full_cmd_copyable}\n")
    print(f"{'=' * 70}")
    print("Command Breakdown:")
    print(f"{'=' * 70}")
    print(f"\nCommand: {shell_cmd}\n")
    print("Environment Variables:")
    for var in env_vars_display:
        print(f"  {var}")
    print(f"\n{'=' * 70}\n")

    # Log full details
    logger.info(f"Executing Harbor command: {shell_cmd}")
    logger.info(f"Environment: {' '.join(env_vars_display)}")

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

    # Find trajectory file: jobs_dir/timestamp/task_name__hash/agent/trajectory.json
    trajectory_path = None
    task_dirs = list(latest_dir.glob("*"))
    for task_dir in task_dirs:
        if task_dir.is_dir() and task_dir.name != "verifier":
            candidate = task_dir / "agent" / "trajectory.json"
            if candidate.exists():
                trajectory_path = candidate
                break

    return parse_harbor_results(results_path, trajectory_path)


def parse_harbor_results(
    results_path: Path, trajectory_path: Path | None = None
) -> TbenchResult:
    """
    Parse Harbor framework JSON output.

    Args:
        results_path: Path to Harbor result.json file
        trajectory_path: Optional path to agent trajectory.json file

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
        trajectory_path=trajectory_path,
    )

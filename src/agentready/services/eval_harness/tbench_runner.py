"""
Terminal-Bench runner with Harbor framework integration.

This module provides functionality to execute real Terminal-Bench evaluations
via the Harbor framework subprocess interface.
"""

import json
import os
import subprocess
import tempfile
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


def _real_tbench_result(repo_path: Path) -> TbenchResult:
    """
    Execute real Terminal-Bench evaluation via Harbor framework.

    Args:
        repo_path: Path to repository being evaluated

    Returns:
        TbenchResult with real benchmark metrics

    Raises:
        RuntimeError: If Harbor subprocess times out or fails
        ValueError: If results path validation fails (path traversal)
    """
    # 1. Create HarborConfig with validation
    config = HarborConfig(
        model=os.environ.get("TBENCH_MODEL", "anthropic/claude-haiku-4-5"),
        agent="claude-code",
        jobs_dir=Path(tempfile.mkdtemp()),
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        timeout=DEFAULT_TIMEOUT,
        n_concurrent=DEFAULT_N_CONCURRENT,
    )

    # 2. Build harbor run command
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

    # 3. Sanitize environment variables (SECURITY: FR-004)
    clean_env = {
        "ANTHROPIC_API_KEY": config.api_key,
        "PATH": os.environ.get("PATH", "/usr/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
    }

    # 4. Execute subprocess with timeout
    try:
        subprocess.run(cmd, env=clean_env, timeout=config.timeout, check=True)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Benchmark timed out after {config.timeout}s")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Harbor command failed: {e}")

    # 5. Parse results.json with path validation (SECURITY: FR-005)
    results_path = config.jobs_dir / "results.json"
    if not results_path.is_relative_to(config.jobs_dir):
        raise ValueError(f"Invalid results path: {results_path}")

    return parse_harbor_results(results_path)


def parse_harbor_results(results_path: Path) -> TbenchResult:
    """
    Parse Harbor framework JSON output.

    Args:
        results_path: Path to Harbor results.json file

    Returns:
        TbenchResult with metrics from Harbor output

    Raises:
        json.JSONDecodeError: If results.json is invalid JSON
        KeyError: If required fields missing from results
    """
    with open(results_path) as f:
        data = json.load(f)

    summary = data["summary"]
    return TbenchResult(
        score=summary["accuracy"],
        task_solved=summary["resolved_trials"] > 0,
        is_mocked=False,
        resolved_trials=summary["resolved_trials"],
        unresolved_trials=summary["unresolved_trials"],
        pass_at_1=summary["pass@1"],
        pass_at_3=summary["pass@3"],
    )

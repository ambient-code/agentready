"""
Parallel benchmark execution for Terminal-Bench eval harness.

This module provides resource-limited parallel execution using ProcessPoolExecutor
to handle large batches of benchmark jobs without exhausting system resources.
"""

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from agentready.services.eval_harness.tbench_runner import (
    TbenchResult,
    _real_tbench_result,
)

# Resource limits for parallel execution
MAX_WORKERS = 4
JOB_TIMEOUT = 3600  # seconds

logger = logging.getLogger(__name__)


def run_batch_benchmarks(repositories: list[Path]) -> list[TbenchResult]:
    """
    Execute Terminal-Bench benchmarks in parallel with resource limits.

    Runs real Harbor framework benchmarks concurrently using ProcessPoolExecutor
    with a maximum of 4 workers to prevent system resource exhaustion. Each job
    has a 3600-second timeout. Failures are logged but don't block other jobs.

    Args:
        repositories: List of repository paths to benchmark

    Returns:
        List of TbenchResult objects for successful benchmarks only.
        Failed benchmarks are logged and excluded from results.

    Examples:
        >>> repos = [Path("/path/to/repo1"), Path("/path/to/repo2")]
        >>> results = run_batch_benchmarks(repos)
        >>> len(results)  # May be less than len(repos) if some failed
        2
    """
    results = []

    # Initialize ProcessPoolExecutor with resource limit
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all benchmark jobs
        future_to_repo = {
            executor.submit(_real_tbench_result, repo): repo for repo in repositories
        }

        # Process results as they complete
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                # Get result with timeout
                result = future.result(timeout=JOB_TIMEOUT)
                results.append(result)
                logger.info(f"Benchmark completed for {repo}: score={result.score}")
            except Exception as exc:
                # Log failure but continue processing other jobs
                logger.error(f"Benchmark failed for {repo}: {exc}")
                continue

    return results

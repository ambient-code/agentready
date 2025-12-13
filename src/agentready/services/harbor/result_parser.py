"""Service for parsing Harbor result.json files."""

import json
from pathlib import Path
from typing import List

from agentready.models.harbor import HarborTaskResult


def parse_harbor_results(results_dir: Path) -> List[HarborTaskResult]:
    """Parse all result.json files in a Harbor run directory.

    Args:
        results_dir: Path to Harbor run directory (e.g., jobs/2025-12-09__22-06-09/)

    Returns:
        List of HarborTaskResult objects

    Raises:
        ValueError: If results_dir doesn't exist or contains no result files
        FileNotFoundError: If results_dir doesn't exist
    """
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    # Find all result.json files in subdirectories (task directories only, not job-level result.json)
    # Task directories are named like "task-name__hash/" while the job result.json is at the root
    all_result_files = list(results_dir.glob("*/result.json"))

    # Filter to only task result files (exclude job-level result.json)
    # Task directories contain "__" in their name (e.g., "build-pmars__abc123")
    result_files = [
        f
        for f in all_result_files
        if "__" in f.parent.name  # Task directories have "__" separator
    ]

    if not result_files:
        raise ValueError(f"No result.json files found in {results_dir}")

    task_results = []
    for result_file in result_files:
        try:
            with open(result_file, "r") as f:
                result_data = json.load(f)
                task_result = HarborTaskResult.from_result_json(result_data)
                task_results.append(task_result)
        except (json.JSONDecodeError, KeyError) as e:
            # Log warning but continue processing other files
            print(f"Warning: Failed to parse {result_file}: {e}")
            continue

    if not task_results:
        raise ValueError(f"No valid task results parsed from {results_dir}")

    return task_results


def parse_single_result(result_file: Path) -> HarborTaskResult:
    """Parse a single result.json file.

    Args:
        result_file: Path to result.json file

    Returns:
        HarborTaskResult object

    Raises:
        FileNotFoundError: If result_file doesn't exist
        json.JSONDecodeError: If result_file is not valid JSON
        KeyError: If required fields are missing
    """
    if not result_file.exists():
        raise FileNotFoundError(f"Result file not found: {result_file}")

    with open(result_file, "r") as f:
        result_data = json.load(f)
        return HarborTaskResult.from_result_json(result_data)

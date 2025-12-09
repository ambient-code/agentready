"""
Benchmark results aggregation for assessor effectiveness analysis.

This module provides functionality to aggregate Terminal-Bench results across
multiple repositories to identify high-impact vs low-impact assessors.
"""

import pandas as pd

# Significance threshold for mean delta (placeholder for statistical test)
SIGNIFICANCE_THRESHOLD = 0.05


def aggregate_results(results: list[dict]) -> pd.DataFrame:
    """
    Aggregate benchmark results by assessor.

    Generic interface for aggregating benchmark results across multiple
    repositories. Follows the principle of "generic interfaces first,
    then consumers" - this function is consumed by CLI commands, reporting
    tools, and analysis scripts.

    Args:
        results: List of dicts with keys:
            - assessor_id: Identifier for the assessor
            - delta_score: Score improvement (can be negative for regressions)

    Returns:
        DataFrame indexed by assessor_id with columns:
            - mean_delta: Average score improvement
            - median_delta: Median score improvement
            - std_delta: Standard deviation of improvements
            - sample_size: Number of repositories tested
            - significant: Boolean indicator (placeholder: abs(mean) > 0.05)
        Sorted by mean_delta descending (highest impact first)

    Examples:
        >>> results = [
        ...     {"assessor_id": "claude_md", "delta_score": 0.12},
        ...     {"assessor_id": "claude_md", "delta_score": 0.10},
        ... ]
        >>> summary = aggregate_results(results)
        >>> summary.loc["claude_md"]["mean_delta"]
        0.11
    """
    # Handle empty results
    if not results:
        return pd.DataFrame(
            columns=[
                "mean_delta",
                "median_delta",
                "std_delta",
                "sample_size",
                "significant",
            ]
        )

    # 1. Create DataFrame from results
    df = pd.DataFrame(results)

    # 2. Aggregate with pandas groupby
    summary = df.groupby("assessor_id").agg(
        {"delta_score": ["mean", "median", "std", "count"]}
    )

    # 3. Rename aggregated columns
    summary.columns = ["mean_delta", "median_delta", "std_delta", "sample_size"]

    # 4. Handle NaN in std (occurs with single value)
    summary["std_delta"] = summary["std_delta"].fillna(0.0)

    # 5. Round to 2 decimal places for readability
    summary = summary.round(2)

    # 5. Add statistical significance placeholder
    # Placeholder: abs(mean_delta) > 0.05
    # Future: Replace with proper statistical test (t-test, etc.)
    summary["significant"] = summary["mean_delta"].abs() > SIGNIFICANCE_THRESHOLD

    # 6. Sort by mean_delta descending (highest impact first)
    summary = summary.sort_values("mean_delta", ascending=False)

    return summary

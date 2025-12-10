"""Service for comparing Harbor benchmark runs and calculating statistical significance."""

from typing import List, Optional

from agentready.models.harbor import HarborComparison, HarborRunMetrics


def compare_runs(
    without_agent: HarborRunMetrics, with_agent: HarborRunMetrics
) -> HarborComparison:
    """Compare two Harbor runs and calculate deltas.

    Args:
        without_agent: Metrics from run without agent file
        with_agent: Metrics from run with agent file

    Returns:
        HarborComparison with calculated deltas and significance

    Raises:
        ValueError: If metrics are incompatible (different task sets)
    """
    # Validate task sets match
    without_tasks = {r.task_name for r in without_agent.task_results}
    with_tasks = {r.task_name for r in with_agent.task_results}

    if without_tasks != with_tasks:
        print(
            f"Warning: Task sets differ. Without: {without_tasks}, With: {with_tasks}. "
            "Comparison may be incomplete."
        )

    # Create comparison object
    comparison = HarborComparison(without_agent=without_agent, with_agent=with_agent)

    # Calculate deltas
    comparison.calculate_deltas()

    # Generate per-task comparison
    comparison.generate_per_task_comparison()

    # Calculate statistical significance
    comparison.statistical_significance = calculate_statistical_significance(
        without_agent, with_agent
    )

    return comparison


def calculate_statistical_significance(
    without_agent: HarborRunMetrics, with_agent: HarborRunMetrics, alpha: float = 0.05
) -> dict:
    """Calculate statistical significance of differences between runs.

    Uses two-sample t-test for continuous metrics and requires scipy.

    Args:
        without_agent: Metrics from run without agent file
        with_agent: Metrics from run with agent file
        alpha: Significance level (default: 0.05 for 95% confidence)

    Returns:
        Dictionary with significance flags and p-values:
        {
            'success_rate_significant': bool,
            'duration_significant': bool,
            'success_rate_p_value': float,
            'duration_p_value': float,
        }
    """
    # Import scipy here to avoid hard dependency
    try:
        from scipy import stats
    except ImportError:
        print(
            "Warning: scipy not installed. "
            "Statistical significance tests unavailable. "
            "Install with: uv pip install scipy"
        )
        return {
            "success_rate_significant": False,
            "duration_significant": False,
            "success_rate_p_value": None,
            "duration_p_value": None,
        }

    # Require minimum sample size for valid statistics
    min_sample_size = 3
    if (
        len(without_agent.task_results) < min_sample_size
        or len(with_agent.task_results) < min_sample_size
    ):
        print(
            f"Warning: Sample size too small (n<{min_sample_size}). "
            "Statistical tests may not be reliable."
        )

    # Extract success rates (binary: 1 for success, 0 for failure)
    without_successes = [1 if r.success else 0 for r in without_agent.task_results]
    with_successes = [1 if r.success else 0 for r in with_agent.task_results]

    # Extract durations (only for completed tasks)
    without_durations = [
        r.duration_sec for r in without_agent.task_results if r.agent_result
    ]
    with_durations = [r.duration_sec for r in with_agent.task_results if r.agent_result]

    results = {}

    # T-test for success rate differences
    if len(without_successes) > 0 and len(with_successes) > 0:
        t_stat, p_value = stats.ttest_ind(without_successes, with_successes)
        results["success_rate_significant"] = p_value < alpha
        results["success_rate_p_value"] = p_value
    else:
        results["success_rate_significant"] = False
        results["success_rate_p_value"] = None

    # T-test for duration differences
    if len(without_durations) > 0 and len(with_durations) > 0:
        t_stat, p_value = stats.ttest_ind(without_durations, with_durations)
        results["duration_significant"] = p_value < alpha
        results["duration_p_value"] = p_value

        # Calculate Cohen's d for effect size
        results["duration_cohens_d"] = calculate_cohens_d(
            without_durations, with_durations
        )
    else:
        results["duration_significant"] = False
        results["duration_p_value"] = None
        results["duration_cohens_d"] = None

    return results


def calculate_cohens_d(group1: List[float], group2: List[float]) -> Optional[float]:
    """Calculate Cohen's d effect size.

    Cohen's d measures the standardized difference between two means:
    - Small effect: 0.2 ≤ |d| < 0.5
    - Medium effect: 0.5 ≤ |d| < 0.8
    - Large effect: |d| ≥ 0.8

    Args:
        group1: First group of values
        group2: Second group of values

    Returns:
        Cohen's d value, or None if calculation not possible
    """
    if not group1 or not group2:
        return None

    # Calculate means
    mean1 = sum(group1) / len(group1)
    mean2 = sum(group2) / len(group2)

    # Calculate pooled standard deviation
    var1 = sum((x - mean1) ** 2 for x in group1) / len(group1)
    var2 = sum((x - mean2) ** 2 for x in group2) / len(group2)
    pooled_std = ((var1 + var2) / 2) ** 0.5

    if pooled_std == 0:
        return None

    return (mean2 - mean1) / pooled_std


def interpret_effect_size(cohens_d: float) -> str:
    """Interpret Cohen's d effect size.

    Args:
        cohens_d: Cohen's d value

    Returns:
        Human-readable interpretation
    """
    abs_d = abs(cohens_d)

    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

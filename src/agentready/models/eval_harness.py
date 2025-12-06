"""Data models for Terminal-Bench eval harness.

The eval harness measures the impact of each AgentReady assessor on
Terminal-Bench (tbench.ai) performance through systematic A/B testing.
"""

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List


@dataclass
class TbenchResult:
    """Result from a single Terminal-Bench run.

    Attributes:
        score: Overall completion rate (0-100)
        completion_rate: Task completion percentage
        pytest_pass_rate: Pytest pass percentage
        latency_ms: Average latency in milliseconds
        timestamp: When this run was executed
        is_mocked: Whether this is mocked data (True) or real tbench (False)
    """

    score: float
    completion_rate: float
    pytest_pass_rate: float
    latency_ms: float
    timestamp: datetime
    is_mocked: bool

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "score": self.score,
            "completion_rate": self.completion_rate,
            "pytest_pass_rate": self.pytest_pass_rate,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
            "is_mocked": self.is_mocked,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TbenchResult":
        """Create from dictionary."""
        return cls(
            score=data["score"],
            completion_rate=data["completion_rate"],
            pytest_pass_rate=data["pytest_pass_rate"],
            latency_ms=data["latency_ms"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            is_mocked=data["is_mocked"],
        )


@dataclass
class BaselineMetrics:
    """Baseline Terminal-Bench performance statistics.

    Calculated from multiple tbench runs on an unmodified repository
    to establish the starting point for measuring assessor impact.

    Attributes:
        mean_score: Average score across all runs
        std_dev: Standard deviation (measure of variance)
        median_score: Median score
        min_score: Minimum score
        max_score: Maximum score
        iterations: Number of runs performed
        raw_results: Individual run results
    """

    mean_score: float
    std_dev: float
    median_score: float
    min_score: float
    max_score: float
    iterations: int
    raw_results: List[TbenchResult] = field(default_factory=list)

    @classmethod
    def from_results(cls, results: List[TbenchResult]) -> "BaselineMetrics":
        """Calculate baseline metrics from run results.

        Args:
            results: List of TbenchResult objects from multiple runs

        Returns:
            BaselineMetrics with calculated statistics

        Raises:
            ValueError: If results list is empty
        """
        if not results:
            raise ValueError("Cannot calculate baseline from empty results")

        scores = [r.score for r in results]

        return cls(
            mean_score=statistics.mean(scores),
            std_dev=statistics.stdev(scores) if len(scores) > 1 else 0.0,
            median_score=statistics.median(scores),
            min_score=min(scores),
            max_score=max(scores),
            iterations=len(results),
            raw_results=results,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "mean_score": self.mean_score,
            "std_dev": self.std_dev,
            "median_score": self.median_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "iterations": self.iterations,
            "raw_results": [r.to_dict() for r in self.raw_results],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BaselineMetrics":
        """Create from dictionary."""
        return cls(
            mean_score=data["mean_score"],
            std_dev=data["std_dev"],
            median_score=data["median_score"],
            min_score=data["min_score"],
            max_score=data["max_score"],
            iterations=data["iterations"],
            raw_results=[
                TbenchResult.from_dict(r) for r in data.get("raw_results", [])
            ],
        )


@dataclass
class AssessorImpact:
    """Impact of a single assessor on Terminal-Bench performance.

    Measures the delta improvement after applying the assessor's remediation,
    with statistical significance testing.

    Attributes:
        assessor_id: Attribute ID (e.g., 'claude_md_file')
        assessor_name: Human-readable name
        tier: Tier 1-4 from research report

        baseline_score: Mean score before remediation
        post_remediation_score: Mean score after remediation
        delta_score: Improvement (positive) or regression (negative)

        p_value: Statistical significance (< 0.05 = significant)
        effect_size: Cohen's d effect size
        is_significant: True if p < 0.05 AND effect_size > 0.2

        iterations: Number of tbench runs performed
        fixes_applied: Number of fixes applied by align command
        remediation_log: List of fix descriptions applied
    """

    assessor_id: str
    assessor_name: str
    tier: int

    baseline_score: float
    post_remediation_score: float
    delta_score: float

    p_value: float
    effect_size: float
    is_significant: bool

    iterations: int
    fixes_applied: int
    remediation_log: List[str] = field(default_factory=list)

    def get_significance_label(self) -> str:
        """Get human-readable significance label.

        Returns:
            "large", "medium", "small", or "negligible"
        """
        if self.effect_size >= 0.8:
            return "large"
        elif self.effect_size >= 0.5:
            return "medium"
        elif self.effect_size >= 0.2:
            return "small"
        else:
            return "negligible"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "assessor_id": self.assessor_id,
            "assessor_name": self.assessor_name,
            "tier": int(self.tier),
            "baseline_score": float(self.baseline_score),
            "post_remediation_score": float(self.post_remediation_score),
            "delta_score": float(self.delta_score),
            "p_value": float(self.p_value),
            "effect_size": float(self.effect_size),
            "is_significant": bool(self.is_significant),
            "significance_label": self.get_significance_label(),
            "iterations": int(self.iterations),
            "fixes_applied": int(self.fixes_applied),
            "remediation_log": list(self.remediation_log),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AssessorImpact":
        """Create from dictionary."""
        return cls(
            assessor_id=data["assessor_id"],
            assessor_name=data["assessor_name"],
            tier=data["tier"],
            baseline_score=data["baseline_score"],
            post_remediation_score=data["post_remediation_score"],
            delta_score=data["delta_score"],
            p_value=data["p_value"],
            effect_size=data["effect_size"],
            is_significant=data["is_significant"],
            iterations=data["iterations"],
            fixes_applied=data["fixes_applied"],
            remediation_log=data.get("remediation_log", []),
        )


@dataclass
class EvalSummary:
    """Complete evaluation summary aggregating all assessor impacts.

    Attributes:
        baseline: Baseline metrics (unmodified repository)
        assessor_impacts: List of individual assessor impacts
        tier_impacts: Average delta score per tier {1: 8.5, 2: 4.2, ...}
        total_assessors_tested: Total number of assessors tested
        significant_improvements: Count of statistically significant improvements
        timestamp: When this evaluation was completed
    """

    baseline: BaselineMetrics
    assessor_impacts: List[AssessorImpact]
    tier_impacts: Dict[int, float]
    total_assessors_tested: int
    significant_improvements: int
    timestamp: datetime

    @classmethod
    def from_impacts(
        cls,
        baseline: BaselineMetrics,
        impacts: List[AssessorImpact],
        timestamp: datetime = None,
    ) -> "EvalSummary":
        """Create summary from baseline and impact list.

        Args:
            baseline: Baseline metrics
            impacts: List of assessor impacts
            timestamp: Optional timestamp (defaults to now)

        Returns:
            EvalSummary with calculated tier impacts
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Calculate tier impacts (average delta per tier)
        tier_groups: Dict[int, List[float]] = {1: [], 2: [], 3: [], 4: []}
        for impact in impacts:
            if impact.tier in tier_groups:
                tier_groups[impact.tier].append(impact.delta_score)

        tier_impacts = {
            tier: statistics.mean(deltas) if deltas else 0.0
            for tier, deltas in tier_groups.items()
        }

        # Count significant improvements
        significant = sum(1 for i in impacts if i.is_significant)

        return cls(
            baseline=baseline,
            assessor_impacts=impacts,
            tier_impacts=tier_impacts,
            total_assessors_tested=len(impacts),
            significant_improvements=significant,
            timestamp=timestamp,
        )

    def get_ranked_assessors(self) -> List[AssessorImpact]:
        """Get assessors ranked by delta score (highest impact first).

        Returns:
            Sorted list of AssessorImpact objects
        """
        return sorted(self.assessor_impacts, key=lambda x: x.delta_score, reverse=True)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "baseline": self.baseline.to_dict(),
            "assessor_impacts": [i.to_dict() for i in self.assessor_impacts],
            "ranked_assessors": [i.to_dict() for i in self.get_ranked_assessors()],
            "tier_impacts": self.tier_impacts,
            "total_assessors_tested": self.total_assessors_tested,
            "significant_improvements": self.significant_improvements,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EvalSummary":
        """Create from dictionary."""
        return cls(
            baseline=BaselineMetrics.from_dict(data["baseline"]),
            assessor_impacts=[
                AssessorImpact.from_dict(i) for i in data["assessor_impacts"]
            ],
            tier_impacts=data["tier_impacts"],
            total_assessors_tested=data["total_assessors_tested"],
            significant_improvements=data["significant_improvements"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


def save_to_json(obj, output_path: Path):
    """Save data model to JSON file.

    Args:
        obj: Object with to_dict() method
        output_path: Path to write JSON file

    Raises:
        AttributeError: If object doesn't have to_dict() method
    """
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(obj.to_dict(), f, indent=2)


def load_from_json(cls, input_path: Path):
    """Load data model from JSON file.

    Args:
        cls: Class with from_dict() class method
        input_path: Path to JSON file

    Returns:
        Instance of cls

    Raises:
        FileNotFoundError: If input_path doesn't exist
        AttributeError: If cls doesn't have from_dict() method
    """
    import json

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return cls.from_dict(data)

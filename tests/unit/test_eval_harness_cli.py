"""
Tests for eval harness CLI aggregation functionality.

Following TDD red-green-refactor workflow:
- Phase 4.1 (RED): Write aggregation tests (T054-T058)
- Phase 4.2 (GREEN): Implement pandas aggregation
- Phase 4.3 (REFACTOR): Add docstrings and documentation
"""

import json
import tempfile
from pathlib import Path

import pytest

from agentready.services.eval_harness.aggregator import aggregate_results


class TestAggregationLogic:
    """Test pandas-based aggregation of benchmark results"""

    def test_summarize_aggregates_by_assessor(self):
        """T054: Verify pandas groupby on assessor_id"""
        # Sample benchmark results
        results = [
            {"assessor_id": "claude_md", "delta_score": 0.12},
            {"assessor_id": "claude_md", "delta_score": 0.10},
            {"assessor_id": "test_coverage", "delta_score": 0.08},
            {"assessor_id": "test_coverage", "delta_score": 0.07},
        ]

        summary = aggregate_results(results)

        # Verify grouping by assessor_id
        assert "claude_md" in summary.index
        assert "test_coverage" in summary.index
        assert len(summary) == 2

    def test_summarize_calculates_mean_median_std(self):
        """T055: Verify correct aggregation functions"""
        results = [
            {"assessor_id": "claude_md", "delta_score": 0.10},
            {"assessor_id": "claude_md", "delta_score": 0.12},
            {"assessor_id": "claude_md", "delta_score": 0.14},
        ]

        summary = aggregate_results(results)

        # Verify statistics calculations
        assert "mean_delta" in summary.columns
        assert "median_delta" in summary.columns
        assert "std_delta" in summary.columns
        assert "sample_size" in summary.columns

        # Verify values
        claude_stats = summary.loc["claude_md"]
        assert claude_stats["mean_delta"] == pytest.approx(0.12, abs=0.01)
        assert claude_stats["median_delta"] == pytest.approx(0.12, abs=0.01)
        assert claude_stats["sample_size"] == 3

    def test_summarize_adds_significance_indicator(self):
        """T056: Verify boolean significant column added"""
        results = [
            {"assessor_id": "high_impact", "delta_score": 0.10},
            {"assessor_id": "high_impact", "delta_score": 0.12},
            {"assessor_id": "low_impact", "delta_score": 0.02},
            {"assessor_id": "low_impact", "delta_score": 0.01},
        ]

        summary = aggregate_results(results)

        # Verify significant column exists
        assert "significant" in summary.columns

        # Verify significance threshold (placeholder: abs(mean_delta) > 0.05)
        assert summary.loc["high_impact"]["significant"]
        assert not summary.loc["low_impact"]["significant"]

    def test_summarize_sorts_by_mean_delta_descending(self):
        """T057: Verify results sorted correctly"""
        results = [
            {"assessor_id": "low", "delta_score": 0.02},
            {"assessor_id": "high", "delta_score": 0.15},
            {"assessor_id": "medium", "delta_score": 0.08},
        ]

        summary = aggregate_results(results)

        # Verify sorting (descending by mean_delta)
        assessors_sorted = summary.index.tolist()
        assert assessors_sorted[0] == "high"
        assert assessors_sorted[1] == "medium"
        assert assessors_sorted[2] == "low"

    def test_summarize_exports_json(self):
        """T058: Verify JSON file written with correct schema"""
        results = [
            {"assessor_id": "claude_md", "delta_score": 0.12},
            {"assessor_id": "test_coverage", "delta_score": 0.08},
        ]

        summary = aggregate_results(results)

        # Verify DataFrame can be exported to JSON
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "aggregation-results.json"
            summary.to_json(output_path, orient="records")

            # Verify file exists and is valid JSON
            assert output_path.exists()
            with open(output_path) as f:
                exported_data = json.load(f)
            assert isinstance(exported_data, list)
            assert len(exported_data) == 2


class TestAggregationEdgeCases:
    """Test edge cases in aggregation"""

    def test_empty_results_list(self):
        """Test handling of empty results"""
        results = []
        summary = aggregate_results(results)
        assert len(summary) == 0

    def test_single_assessor_single_result(self):
        """Test aggregation with minimal data"""
        results = [{"assessor_id": "claude_md", "delta_score": 0.10}]
        summary = aggregate_results(results)
        assert len(summary) == 1
        assert summary.loc["claude_md"]["mean_delta"] == 0.10
        assert summary.loc["claude_md"]["std_delta"] == 0.0  # Single value has no std

    def test_negative_delta_scores(self):
        """Test that negative deltas (regressions) are handled"""
        results = [
            {"assessor_id": "regression", "delta_score": -0.05},
            {"assessor_id": "regression", "delta_score": -0.03},
        ]
        summary = aggregate_results(results)
        assert summary.loc["regression"]["mean_delta"] < 0
        assert not summary.loc["regression"]["significant"]  # abs < 0.05

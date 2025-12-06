"""Unit tests for eval harness data models."""

from datetime import datetime

import pytest

from agentready.models.eval_harness import (
    AssessorImpact,
    BaselineMetrics,
    EvalSummary,
    TbenchResult,
)


class TestTbenchResult:
    """Tests for TbenchResult model."""

    def test_create_tbench_result(self):
        """Test creating a TbenchResult."""
        result = TbenchResult(
            score=75.5,
            completion_rate=72.0,
            pytest_pass_rate=80.0,
            latency_ms=3500.0,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            is_mocked=True,
        )

        assert result.score == 75.5
        assert result.completion_rate == 72.0
        assert result.pytest_pass_rate == 80.0
        assert result.latency_ms == 3500.0
        assert result.is_mocked is True

    def test_to_dict_and_from_dict(self):
        """Test JSON serialization roundtrip."""
        original = TbenchResult(
            score=67.3,
            completion_rate=65.0,
            pytest_pass_rate=70.0,
            latency_ms=4000.0,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            is_mocked=True,
        )

        # Serialize
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["score"] == 67.3
        assert data["is_mocked"] is True

        # Deserialize
        restored = TbenchResult.from_dict(data)
        assert restored.score == original.score
        assert restored.completion_rate == original.completion_rate
        assert restored.timestamp == original.timestamp
        assert restored.is_mocked == original.is_mocked


class TestBaselineMetrics:
    """Tests for BaselineMetrics model."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results for testing."""
        return [
            TbenchResult(
                score=70.0,
                completion_rate=68.0,
                pytest_pass_rate=75.0,
                latency_ms=3500.0,
                timestamp=datetime(2025, 1, 1, 12, 0, 0),
                is_mocked=True,
            ),
            TbenchResult(
                score=72.0,
                completion_rate=70.0,
                pytest_pass_rate=77.0,
                latency_ms=3400.0,
                timestamp=datetime(2025, 1, 1, 12, 1, 0),
                is_mocked=True,
            ),
            TbenchResult(
                score=68.0,
                completion_rate=66.0,
                pytest_pass_rate=73.0,
                latency_ms=3600.0,
                timestamp=datetime(2025, 1, 1, 12, 2, 0),
                is_mocked=True,
            ),
            TbenchResult(
                score=71.0,
                completion_rate=69.0,
                pytest_pass_rate=76.0,
                latency_ms=3450.0,
                timestamp=datetime(2025, 1, 1, 12, 3, 0),
                is_mocked=True,
            ),
            TbenchResult(
                score=69.0,
                completion_rate=67.0,
                pytest_pass_rate=74.0,
                latency_ms=3550.0,
                timestamp=datetime(2025, 1, 1, 12, 4, 0),
                is_mocked=True,
            ),
        ]

    def test_from_results(self, sample_results):
        """Test creating BaselineMetrics from results."""
        baseline = BaselineMetrics.from_results(sample_results)

        # Check calculated statistics
        assert baseline.mean_score == 70.0  # (70+72+68+71+69)/5
        assert baseline.median_score == 70.0
        assert baseline.min_score == 68.0
        assert baseline.max_score == 72.0
        assert baseline.iterations == 5
        assert len(baseline.raw_results) == 5

    def test_std_dev_calculation(self, sample_results):
        """Test standard deviation calculation."""
        baseline = BaselineMetrics.from_results(sample_results)

        # Should be around 1.58 for this data
        assert baseline.std_dev > 0
        assert baseline.std_dev < 2.0

    def test_from_empty_results_raises(self):
        """Test that empty results raises ValueError."""
        with pytest.raises(ValueError, match="Cannot calculate baseline"):
            BaselineMetrics.from_results([])

    def test_to_dict_and_from_dict(self, sample_results):
        """Test JSON serialization roundtrip."""
        original = BaselineMetrics.from_results(sample_results)

        # Serialize
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["mean_score"] == original.mean_score
        assert data["iterations"] == 5

        # Deserialize
        restored = BaselineMetrics.from_dict(data)
        assert restored.mean_score == original.mean_score
        assert restored.std_dev == original.std_dev
        assert restored.iterations == original.iterations
        assert len(restored.raw_results) == len(original.raw_results)


class TestAssessorImpact:
    """Tests for AssessorImpact model."""

    def test_create_assessor_impact(self):
        """Test creating an AssessorImpact."""
        impact = AssessorImpact(
            assessor_id="claude_md_file",
            assessor_name="CLAUDE.md Configuration Files",
            tier=1,
            baseline_score=70.0,
            post_remediation_score=82.5,
            delta_score=12.5,
            p_value=0.003,
            effect_size=0.92,
            is_significant=True,
            iterations=5,
            fixes_applied=2,
            remediation_log=["CREATE CLAUDE.md", "ADD project overview"],
        )

        assert impact.assessor_id == "claude_md_file"
        assert impact.delta_score == 12.5
        assert impact.is_significant is True
        assert len(impact.remediation_log) == 2

    def test_significance_labels(self):
        """Test significance label generation."""
        # Large effect
        large = AssessorImpact(
            assessor_id="test",
            assessor_name="Test",
            tier=1,
            baseline_score=70.0,
            post_remediation_score=85.0,
            delta_score=15.0,
            p_value=0.001,
            effect_size=0.9,  # >= 0.8 = large
            is_significant=True,
            iterations=5,
            fixes_applied=1,
        )
        assert large.get_significance_label() == "large"

        # Medium effect
        medium = AssessorImpact(
            assessor_id="test",
            assessor_name="Test",
            tier=1,
            baseline_score=70.0,
            post_remediation_score=78.0,
            delta_score=8.0,
            p_value=0.02,
            effect_size=0.6,  # >= 0.5 = medium
            is_significant=True,
            iterations=5,
            fixes_applied=1,
        )
        assert medium.get_significance_label() == "medium"

        # Small effect
        small = AssessorImpact(
            assessor_id="test",
            assessor_name="Test",
            tier=1,
            baseline_score=70.0,
            post_remediation_score=73.0,
            delta_score=3.0,
            p_value=0.04,
            effect_size=0.3,  # >= 0.2 = small
            is_significant=True,
            iterations=5,
            fixes_applied=1,
        )
        assert small.get_significance_label() == "small"

        # Negligible effect
        negligible = AssessorImpact(
            assessor_id="test",
            assessor_name="Test",
            tier=1,
            baseline_score=70.0,
            post_remediation_score=71.0,
            delta_score=1.0,
            p_value=0.30,
            effect_size=0.1,  # < 0.2 = negligible
            is_significant=False,
            iterations=5,
            fixes_applied=1,
        )
        assert negligible.get_significance_label() == "negligible"

    def test_to_dict_and_from_dict(self):
        """Test JSON serialization roundtrip."""
        original = AssessorImpact(
            assessor_id="readme_structure",
            assessor_name="README Structure",
            tier=2,
            baseline_score=68.0,
            post_remediation_score=75.0,
            delta_score=7.0,
            p_value=0.015,
            effect_size=0.55,
            is_significant=True,
            iterations=5,
            fixes_applied=3,
            remediation_log=["ADD Installation section", "ADD Usage examples"],
        )

        # Serialize
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["assessor_id"] == "readme_structure"
        assert data["delta_score"] == 7.0
        assert data["significance_label"] == "medium"

        # Deserialize
        restored = AssessorImpact.from_dict(data)
        assert restored.assessor_id == original.assessor_id
        assert restored.delta_score == original.delta_score
        assert restored.is_significant == original.is_significant


class TestEvalSummary:
    """Tests for EvalSummary model."""

    @pytest.fixture
    def sample_baseline(self):
        """Create sample baseline for testing."""
        results = [
            TbenchResult(
                score=70.0,
                completion_rate=68.0,
                pytest_pass_rate=75.0,
                latency_ms=3500.0,
                timestamp=datetime(2025, 1, 1, 12, 0, 0),
                is_mocked=True,
            )
            for _ in range(5)
        ]
        return BaselineMetrics.from_results(results)

    @pytest.fixture
    def sample_impacts(self):
        """Create sample impacts for testing."""
        return [
            AssessorImpact(
                assessor_id="claude_md_file",
                assessor_name="CLAUDE.md",
                tier=1,
                baseline_score=70.0,
                post_remediation_score=82.5,
                delta_score=12.5,
                p_value=0.003,
                effect_size=0.92,
                is_significant=True,
                iterations=5,
                fixes_applied=2,
            ),
            AssessorImpact(
                assessor_id="readme_structure",
                assessor_name="README",
                tier=2,
                baseline_score=70.0,
                post_remediation_score=76.0,
                delta_score=6.0,
                p_value=0.020,
                effect_size=0.45,
                is_significant=True,
                iterations=5,
                fixes_applied=1,
            ),
            AssessorImpact(
                assessor_id="gitignore",
                assessor_name="Gitignore",
                tier=3,
                baseline_score=70.0,
                post_remediation_score=72.0,
                delta_score=2.0,
                p_value=0.15,
                effect_size=0.15,
                is_significant=False,
                iterations=5,
                fixes_applied=1,
            ),
        ]

    def test_from_impacts(self, sample_baseline, sample_impacts):
        """Test creating EvalSummary from impacts."""
        summary = EvalSummary.from_impacts(sample_baseline, sample_impacts)

        assert summary.total_assessors_tested == 3
        assert summary.significant_improvements == 2
        assert 1 in summary.tier_impacts
        assert 2 in summary.tier_impacts
        assert 3 in summary.tier_impacts

    def test_tier_impact_calculation(self, sample_baseline, sample_impacts):
        """Test tier impact aggregation."""
        summary = EvalSummary.from_impacts(sample_baseline, sample_impacts)

        # Tier 1: only claude_md_file (12.5)
        assert summary.tier_impacts[1] == 12.5

        # Tier 2: only readme_structure (6.0)
        assert summary.tier_impacts[2] == 6.0

        # Tier 3: only gitignore (2.0)
        assert summary.tier_impacts[3] == 2.0

        # Tier 4: no assessors (should be 0.0)
        assert summary.tier_impacts[4] == 0.0

    def test_get_ranked_assessors(self, sample_baseline, sample_impacts):
        """Test ranking assessors by delta score."""
        summary = EvalSummary.from_impacts(sample_baseline, sample_impacts)
        ranked = summary.get_ranked_assessors()

        # Should be sorted descending by delta_score
        assert ranked[0].assessor_id == "claude_md_file"  # 12.5
        assert ranked[1].assessor_id == "readme_structure"  # 6.0
        assert ranked[2].assessor_id == "gitignore"  # 2.0

    def test_to_dict_and_from_dict(self, sample_baseline, sample_impacts):
        """Test JSON serialization roundtrip."""
        original = EvalSummary.from_impacts(
            sample_baseline, sample_impacts, timestamp=datetime(2025, 1, 1, 12, 0, 0)
        )

        # Serialize
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["total_assessors_tested"] == 3
        assert data["significant_improvements"] == 2
        assert "ranked_assessors" in data

        # Deserialize
        restored = EvalSummary.from_dict(data)
        assert restored.total_assessors_tested == original.total_assessors_tested
        assert restored.significant_improvements == original.significant_improvements
        assert restored.tier_impacts == original.tier_impacts

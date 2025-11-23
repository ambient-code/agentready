"""Unit tests for batch assessment models."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from agentready.models import (
    BatchAssessment,
    BatchSummary,
    FailureTracker,
    RepositoryResult,
)
from agentready.models.assessment import Assessment
from agentready.models.attribute import Attribute
from agentready.models.finding import Finding
from agentready.models.repository import Repository


@pytest.fixture
def sample_repository():
    """Create a sample repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        # Create .git directory to make it a valid repo
        (repo_path / ".git").mkdir()
        yield Repository(
            path=repo_path,
            name="test-repo",
            url="https://github.com/user/test-repo",
            branch="main",
            commit_hash="abc123",
            languages={"Python": 100},
            total_files=10,
            total_lines=500,
        )


@pytest.fixture
def sample_assessment(sample_repository):
    """Create a sample assessment for testing."""
    attribute = Attribute(
        id="claude_md_file",
        name="CLAUDE.md File",
        description="Repository has CLAUDE.md",
        category="Documentation",
        tier=1,
        criteria="File exists",
        default_weight=0.10,
    )

    finding = Finding(
        attribute=attribute,
        status="pass",
        score=100.0,
        measured_value="present",
        threshold="present",
        evidence=["CLAUDE.md exists"],
        remediation=None,
        error_message=None,
    )

    return Assessment(
        repository=sample_repository,
        timestamp=datetime.now(),
        overall_score=85.0,
        certification_level="Gold",
        attributes_assessed=1,
        attributes_not_assessed=0,
        attributes_total=1,
        findings=[finding],
        config=None,
        duration_seconds=5.0,
    )


class TestRepositoryResult:
    """Test RepositoryResult model."""

    def test_success_result(self, sample_assessment):
        """Test creating a successful result."""
        result = RepositoryResult(
            repository_url="https://github.com/user/repo",
            assessment=sample_assessment,
        )
        assert result.is_success()
        assert result.assessment is not None
        assert result.error is None

    def test_error_result(self):
        """Test creating an error result."""
        result = RepositoryResult(
            repository_url="https://github.com/user/repo",
            assessment=None,
            error="Clone failed",
            error_type="clone_error",
        )
        assert not result.is_success()
        assert result.assessment is None
        assert result.error == "Clone failed"

    def test_validation_both_assessment_and_error(self, sample_assessment):
        """Test that having both assessment and error raises error."""
        with pytest.raises(ValueError):
            RepositoryResult(
                repository_url="https://github.com/user/repo",
                assessment=sample_assessment,
                error="Error",
                error_type="test_error",
            )

    def test_validation_error_without_type(self):
        """Test that error without error_type raises error."""
        with pytest.raises(ValueError):
            RepositoryResult(
                repository_url="https://github.com/user/repo",
                assessment=None,
                error="Clone failed",
            )

    def test_to_dict(self, sample_assessment):
        """Test serialization to dict."""
        result = RepositoryResult(
            repository_url="https://github.com/user/repo",
            assessment=sample_assessment,
            cached=True,
            duration_seconds=5.2,
        )
        data = result.to_dict()
        assert data["repository_url"] == "https://github.com/user/repo"
        assert data["assessment"] is not None
        assert data["cached"] is True
        assert data["duration_seconds"] == 5.2


class TestBatchSummary:
    """Test BatchSummary model."""

    def test_create_summary(self):
        """Test creating a batch summary."""
        summary = BatchSummary(
            total_repositories=5,
            successful_assessments=4,
            failed_assessments=1,
            average_score=82.5,
            score_distribution={
                "Platinum": 1,
                "Gold": 2,
                "Silver": 1,
                "Bronze": 0,
                "Needs Improvement": 0,
            },
            language_breakdown={"Python": 45, "JavaScript": 20},
            top_failing_attributes=[
                {"attribute_id": "test_coverage", "failure_count": 3},
                {"attribute_id": "type_annotations", "failure_count": 2},
            ],
        )
        assert summary.total_repositories == 5
        assert summary.successful_assessments == 4
        assert summary.failed_assessments == 1
        assert summary.average_score == 82.5

    def test_to_dict(self):
        """Test serialization to dict."""
        summary = BatchSummary(
            total_repositories=2,
            successful_assessments=2,
            failed_assessments=0,
            average_score=75.0,
        )
        data = summary.to_dict()
        assert data["total_repositories"] == 2
        assert data["average_score"] == 75.0


class TestFailureTracker:
    """Test FailureTracker model."""

    def test_retryable_error(self):
        """Test retryable error detection."""
        failure = FailureTracker(
            repository_url="https://github.com/user/repo",
            error_type="network_error",
            error_message="Connection timeout",
        )
        assert failure.can_retry is True

    def test_non_retryable_error(self):
        """Test non-retryable error detection."""
        failure = FailureTracker(
            repository_url="https://github.com/user/repo",
            error_type="validation_error",
            error_message="Invalid URL",
        )
        assert failure.can_retry is False

    def test_to_dict(self):
        """Test serialization to dict."""
        failure = FailureTracker(
            repository_url="https://github.com/user/repo",
            error_type="clone_error",
            error_message="Repository not found",
            retry_count=2,
        )
        data = failure.to_dict()
        assert data["repository_url"] == "https://github.com/user/repo"
        assert data["error_type"] == "clone_error"
        assert data["retry_count"] == 2


class TestBatchAssessment:
    """Test BatchAssessment model."""

    def test_create_batch_assessment(self, sample_assessment):
        """Test creating a batch assessment."""
        results = [
            RepositoryResult(
                repository_url="https://github.com/user/repo1",
                assessment=sample_assessment,
            ),
            RepositoryResult(
                repository_url="https://github.com/user/repo2",
                assessment=None,
                error="Clone failed",
                error_type="clone_error",
            ),
        ]

        summary = BatchSummary(
            total_repositories=2,
            successful_assessments=1,
            failed_assessments=1,
            average_score=sample_assessment.overall_score,
        )

        batch = BatchAssessment(
            batch_id="test-batch-001",
            timestamp=datetime.now(),
            results=results,
            summary=summary,
            total_duration_seconds=10.5,
            agentready_version="1.0.0",
            command="assess-batch",
        )

        assert batch.batch_id == "test-batch-001"
        assert len(batch.results) == 2
        assert batch.summary.successful_assessments == 1

    def test_get_success_rate(self, sample_assessment):
        """Test success rate calculation."""
        results = [
            RepositoryResult(
                repository_url="https://github.com/user/repo1",
                assessment=sample_assessment,
            ),
            RepositoryResult(
                repository_url="https://github.com/user/repo2",
                assessment=None,
                error="Clone failed",
                error_type="clone_error",
            ),
        ]

        summary = BatchSummary(
            total_repositories=2,
            successful_assessments=1,
            failed_assessments=1,
            average_score=sample_assessment.overall_score,
        )

        batch = BatchAssessment(
            batch_id="test-batch",
            timestamp=datetime.now(),
            results=results,
            summary=summary,
            total_duration_seconds=10.0,
        )

        assert batch.get_success_rate() == 50.0

    def test_validation_mismatched_successful(self, sample_assessment):
        """Test validation of mismatched successful count."""
        results = [
            RepositoryResult(
                repository_url="https://github.com/user/repo1",
                assessment=sample_assessment,
            ),
        ]

        summary = BatchSummary(
            total_repositories=1,
            successful_assessments=2,  # Mismatch!
            failed_assessments=0,
            average_score=sample_assessment.overall_score,
        )

        with pytest.raises(ValueError):
            BatchAssessment(
                batch_id="test-batch",
                timestamp=datetime.now(),
                results=results,
                summary=summary,
                total_duration_seconds=10.0,
            )

    def test_to_dict(self, sample_assessment):
        """Test serialization to dict."""
        results = [
            RepositoryResult(
                repository_url="https://github.com/user/repo1",
                assessment=sample_assessment,
            ),
        ]

        summary = BatchSummary(
            total_repositories=1,
            successful_assessments=1,
            failed_assessments=0,
            average_score=sample_assessment.overall_score,
        )

        batch = BatchAssessment(
            batch_id="test-batch",
            timestamp=datetime.now(),
            results=results,
            summary=summary,
            total_duration_seconds=10.0,
        )

        data = batch.to_dict()
        assert data["batch_id"] == "test-batch"
        assert len(data["results"]) == 1
        assert "summary" in data

"""Batch assessment models for multi-repository evaluation."""

from dataclasses import dataclass, field
from datetime import datetime

from .assessment import Assessment


@dataclass
class RepositoryResult:
    """Result of assessing a single repository in a batch.

    Attributes:
        repository_url: URL or path of the repository assessed
        assessment: The assessment result (None if failed to assess)
        error: Error message if assessment failed
        error_type: Type of error (e.g., "clone_error", "assessment_error", "validation_error")
        duration_seconds: Time taken to complete
        cached: Whether this result came from cache
    """

    repository_url: str
    assessment: Assessment | None
    error: str | None = None
    error_type: str | None = None
    duration_seconds: float = 0.0
    cached: bool = False

    def __post_init__(self):
        """Validate result data."""
        if self.assessment is None and not self.error:
            raise ValueError("Either assessment or error must be provided")

        if self.assessment is not None and self.error:
            raise ValueError("Cannot have both assessment and error")

        if self.error and not self.error_type:
            raise ValueError("error_type must be provided when error is set")

    def is_success(self) -> bool:
        """Check if assessment was successful."""
        return self.assessment is not None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "repository_url": self.repository_url,
            "assessment": self.assessment.to_dict() if self.assessment else None,
            "error": self.error,
            "error_type": self.error_type,
            "duration_seconds": self.duration_seconds,
            "cached": self.cached,
        }


@dataclass
class BatchSummary:
    """Summary statistics for a batch assessment.

    Attributes:
        total_repositories: Total repositories processed
        successful_assessments: Number of successful assessments
        failed_assessments: Number of failed assessments
        average_score: Average overall score across successful assessments
        score_distribution: Count of repos by certification level
        language_breakdown: Aggregated language detection across repos
        top_failing_attributes: Most frequently failed attributes
    """

    total_repositories: int
    successful_assessments: int
    failed_assessments: int
    average_score: float
    score_distribution: dict[str, int] = field(default_factory=dict)
    language_breakdown: dict[str, int] = field(default_factory=dict)
    top_failing_attributes: list[dict[str, str | int]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_repositories": self.total_repositories,
            "successful_assessments": self.successful_assessments,
            "failed_assessments": self.failed_assessments,
            "average_score": self.average_score,
            "score_distribution": self.score_distribution,
            "language_breakdown": self.language_breakdown,
            "top_failing_attributes": self.top_failing_attributes,
        }


@dataclass
class BatchAssessment:
    """Complete batch assessment of multiple repositories.

    Attributes:
        batch_id: Unique identifier for this batch
        timestamp: When batch started
        results: Individual repository results
        summary: Aggregated statistics
        total_duration_seconds: Total time for entire batch
        agentready_version: AgentReady version used
        command: CLI command that triggered this batch
    """

    batch_id: str
    timestamp: datetime
    results: list[RepositoryResult]
    summary: BatchSummary
    total_duration_seconds: float
    agentready_version: str = "unknown"
    command: str = ""
    schema_version: str = "1.0.0"

    CURRENT_SCHEMA_VERSION = "1.0.0"

    def __post_init__(self):
        """Validate batch assessment data."""
        if not self.results:
            raise ValueError("Batch must have at least one result")

        successful = sum(1 for r in self.results if r.is_success())
        if successful != self.summary.successful_assessments:
            raise ValueError(
                f"Summary successful_assessments ({self.summary.successful_assessments}) "
                f"doesn't match actual successful results ({successful})"
            )

        failed = len(self.results) - successful
        if failed != self.summary.failed_assessments:
            raise ValueError(
                f"Summary failed_assessments ({self.summary.failed_assessments}) "
                f"doesn't match actual failed results ({failed})"
            )

    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if not self.results:
            return 0.0
        return (self.summary.successful_assessments / len(self.results)) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary.to_dict(),
            "total_duration_seconds": self.total_duration_seconds,
            "success_rate": self.get_success_rate(),
            "agentready_version": self.agentready_version,
            "command": self.command,
        }


@dataclass
class FailureTracker:
    """Track failures during batch assessment for reporting.

    Attributes:
        repository_url: URL of failed repository
        error_type: Type of error
        error_message: Detailed error message
        timestamp: When failure occurred
        retry_count: Number of retry attempts
        can_retry: Whether this error is retryable
    """

    repository_url: str
    error_type: str
    error_message: str
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    can_retry: bool = True

    RETRYABLE_ERRORS = {
        "network_error",
        "timeout",
        "rate_limit",
        "temporary_failure",
    }

    def __post_init__(self):
        """Update retry status based on error type."""
        if self.error_type not in self.RETRYABLE_ERRORS:
            self.can_retry = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "repository_url": self.repository_url,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count,
            "can_retry": self.can_retry,
        }

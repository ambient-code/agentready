"""Assessment model representing complete repository evaluation."""

from dataclasses import dataclass, field
from datetime import datetime

from .config import Config
from .discovered_skill import DiscoveredSkill
from .finding import Finding
from .metadata import AssessmentMetadata
from .repository import Repository


@dataclass
class Assessment:
    """Complete evaluation of a repository at a specific point in time.

    Attributes:
        repository: The repository assessed
        timestamp: When assessment was performed
        overall_score: Weighted average score 0-100
        certification_level: Platinum/Gold/Silver/Bronze based on score
        attributes_assessed: Number of successfully evaluated attributes
        attributes_not_assessed: Number of not assessed attributes (skipped, error, not_applicable)
        attributes_total: Total attributes (should be 25)
        findings: Individual attribute results
        config: Custom configuration used (if any)
        duration_seconds: Time taken for assessment
        discovered_skills: Patterns extracted from this assessment (optional)
        metadata: Execution context (version, user, command, timestamp)
        schema_version: Report schema version for backwards compatibility
    """

    repository: Repository
    timestamp: datetime
    overall_score: float
    certification_level: str
    attributes_assessed: int
    attributes_not_assessed: int
    attributes_total: int
    findings: list[Finding]
    config: Config | None
    duration_seconds: float
    discovered_skills: list[DiscoveredSkill] = field(default_factory=list)
    metadata: AssessmentMetadata | None = None
    schema_version: str = "1.0.0"

    VALID_LEVELS = {"Platinum", "Gold", "Silver", "Bronze", "Needs Improvement"}
    CURRENT_SCHEMA_VERSION = "1.0.0"

    def __post_init__(self):
        """Validate assessment data after initialization."""
        if not 0.0 <= self.overall_score <= 100.0:
            raise ValueError(
                f"Overall score must be in range [0.0, 100.0]: {self.overall_score}"
            )

        if self.certification_level not in self.VALID_LEVELS:
            raise ValueError(
                f"Certification level must be one of {self.VALID_LEVELS}: "
                f"{self.certification_level}"
            )

        # Only validate counts if attributes_total > 0 (allows mock assessments for testing)
        if self.attributes_total > 0:
            if (
                self.attributes_assessed + self.attributes_not_assessed
                != self.attributes_total
            ):
                raise ValueError(
                    f"Assessed ({self.attributes_assessed}) + not assessed "
                    f"({self.attributes_not_assessed}) must equal total "
                    f"({self.attributes_total})"
                )

            if len(self.findings) != self.attributes_total:
                raise ValueError(
                    f"Findings count ({len(self.findings)}) must equal "
                    f"attributes total ({self.attributes_total})"
                )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "repository": self.repository.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "overall_score": self.overall_score,
            "certification_level": self.certification_level,
            "attributes_assessed": self.attributes_assessed,
            "attributes_not_assessed": self.attributes_not_assessed,
            "attributes_total": self.attributes_total,
            "findings": [f.to_dict() for f in self.findings],
            "config": self.config.to_dict() if self.config else None,
            "duration_seconds": self.duration_seconds,
            "discovered_skills": [s.to_dict() for s in self.discovered_skills],
        }

    @staticmethod
    def determine_certification_level(score: float) -> str:
        """Determine certification level based on overall score.

        Thresholds:
        - Platinum: 90-100
        - Gold: 75-89
        - Silver: 60-74
        - Bronze: 40-59
        - Needs Improvement: 0-39
        """
        if score >= 90:
            return "Platinum"
        elif score >= 75:
            return "Gold"
        elif score >= 60:
            return "Silver"
        elif score >= 40:
            return "Bronze"
        else:
            return "Needs Improvement"

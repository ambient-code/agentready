"""Finding and Remediation models for assessment results."""

from dataclasses import dataclass

from .attribute import Attribute
from .citation import Citation


@dataclass
class Remediation:
    """Actionable guidance for fixing a failing attribute.

    Attributes:
        summary: One-line summary of what to do
        steps: Ordered steps to remediate
        tools: Tools/packages needed (e.g., "black", "pytest-cov")
        commands: Example commands to run
        examples: Code/config examples
        citations: Links to documentation/research
    """

    summary: str
    steps: list[str]
    tools: list[str]
    commands: list[str]
    examples: list[str]
    citations: list[Citation]

    def __post_init__(self):
        """Validate remediation data after initialization."""
        if not self.summary:
            raise ValueError("Remediation summary must be non-empty")

        if not self.steps:
            raise ValueError("Remediation must have at least one step")

    @classmethod
    def from_dict(cls, data: dict) -> "Remediation":
        """Create Remediation from dictionary."""
        steps = data.get("steps")
        if not steps:
            steps = [data["summary"]]
        return cls(
            summary=data["summary"],
            steps=steps,
            tools=data.get("tools", []),
            commands=data.get("commands", []),
            examples=data.get("examples", []),
            citations=[Citation.from_dict(c) for c in data.get("citations", [])],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": self.summary,
            "steps": self.steps,
            "tools": self.tools,
            "commands": self.commands,
            "examples": self.examples,
            "citations": [c.to_dict() for c in self.citations],
        }


@dataclass
class Finding:
    """Result of assessing a single attribute against a repository.

    Attributes:
        attribute: The attribute being assessed
        status: One of: pass, fail, skipped, error, not_applicable
        score: Score 0-100, or None if skipped/error
        measured_value: Actual measurement (e.g., "847 lines", "63% coverage")
        threshold: Expected threshold (e.g., "<300 lines", ">80% coverage")
        evidence: Specific files/metrics supporting the finding
        remediation: How to fix if failing (None if passing)
        error_message: Error details if status="error"
    """

    attribute: Attribute
    status: str
    score: float | None
    measured_value: str | None
    threshold: str | None
    evidence: list[str]
    remediation: Remediation | None
    error_message: str | None

    VALID_STATUSES = {"pass", "fail", "skipped", "error", "not_applicable"}

    def __post_init__(self):
        """Validate finding data after initialization."""
        if self.status not in self.VALID_STATUSES:
            raise ValueError(
                f"Status must be one of {self.VALID_STATUSES}: {self.status}"
            )

        if self.status in ("pass", "fail"):
            if self.score is None:
                raise ValueError(f"Score required for status {self.status}")
            if not 0.0 <= self.score <= 100.0:
                raise ValueError(f"Score must be in range [0.0, 100.0]: {self.score}")

        if self.status == "error" and not self.error_message:
            raise ValueError("Error message required for status error")

    @classmethod
    def from_dict(cls, data: dict) -> "Finding":
        """Create Finding from dictionary."""
        remediation_data = data.get("remediation")
        return cls(
            attribute=Attribute.from_dict(data["attribute"]),
            status=data["status"],
            score=data.get("score"),
            measured_value=data.get("measured_value"),
            threshold=data.get("threshold"),
            evidence=data.get("evidence", []),
            remediation=(
                Remediation.from_dict(remediation_data) if remediation_data else None
            ),
            error_message=data.get("error_message"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "attribute": self.attribute.to_dict(),
            "status": self.status,
            "score": self.score,
            "measured_value": self.measured_value,
            "threshold": self.threshold,
            "evidence": self.evidence,
            "remediation": self.remediation.to_dict() if self.remediation else None,
            "error_message": self.error_message,
        }

    @classmethod
    def not_applicable(cls, attribute: Attribute, reason: str = "") -> "Finding":
        """Create a not_applicable finding for language-specific attributes."""
        evidence = [reason] if reason else []
        return cls(
            attribute=attribute,
            status="not_applicable",
            score=None,
            measured_value=None,
            threshold=None,
            evidence=evidence,
            remediation=None,
            error_message=None,
        )

    @classmethod
    def skipped(
        cls, attribute: Attribute, reason: str, remediation: str = ""
    ) -> "Finding":
        """Create a skipped finding for missing tools or permission errors."""
        rem = None
        if remediation:
            rem = Remediation(
                summary=remediation,
                steps=[remediation],
                tools=[],
                commands=[],
                examples=[],
                citations=[],
            )

        return cls(
            attribute=attribute,
            status="skipped",
            score=None,
            measured_value=None,
            threshold=None,
            evidence=[reason],
            remediation=rem,
            error_message=None,
        )

    @classmethod
    def error(cls, attribute: Attribute, reason: str) -> "Finding":
        """Create an error finding for unexpected failures."""
        return cls(
            attribute=attribute,
            status="error",
            score=None,
            measured_value=None,
            threshold=None,
            evidence=[],
            remediation=None,
            error_message=reason,
        )

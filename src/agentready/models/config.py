"""Config model for user customization of assessment behavior."""

from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..utils.security import validate_path


class LintSuppressionOptions(BaseModel):
    """Typed options for the lint_suppression_density assessor.

    Attributes:
        pass_per_kloc: Suppressions per 1,000 LOC at or below which score is 100 (pass).
        fail_per_kloc: Suppressions per 1,000 LOC at or above which score is 0 (fail).
        exclude_tests: When True, test files are excluded from suppression scanning.
    """

    pass_per_kloc: Annotated[
        float,
        Field(
            default=5.0, gt=0, description="Pass threshold (suppressions per 1k LOC)"
        ),
    ]
    fail_per_kloc: Annotated[
        float,
        Field(
            default=15.0, gt=0, description="Fail threshold (suppressions per 1k LOC)"
        ),
    ]
    exclude_tests: Annotated[
        bool,
        Field(
            default=False, description="Exclude test files from suppression scanning"
        ),
    ]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_thresholds(self) -> "LintSuppressionOptions":
        if self.fail_per_kloc <= self.pass_per_kloc:
            raise ValueError(
                f"fail_per_kloc ({self.fail_per_kloc}) must exceed "
                f"pass_per_kloc ({self.pass_per_kloc})"
            )
        return self


class AdrSourceConfig(BaseModel):
    """Typed configuration for a central ADR repository.

    Attributes:
        repo: Absolute path to a locally cloned central ADR repository.
        path: Relative subpath within repo containing ADR .md files (default "ADR").
              Must be a relative path with no traversal components.
    """

    repo: Annotated[
        str, Field(description="Absolute path to the locally cloned central ADR repo")
    ]
    path: Annotated[
        str,
        Field(default="ADR", description="Relative subpath within repo (e.g. 'ADR')"),
    ]

    model_config = ConfigDict(extra="forbid")

    @field_validator("path")
    @classmethod
    def validate_path_is_relative(cls, v: str) -> str:
        """Reject empty, absolute, or traversal-containing path values."""
        stripped = v.rstrip("/")
        if not stripped:
            raise ValueError(
                f"adr_source.path must be a non-empty relative path, got: {v!r}"
            )
        p = Path(stripped)
        if p.is_absolute():
            raise ValueError(f"adr_source.path must be a relative path, got: {v!r}")
        if ".." in p.parts:
            raise ValueError(f"adr_source.path must not contain '..', got: {v!r}")
        return stripped

    @field_validator("repo")
    @classmethod
    def validate_repo_nonempty(cls, v: str) -> str:
        """Reject empty repo strings."""
        if not v.strip():
            raise ValueError("adr_source.repo must not be empty")
        return v


class Config(BaseModel):
    """User configuration for customizing assessment behavior.

    Uses Pydantic for automatic validation, type checking, and JSON schema generation.
    Replaces 85 lines of manual validation code with declarative field validators.

    Attributes:
        weights: Custom attribute weights (attribute_id → weight, positive values, allows boosting >1.0)
        excluded_attributes: Attributes to skip during assessment
        language_overrides: Force language detection (lang → glob patterns)
        output_dir: Custom output directory (None uses default .agentready/)
        report_theme: Theme name for HTML reports (default, dark, light, etc.)
        custom_theme: Custom theme colors (overrides report_theme if provided)
        adr_source: Central ADR repository config (repo path + relative ADR subdir)
    """

    weights: Annotated[
        dict[str, float],
        Field(
            default_factory=dict,
            description="Custom attribute weights (positive values, allows boosting >1.0)",
        ),
    ]
    excluded_attributes: Annotated[
        list[str], Field(default_factory=list, description="Attributes to skip")
    ]
    language_overrides: Annotated[
        dict[str, list[str]],
        Field(
            default_factory=dict,
            description="Force language detection (lang → glob patterns)",
        ),
    ]
    output_dir: Annotated[
        Path | None,
        Field(
            default=None,
            description="Custom output directory (None uses .agentready/)",
        ),
    ]
    report_theme: Annotated[
        str, Field(default="default", description="Theme name for HTML reports")
    ]
    custom_theme: Annotated[
        dict[str, str] | None,
        Field(
            default=None,
            description="Custom theme colors (str → str color mappings)",
        ),
    ]
    adr_source: Annotated[
        AdrSourceConfig | None,
        Field(
            default=None,
            description="Central ADR repository config (repo path + relative ADR subdir)",
        ),
    ]
    lint_suppression_density: Annotated[
        LintSuppressionOptions,
        Field(
            default_factory=LintSuppressionOptions,
            description="Options for the lint_suppression_density assessor",
        ),
    ]
    assessor_options: Annotated[
        dict[str, dict[str, Any]],
        Field(
            default_factory=dict,
            description="Per-assessor configuration keyed by attribute_id (generic fallback)",
        ),
    ]

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow Path objects
        extra="forbid",  # Reject unknown fields
    )

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate weight values are positive (no upper limit - allow boosting)."""
        for attr_id, weight in v.items():
            if weight <= 0:
                raise ValueError(f"Weight must be positive for {attr_id}: {weight}")
        return v

    @field_validator("language_overrides")
    @classmethod
    def validate_language_overrides(
        cls, v: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """Validate language override patterns are strings."""
        for lang, patterns in v.items():
            if not all(isinstance(p, str) for p in patterns):
                raise ValueError(
                    f"All language_overrides patterns for '{lang}' must be strings"
                )
        return v

    @field_validator("custom_theme")
    @classmethod
    def validate_custom_theme(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """Validate custom theme values are strings."""
        if v is not None:
            if not all(
                isinstance(k, str) and isinstance(val, str) for k, val in v.items()
            ):
                raise ValueError("All custom_theme keys and values must be strings")
        return v

    @field_validator("output_dir", mode="before")
    @classmethod
    def validate_output_dir_path(cls, v: str | Path | None) -> Path | None:
        """Validate and sanitize output directory path."""
        if v is None:
            return None
        if isinstance(v, str):
            # Security: Use centralized path validation
            return validate_path(v, allow_system_dirs=False, must_exist=False)
        return v

    def model_dump(self, **kwargs) -> dict:
        """Convert to dictionary for JSON serialization.

        Overrides Pydantic's model_dump to handle Path serialization.
        """
        data = super().model_dump(**kwargs)
        if self.output_dir:
            data["output_dir"] = str(self.output_dir)
        return data

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Provides backwards-compatible method name matching old dataclass API.
        """
        return self.model_dump()

    def get_weight(self, attribute_id: str, default: float) -> float:
        """Get weight for attribute, falling back to default if not specified."""
        return self.weights.get(attribute_id, default)

    def is_excluded(self, attribute_id: str) -> bool:
        """Check if attribute is excluded from assessment."""
        return attribute_id in self.excluded_attributes

    @classmethod
    def load_default(cls) -> "Config":
        """Create a default configuration with no customizations.

        Returns:
            Config with empty weights, no exclusions, no overrides
        """
        return cls()

    @classmethod
    def from_yaml_dict(cls, data: dict) -> "Config":
        """Load config from YAML dictionary with Pydantic validation.

        This method replaces the 67-line load_config() function in cli/main.py
        with automatic Pydantic validation and type checking.

        Args:
            data: Dictionary from YAML file (via yaml.safe_load)

        Returns:
            Validated Config instance

        Raises:
            pydantic.ValidationError: If data doesn't match schema
        """
        # Pydantic automatically handles:
        # - Type validation (dict[str, float] for weights, etc.)
        # - Nested structure validation (via field_validators)
        # - Required vs optional fields
        # - Default values
        return cls(**data)

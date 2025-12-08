"""Config model for user customization of assessment behavior."""

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.security import validate_path


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

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow Path objects
        extra="forbid",  # Reject unknown keys
    )

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate weight values are positive."""
        if not v:
            return v

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
            ValueError: If data is not a dictionary or validation fails
        """
        from pydantic import ValidationError

        # Validate data is a dictionary
        if not isinstance(data, dict):
            raise ValueError(
                f"Config must be a dict, got {type(data).__name__}. "
                f"Check your YAML file for proper formatting."
            )

        # Pydantic automatically handles:
        # - Type validation (dict[str, float] for weights, etc.)
        # - Nested structure validation (via field_validators)
        # - Required vs optional fields
        # - Default values
        try:
            return cls(**data)
        except ValidationError as e:
            # Convert Pydantic validation errors to user-friendly ValueError messages
            for error in e.errors():
                field_path = error["loc"]
                field_name = field_path[0] if field_path else "config"
                error_type = error["type"]

                # Provide specific error messages that match test expectations
                if error_type == "extra_forbidden":
                    unknown_keys = [str(loc) for loc in field_path]
                    raise ValueError(
                        f"Unknown config keys: {', '.join(unknown_keys)}"
                    ) from None
                elif field_name == "weights":
                    if error_type == "dict_type":
                        raise ValueError("'weights' must be a dict") from None
                    elif error_type in ("float_parsing", "float_type"):
                        raise ValueError("'weights' values must be numbers") from None
                elif field_name == "excluded_attributes":
                    if error_type == "list_type":
                        raise ValueError(
                            "'excluded_attributes' must be a list"
                        ) from None
                elif field_name == "report_theme":
                    if error_type == "string_type":
                        raise ValueError("'report_theme' must be str") from None

            # If no specific handler matched, re-raise the ValidationError
            raise

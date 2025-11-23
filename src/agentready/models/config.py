"""Config model for user customization of assessment behavior."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """User configuration for customizing assessment behavior.

    Attributes:
        weights: Custom attribute weights (attribute_id → weight)
        excluded_attributes: Attributes to skip
        language_overrides: Force language detection (lang → [patterns])
        output_dir: Custom output directory (None uses default .agentready/)
        report_theme: Theme name for HTML reports (default, dark, light, etc.)
        custom_theme: Custom theme colors (overrides report_theme if provided)
    """

    weights: dict[str, float]
    excluded_attributes: list[str]
    language_overrides: dict[str, list[str]]
    output_dir: Path | None
    report_theme: str = "default"
    custom_theme: dict[str, str] | None = None

    def __post_init__(self):
        """Validate config data after initialization."""
        # Validate weights are positive
        for attr_id, weight in self.weights.items():
            if weight <= 0:
                raise ValueError(f"Weight must be positive for {attr_id}: {weight}")
            if weight > 1.0:
                raise ValueError(f"Weight must be <= 1.0 for {attr_id}: {weight}")

        # Validate weights sum (with tolerance for floating point)
        if self.weights:
            total = sum(self.weights.values())
            tolerance = 0.001
            if abs(total - 1.0) > tolerance:
                raise ValueError(
                    f"Weights must sum to 1.0 (got {total:.4f}, "
                    f"difference: {total - 1.0:+.4f})"
                )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "weights": self.weights,
            "excluded_attributes": self.excluded_attributes,
            "language_overrides": self.language_overrides,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "report_theme": self.report_theme,
            "custom_theme": self.custom_theme,
        }

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
        return cls(
            weights={},
            excluded_attributes=[],
            language_overrides={},
            output_dir=None,
            report_theme="default",
            custom_theme=None,
        )

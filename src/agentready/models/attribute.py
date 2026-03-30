"""Attribute model defining one of the 25 agent-ready quality attributes."""

from dataclasses import dataclass


@dataclass
class Attribute:
    """Defines an agent-ready quality attribute from the research report.

    Attributes:
        id: Unique identifier (e.g., "claude_md_file", "test_coverage")
        name: Human-readable name (e.g., "CLAUDE.md Configuration Files")
        category: Research report section (e.g., "Context Window Optimization")
        tier: Priority tier 1-4 (1=Essential, 4=Advanced)
        description: What this attribute measures
        criteria: Measurable criteria for passing
        default_weight: Default weight in scoring (0.0-1.0)
    """

    id: str
    name: str
    category: str
    tier: int
    description: str
    criteria: str
    default_weight: float

    def __post_init__(self):
        """Validate attribute data after initialization."""
        if not self.id.islower() or " " in self.id:
            raise ValueError(f"Attribute ID must be lowercase snake_case: {self.id}")

        if self.tier not in (1, 2, 3, 4):
            raise ValueError(f"Tier must be 1, 2, 3, or 4: {self.tier}")

        if not 0.0 <= self.default_weight <= 1.0:
            raise ValueError(
                f"Default weight must be in range [0.0, 1.0]: {self.default_weight}"
            )

    @classmethod
    def from_dict(cls, data: dict) -> "Attribute":
        """Create Attribute from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            tier=data["tier"],
            description=data["description"],
            criteria=data["criteria"],
            default_weight=data["default_weight"],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "tier": self.tier,
            "description": self.description,
            "criteria": self.criteria,
            "default_weight": self.default_weight,
        }

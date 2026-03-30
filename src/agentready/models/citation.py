"""Citation model for authoritative sources from research report."""

from dataclasses import dataclass


@dataclass
class Citation:
    """Reference to authoritative source from research report.

    Attributes:
        source: Source name (e.g., "Anthropic Engineering Blog")
        title: Article/paper title
        url: Link to source (optional)
        relevance: Why this citation supports the attribute
    """

    source: str
    title: str
    url: str | None
    relevance: str

    def __post_init__(self):
        """Validate citation data after initialization."""
        if not self.source:
            raise ValueError("Citation source must be non-empty")

        if not self.title:
            raise ValueError("Citation title must be non-empty")

        if not self.relevance:
            raise ValueError("Citation relevance must be non-empty")

    @classmethod
    def from_dict(cls, data: dict) -> "Citation":
        """Create Citation from dictionary."""
        return cls(
            source=data["source"],
            title=data["title"],
            url=data.get("url"),
            relevance=data["relevance"],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "relevance": self.relevance,
        }

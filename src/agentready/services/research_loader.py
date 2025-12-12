"""Research loader service for loading and validating research reports."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ResearchMetadata:
    """Metadata extracted from research report."""

    version: str
    date: str
    attribute_count: int
    tier_count: int
    reference_count: int


class ResearchLoader:
    """Loads and validates bundled research report.

    Supports loading from bundled data, custom paths, and URLs.
    Validates structure per FR-024.
    """

    def __init__(self, data_dir: Path | None = None):
        """Initialize research loader.

        Args:
            data_dir: Directory containing research report
                     (defaults to package data directory)
        """
        if data_dir is None:
            # Default to package data directory
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = data_dir

        self.research_file = self.data_dir / "RESEARCH_REPORT.md"

    def load_research_report(self) -> str:
        """Load research report content.

        Returns:
            Research report markdown content

        Raises:
            FileNotFoundError: If research report not found
        """
        if not self.research_file.exists():
            raise FileNotFoundError(f"Research report not found: {self.research_file}")

        with open(self.research_file, "r", encoding="utf-8") as f:
            return f.read()

    def extract_metadata(self, content: str) -> ResearchMetadata:
        """Extract metadata from research report.

        Args:
            content: Research report markdown content

        Returns:
            ResearchMetadata with version, date, counts

        Raises:
            ValueError: If metadata cannot be extracted
        """
        # Extract version and date from YAML frontmatter
        frontmatter_match = re.search(
            r"^---\s*\nversion:\s*([^\n]+)\s*\ndate:\s*([^\n]+)\s*\n---",
            content,
            re.MULTILINE,
        )

        if frontmatter_match:
            version = frontmatter_match.group(1).strip()
            date = frontmatter_match.group(2).strip()
        else:
            # Default version if not found
            version = "1.0.0"
            date = "unknown"

        # Count attributes (look for ### headings with numbering like "1.1", "2.3", etc.)
        attribute_pattern = r"^###\s+\d+\.\d+\s+"
        attribute_count = len(re.findall(attribute_pattern, content, re.MULTILINE))

        # Count tiers (look for tier headings)
        tier_pattern = r"^###\s+Tier\s+\d+:"
        tier_count = len(re.findall(tier_pattern, content, re.MULTILINE))

        # Count references (look for citation patterns)
        reference_pattern = r"^\d+\.\s+\[.+?\]\(.+?\)"
        reference_count = len(re.findall(reference_pattern, content, re.MULTILINE))

        return ResearchMetadata(
            version=version,
            date=date,
            attribute_count=attribute_count,
            tier_count=tier_count,
            reference_count=reference_count,
        )

    def validate_structure(self, content: str) -> tuple[bool, list[str], list[str]]:
        """Validate research report structure.

        Args:
            content: Research report markdown content

        Returns:
            Tuple of (is_valid, errors, warnings)
            - errors: Blocking issues that prevent usage
            - warnings: Non-critical issues that can be ignored

        Validation rules per FR-024:
        - Errors: Missing metadata, incorrect attribute count, missing measurable criteria
        - Warnings: Missing impact sections, fewer references than recommended
        """
        errors = []
        warnings = []

        metadata = self.extract_metadata(content)

        # Check attribute count (should be 25)
        if metadata.attribute_count != 25:
            errors.append(f"Expected 25 attributes, found {metadata.attribute_count}")

        # Check tier count (should be 4)
        if metadata.tier_count < 4:
            errors.append(f"Expected 4 tiers, found {metadata.tier_count}")

        # Check reference count (recommend 20+)
        if metadata.reference_count < 20:
            warnings.append(
                f"Only {metadata.reference_count} references "
                f"(recommend 20+ for evidence-based design)"
            )

        # Check for "Measurable Criteria" sections
        measurable_criteria_pattern = r"\*\*Measurable Criteria:\*\*"
        criteria_count = len(
            re.findall(measurable_criteria_pattern, content, re.MULTILINE)
        )

        if criteria_count < 25:
            errors.append(
                f"Missing 'Measurable Criteria' sections (found {criteria_count}/25)"
            )

        # Check for "Impact on Agent Behavior" sections (warning only)
        impact_pattern = r"\*\*Impact on Agent Behavior:\*\*"
        impact_count = len(re.findall(impact_pattern, content, re.MULTILINE))

        if impact_count < 25:
            warnings.append(
                f"{25 - impact_count} attributes missing "
                f"'Impact on Agent Behavior' sections"
            )

        is_valid = len(errors) == 0

        return is_valid, errors, warnings

    def load_and_validate(
        self,
    ) -> tuple[str, ResearchMetadata, bool, list[str], list[str]]:
        """Load research report and validate structure.

        Returns:
            Tuple of (content, metadata, is_valid, errors, warnings)

        Raises:
            FileNotFoundError: If research report not found
        """
        content = self.load_research_report()
        metadata = self.extract_metadata(content)
        is_valid, errors, warnings = self.validate_structure(content)

        return content, metadata, is_valid, errors, warnings

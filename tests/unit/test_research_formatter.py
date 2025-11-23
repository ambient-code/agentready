"""Unit tests for research formatter."""

import pytest

from agentready.services.research_formatter import ResearchFormatter


@pytest.fixture
def formatter():
    """Create ResearchFormatter instance."""
    return ResearchFormatter()


@pytest.fixture
def sample_research_report():
    """Sample research report content for testing."""
    return """---
version: 1.0.0
date: 2025-11-20
---

# Agent-Ready Codebase Attributes

**Version:** 1.0.0
**Date:** 2025-11-20

## 1. CONTEXT WINDOW OPTIMIZATION

### 1.1 First Attribute

**Definition:** Test definition

**Why It Matters:** Test rationale

**Impact on Agent Behavior:**
- Impact 1
- Impact 2

**Measurable Criteria:**
- Criterion 1
- Criterion 2

**Citations:**
- Source 1

---

### 1.2 Second Attribute

**Definition:** Another test definition

**Measurable Criteria:**
- Criterion A

**Citations:**
- Source A

---

## IMPLEMENTATION PRIORITIES

### Tier 1: Essential (Must-Have)
- 1.1 First Attribute

### Tier 2: Critical (Should-Have)
- 1.2 Second Attribute

### Tier 3: Important (Nice-to-Have)

### Tier 4: Advanced (Optimization)

---

## REFERENCES & CITATIONS

1. Source 1
2. Source A
"""


class TestGenerateTemplate:
    """Tests for generate_template method."""

    def test_generates_valid_template(self, formatter):
        """Test that template includes all required sections."""
        template = formatter.generate_template()

        # Check for YAML frontmatter
        assert "---\nversion: 1.0.0" in template
        assert "date:" in template

        # Check for required sections
        assert "# Agent-Ready Codebase Attributes" in template
        assert "## Executive Summary" in template
        assert "## 1. CONTEXT WINDOW OPTIMIZATION" in template
        assert "## IMPLEMENTATION PRIORITIES" in template
        assert "### Tier 1: Essential" in template
        assert "### Tier 2: Critical" in template
        assert "### Tier 3: Important" in template
        assert "### Tier 4: Advanced" in template
        assert "## REFERENCES & CITATIONS" in template

    def test_template_has_attribute_structure(self, formatter):
        """Test that template includes proper attribute structure."""
        template = formatter.generate_template()

        assert "**Definition:**" in template
        assert "**Why It Matters:**" in template
        assert "**Impact on Agent Behavior:**" in template
        assert "**Measurable Criteria:**" in template
        assert "**Citations:**" in template


class TestAddAttribute:
    """Tests for add_attribute method."""

    def test_adds_attribute_to_existing_category(
        self, formatter, sample_research_report
    ):
        """Test adding attribute to existing category."""
        result = formatter.add_attribute(
            sample_research_report,
            "1.3",
            "Third Attribute",
            tier=1,
            category="1. CONTEXT WINDOW OPTIMIZATION",
        )

        # Check attribute was added
        assert "### 1.3 Third Attribute" in result
        assert "**Definition:** [TODO: Add clear definition]" in result
        assert "**Measurable Criteria:**" in result

        # Check tier assignment was added
        assert "- 1.3 Third Attribute" in result

    def test_adds_attribute_to_new_category(self, formatter, sample_research_report):
        """Test adding attribute creates new category if needed."""
        result = formatter.add_attribute(
            sample_research_report,
            "5.1",
            "New Category Attribute",
            tier=2,
            category="5. NEW CATEGORY",
        )

        # Check category was created
        assert "## 5. NEW CATEGORY" in result
        assert "### 5.1 New Category Attribute" in result

    def test_adds_to_correct_tier(self, formatter, sample_research_report):
        """Test attribute is added to correct tier section."""
        result = formatter.add_attribute(
            sample_research_report,
            "2.1",
            "Tier 3 Attribute",
            tier=3,
            category="Testing",
        )

        # Find Tier 3 section and verify attribute is listed
        tier3_start = result.index("### Tier 3:")
        tier4_start = result.index("### Tier 4:")
        tier3_section = result[tier3_start:tier4_start]

        assert "- 2.1 Tier 3 Attribute" in tier3_section


class TestBumpVersion:
    """Tests for bump_version method."""

    def test_bump_patch_version(self, formatter, sample_research_report):
        """Test bumping patch version."""
        result = formatter.bump_version(sample_research_report, "patch")

        assert "version: 1.0.1" in result
        # Date should be updated to today
        from datetime import date

        today = date.today().isoformat()
        assert f"date: {today}" in result

    def test_bump_minor_version(self, formatter, sample_research_report):
        """Test bumping minor version."""
        result = formatter.bump_version(sample_research_report, "minor")

        assert "version: 1.1.0" in result

    def test_bump_major_version(self, formatter, sample_research_report):
        """Test bumping major version."""
        result = formatter.bump_version(sample_research_report, "major")

        assert "version: 2.0.0" in result

    def test_bump_minor_resets_patch(self, formatter):
        """Test that bumping minor resets patch to 0."""
        content = """---
version: 1.2.5
date: 2025-01-01
---
"""
        result = formatter.bump_version(content, "minor")
        assert "version: 1.3.0" in result

    def test_bump_major_resets_minor_and_patch(self, formatter):
        """Test that bumping major resets minor and patch to 0."""
        content = """---
version: 1.2.5
date: 2025-01-01
---
"""
        result = formatter.bump_version(content, "major")
        assert "version: 2.0.0" in result

    def test_raises_on_missing_version(self, formatter):
        """Test error handling when version is missing."""
        content = "# No version here"
        with pytest.raises(ValueError, match="Could not find version"):
            formatter.bump_version(content, "patch")

    def test_raises_on_invalid_bump_type(self, formatter, sample_research_report):
        """Test error handling for invalid bump type."""
        with pytest.raises(ValueError, match="Invalid bump type"):
            formatter.bump_version(sample_research_report, "invalid")


class TestSetVersion:
    """Tests for set_version method."""

    def test_sets_explicit_version(self, formatter, sample_research_report):
        """Test setting explicit version."""
        result = formatter.set_version(sample_research_report, "3.5.2")

        assert "version: 3.5.2" in result
        assert "**Version:** 3.5.2" in result

    def test_updates_date(self, formatter, sample_research_report):
        """Test that setting version updates date."""
        from datetime import date

        today = date.today().isoformat()

        result = formatter.set_version(sample_research_report, "2.0.0")

        assert f"date: {today}" in result
        assert f"**Date:** {today}" in result


class TestFormatReport:
    """Tests for format_report method."""

    def test_removes_trailing_whitespace(self, formatter):
        """Test removal of trailing whitespace."""
        content = "# Title   \n\nParagraph with trailing spaces   \n"
        result = formatter.format_report(content)

        assert result == "# Title\n\nParagraph with trailing spaces\n"

    def test_ensures_single_newline_at_end(self, formatter):
        """Test file ends with exactly one newline."""
        content = "# Title\n\n\n"
        result = formatter.format_report(content)

        assert result.endswith("\n")
        assert not result.endswith("\n\n")

    def test_limits_consecutive_blank_lines(self, formatter):
        """Test that multiple blank lines are reduced."""
        content = "# Title\n\n\n\n\nContent"
        result = formatter.format_report(content)

        # Should have max 2 consecutive blank lines (3 newlines)
        assert "\n\n\n\n" not in result

    def test_consistent_heading_spacing(self, formatter):
        """Test consistent spacing after headings."""
        content = "# Title\nNo space after heading"
        result = formatter.format_report(content)

        assert "# Title\n\nNo space after heading" in result


class TestExtractAttributeIds:
    """Tests for extract_attribute_ids method."""

    def test_extracts_attribute_ids(self, formatter, sample_research_report):
        """Test extraction of attribute IDs."""
        ids = formatter.extract_attribute_ids(sample_research_report)

        assert ids == ["1.1", "1.2"]

    def test_returns_empty_list_when_no_attributes(self, formatter):
        """Test empty list when no attributes found."""
        content = "# No attributes here"
        ids = formatter.extract_attribute_ids(content)

        assert ids == []


class TestValidateAttributeNumbering:
    """Tests for validate_attribute_numbering method."""

    def test_validates_correct_numbering(self, formatter, sample_research_report):
        """Test validation passes for correct numbering."""
        is_valid, errors = formatter.validate_attribute_numbering(
            sample_research_report
        )

        assert is_valid
        assert errors == []

    def test_detects_duplicate_ids(self, formatter):
        """Test detection of duplicate attribute IDs."""
        content = """
### 1.1 First
### 1.1 Duplicate
"""
        is_valid, errors = formatter.validate_attribute_numbering(content)

        assert not is_valid
        assert any("Duplicate attribute ID: 1.1" in e for e in errors)

    def test_detects_invalid_format(self, formatter):
        """Test detection of invalid attribute ID format."""
        content = """
### 1.a Invalid
"""
        is_valid, errors = formatter.validate_attribute_numbering(content)

        assert not is_valid
        assert any("Invalid attribute ID format" in e for e in errors)

    def test_detects_non_sequential_numbering(self, formatter):
        """Test detection of non-sequential minor numbers."""
        content = """
### 1.1 First
### 1.3 Skipped 1.2
"""
        is_valid, errors = formatter.validate_attribute_numbering(content)

        assert not is_valid
        assert any("Expected 1.2" in e for e in errors)

    def test_detects_wrong_starting_minor(self, formatter):
        """Test detection of major section not starting at .1."""
        content = """
### 1.1 First
### 2.2 Should start at 2.1
"""
        is_valid, errors = formatter.validate_attribute_numbering(content)

        assert not is_valid
        assert any("should be .1" in e.lower() for e in errors)

    def test_returns_error_when_no_attributes(self, formatter):
        """Test error when no attributes found."""
        content = "# No attributes"
        is_valid, errors = formatter.validate_attribute_numbering(content)

        assert not is_valid
        assert any("No attributes found" in e for e in errors)

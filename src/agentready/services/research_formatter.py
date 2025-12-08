"""Research report formatting and manipulation utilities."""

import re
from datetime import date
from typing import Tuple


class ResearchFormatter:
    """Utilities for formatting and manipulating research reports."""

    def generate_template(self) -> str:
        """Generate a new research report template.

        Returns:
            Markdown template with proper structure
        """
        today = date.today().isoformat()

        template = f"""---
version: 1.0.0
date: {today}
---

# Agent-Ready Codebase Attributes: Comprehensive Research
*Optimizing Codebases for Claude Code and AI-Assisted Development*

**Version:** 1.0.0
**Date:** {today}
**Focus:** Claude Code/Claude-specific optimization
**Sources:** TBD

---

## Executive Summary

This document catalogs 25 high-impact attributes that make codebases optimal for AI-assisted development, specifically Claude Code. Each attribute includes:
- Definition and importance for AI agents
- Impact on agent behavior (context window, comprehension, task success)
- Measurable criteria and tooling
- Authoritative citations
- Good vs. bad examples

---

## 1. CONTEXT WINDOW OPTIMIZATION

### 1.1 Attribute Template

**Definition:** [Clear, concise definition of the attribute]

**Why It Matters:** [Explanation of importance for AI-assisted development]

**Impact on Agent Behavior:**
- [Impact point 1]
- [Impact point 2]
- [Impact point 3]

**Measurable Criteria:**
- [Criterion 1 with specific thresholds]
- [Criterion 2 with tooling recommendations]
- [Criterion 3 with success metrics]

**Citations:**
- [Source 1: Title and URL]
- [Source 2: Title and URL]

**Example:**
```
[Code example showing good vs bad implementation]
```

---

## IMPLEMENTATION PRIORITIES

### Tier 1: Essential (Must-Have)
- 1.1 [Attribute name]

### Tier 2: Critical (Should-Have)
- 2.1 [Attribute name]

### Tier 3: Important (Nice-to-Have)
- 3.1 [Attribute name]

### Tier 4: Advanced (Optimization)
- 4.1 [Attribute name]

---

## REFERENCES & CITATIONS

1. [Citation 1]
2. [Citation 2]

---

**Last Updated:** {today}
**Contributors:** [Your name]
"""
        return template

    def add_attribute(
        self, content: str, attribute_id: str, name: str, tier: int, category: str
    ) -> str:
        """Add a new attribute to the research report.

        Args:
            content: Current research report content
            attribute_id: Attribute ID (e.g., "1.3")
            name: Attribute name
            tier: Tier assignment (1-4)
            category: Category name

        Returns:
            Updated research report content
        """
        # Create attribute section
        attribute_section = f"""
### {attribute_id} {name}

**Definition:** [TODO: Add clear definition]

**Why It Matters:** [TODO: Explain importance]

**Impact on Agent Behavior:**
- [TODO: Impact point 1]
- [TODO: Impact point 2]

**Measurable Criteria:**
- [TODO: Add measurable criterion 1]
- [TODO: Add measurable criterion 2]

**Citations:**
- [TODO: Add citation]

---
"""

        # Find the appropriate category section to insert the attribute
        category_pattern = rf"##\s+{re.escape(category)}"
        match = re.search(category_pattern, content, re.IGNORECASE)

        if match:
            # Insert after category heading
            insert_pos = content.find("\n", match.end()) + 1
            content = content[:insert_pos] + attribute_section + content[insert_pos:]
        else:
            # Category doesn't exist, add it before IMPLEMENTATION PRIORITIES
            impl_match = re.search(r"##\s+IMPLEMENTATION PRIORITIES", content)
            if impl_match:
                insert_pos = impl_match.start()
                new_category = f"\n## {category}\n{attribute_section}\n"
                content = content[:insert_pos] + new_category + content[insert_pos:]
            else:
                # Just append to end
                content += f"\n## {category}\n{attribute_section}"

        # Add to tier section
        tier_pattern = rf"###\s+Tier\s+{tier}:"
        tier_match = re.search(tier_pattern, content)

        if tier_match:
            # Find the end of the tier's bullet list
            tier_start = tier_match.end()
            # Find next tier or section
            next_section = re.search(r"\n###|\n##", content[tier_start:])
            if next_section:
                insert_pos = tier_start + next_section.start()
            else:
                insert_pos = len(content)

            tier_item = f"- {attribute_id} {name}\n"
            content = content[:insert_pos] + tier_item + content[insert_pos:]

        return content

    def bump_version(self, content: str, bump_type: str = "patch") -> str:
        """Bump version in research report.

        Args:
            content: Research report content
            bump_type: Type of version bump (major, minor, patch)

        Returns:
            Updated content with bumped version
        """
        # Extract current version
        version_match = re.search(
            r"^version:\s*(\d+)\.(\d+)\.(\d+)", content, re.MULTILINE
        )

        if not version_match:
            raise ValueError("Could not find version in research report")

        major, minor, patch = map(int, version_match.groups())

        # Bump version
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        new_version = f"{major}.{minor}.{patch}"

        return self.set_version(content, new_version)

    def set_version(self, content: str, version: str) -> str:
        """Set explicit version in research report.

        Args:
            content: Research report content
            version: New version string (e.g., "2.0.0")

        Returns:
            Updated content with new version and current date
        """
        today = date.today().isoformat()

        # Update version in YAML frontmatter
        content = re.sub(
            r"^version:\s*[^\n]+", f"version: {version}", content, flags=re.MULTILINE
        )

        # Update date in YAML frontmatter
        content = re.sub(
            r"^date:\s*[^\n]+", f"date: {today}", content, flags=re.MULTILINE
        )

        # Update version in body (if present)
        content = re.sub(
            r"\*\*Version:\*\*\s+[^\n]+",
            f"**Version:** {version}",
            content,
            flags=re.MULTILINE,
        )

        # Update date in body (if present)
        content = re.sub(
            r"\*\*Date:\*\*\s+[^\n]+", f"**Date:** {today}", content, flags=re.MULTILINE
        )

        return content

    def format_report(self, content: str) -> str:
        """Format research report for consistency.

        Applies:
        - Consistent spacing between sections
        - Proper heading hierarchy
        - Citation formatting
        - Trailing whitespace cleanup

        Args:
            content: Research report content

        Returns:
            Formatted content
        """
        # Ensure consistent spacing after headings
        content = re.sub(
            r"(^#+\s+.+)(\n)([^\n])", r"\1\n\n\3", content, flags=re.MULTILINE
        )

        # Ensure consistent spacing between sections (3 dashes become separator)
        content = re.sub(r"\n---\n", "\n\n---\n\n", content)

        # Remove trailing whitespace
        lines = content.splitlines()
        lines = [line.rstrip() for line in lines]
        content = "\n".join(lines)

        # Ensure file ends with single newline
        content = content.rstrip("\n") + "\n"

        # Remove multiple blank lines (max 2 consecutive blank lines)
        content = re.sub(r"\n{4,}", "\n\n\n", content)

        return content

    def extract_attribute_ids(self, content: str) -> list[str]:
        """Extract all attribute IDs from research report.

        Args:
            content: Research report content

        Returns:
            List of attribute IDs (e.g., ["1.1", "1.2", "2.1", ...])
            Note: Returns all potential attribute IDs including invalid ones
        """
        # Match anything that looks like an attribute ID (must contain a dot)
        # This allows validation to catch and report invalid formats like "1.a"
        # while excluding non-attribute headers like "### Tier 1"
        pattern = r"^###\s+([^\s]+\.[^\s]+)"
        matches = re.findall(pattern, content, re.MULTILINE)
        return matches

    def validate_attribute_numbering(self, content: str) -> Tuple[bool, list[str]]:
        """Validate that attribute numbering is consistent and sequential.

        Args:
            content: Research report content

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        attribute_ids = self.extract_attribute_ids(content)

        if not attribute_ids:
            errors.append("No attributes found in research report")
            return False, errors

        # Check for duplicates
        seen = set()
        for attr_id in attribute_ids:
            if attr_id in seen:
                errors.append(f"Duplicate attribute ID: {attr_id}")
            seen.add(attr_id)

        # Parse and sort
        parsed = []
        for attr_id in attribute_ids:
            # Validate format first (must be exactly "N.M" where N and M are integers)
            if not re.match(r"^\d+\.\d+$", attr_id):
                errors.append(f"Invalid attribute ID format: {attr_id}")
                continue

            try:
                major, minor = map(int, attr_id.split("."))
                parsed.append((major, minor, attr_id))
            except ValueError:
                errors.append(f"Invalid attribute ID format: {attr_id}")

        if errors:
            return False, errors

        parsed.sort()

        # Check sequential ordering within each major section
        last_major = 0
        last_minor = 0

        for major, minor, attr_id in parsed:
            if major != last_major:
                # New major section, reset minor
                if minor != 1:
                    errors.append(
                        f"Attribute {attr_id}: First attribute in section should be .1"
                    )
                last_major = major
                last_minor = 1
            else:
                # Same major section, check minor is sequential
                if minor != last_minor + 1:
                    errors.append(
                        f"Attribute {attr_id}: Expected {last_major}.{last_minor + 1}"
                    )
                last_minor = minor

        is_valid = len(errors) == 0
        return is_valid, errors

"""Integration tests for research CLI commands."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from agentready.cli.research import research


@pytest.fixture
def cli_runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_report():
    """Create a temporary sample research report."""
    content = """---
version: 1.0.0
date: 2025-11-20
---

# Agent-Ready Codebase Attributes

**Version:** 1.0.0
**Date:** 2025-11-20

## 1. CONTEXT WINDOW OPTIMIZATION

### 1.1 Test Attribute

**Definition:** Test definition

**Why It Matters:** Test rationale

**Impact on Agent Behavior:**
- Impact 1

**Measurable Criteria:**
- Criterion 1

**Citations:**
- Source 1

---

## IMPLEMENTATION PRIORITIES

### Tier 1: Essential (Must-Have)
- 1.1 Test Attribute

### Tier 2: Critical (Should-Have)

### Tier 3: Important (Nice-to-Have)

### Tier 4: Advanced (Optimization)

---

## REFERENCES & CITATIONS

1. Source 1
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestValidateCommand:
    """Tests for 'research validate' command."""

    def test_validate_valid_report(self, cli_runner, sample_report):
        """Test validating a valid research report."""
        result = cli_runner.invoke(research, ["validate", sample_report])

        assert result.exit_code == 0
        assert "Version: 1.0.0" in result.output
        assert "Date: 2025-11-20" in result.output
        assert "✅ Validation: PASSED" in result.output

    def test_validate_with_verbose(self, cli_runner, sample_report):
        """Test validate with verbose flag."""
        result = cli_runner.invoke(research, ["validate", sample_report, "--verbose"])

        assert result.exit_code == 0
        assert "Validating research report" in result.output

    def test_validate_nonexistent_file(self, cli_runner):
        """Test validating non-existent file."""
        result = cli_runner.invoke(research, ["validate", "nonexistent.md"])

        assert result.exit_code != 0

    def test_validate_shows_warnings(self, cli_runner):
        """Test that warnings are displayed."""
        # Create report with only 1 attribute (triggers warning)
        content = """---
version: 1.0.0
date: 2025-11-20
---

### 1.1 Only One Attribute

**Measurable Criteria:**
- Test

## IMPLEMENTATION PRIORITIES

### Tier 1: Essential (Must-Have)
### Tier 2: Critical (Should-Have)
### Tier 3: Important (Nice-to-Have)
### Tier 4: Advanced (Optimization)
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = cli_runner.invoke(research, ["validate", temp_path])

            # Should show errors about incorrect attribute count
            assert "❌ ERRORS" in result.output or "Expected 25 attributes" in result.output
            assert result.exit_code == 1  # Should fail validation
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestInitCommand:
    """Tests for 'research init' command."""

    def test_init_creates_report(self, cli_runner):
        """Test creating new research report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "new-research.md"

            result = cli_runner.invoke(
                research, ["init", "--output", str(output_path)]
            )

            assert result.exit_code == 0
            assert "✅ Created" in result.output
            assert output_path.exists()

            # Verify content has required sections
            content = output_path.read_text()
            assert "version: 1.0.0" in content
            assert "## Executive Summary" in content
            assert "## IMPLEMENTATION PRIORITIES" in content

    def test_init_prompts_on_overwrite(self, cli_runner):
        """Test init prompts when file exists."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("existing content")
            temp_path = f.name

        try:
            # Simulate 'no' to overwrite prompt
            result = cli_runner.invoke(
                research, ["init", "--output", temp_path], input="n\n"
            )

            # Should abort without overwriting
            assert "Overwrite?" in result.output or result.exit_code == 0
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestAddAttributeCommand:
    """Tests for 'research add-attribute' command."""

    def test_add_attribute_success(self, cli_runner, sample_report):
        """Test adding a new attribute."""
        result = cli_runner.invoke(
            research,
            [
                "add-attribute",
                sample_report,
                "--attribute-id",
                "1.2",
                "--name",
                "New Attribute",
                "--tier",
                "1",
                "--category",
                "1. CONTEXT WINDOW OPTIMIZATION",
            ],
        )

        assert result.exit_code == 0
        assert "✅ Added attribute 1.2" in result.output

        # Verify attribute was actually added
        content = Path(sample_report).read_text()
        assert "### 1.2 New Attribute" in content

    def test_add_attribute_missing_required_args(self, cli_runner, sample_report):
        """Test error when required arguments are missing."""
        result = cli_runner.invoke(
            research, ["add-attribute", sample_report, "--attribute-id", "1.2"]
        )

        assert result.exit_code != 0


class TestBumpVersionCommand:
    """Tests for 'research bump-version' command."""

    def test_bump_patch_version(self, cli_runner, sample_report):
        """Test bumping patch version."""
        result = cli_runner.invoke(
            research, ["bump-version", sample_report, "--type", "patch"]
        )

        assert result.exit_code == 0
        assert "✅ Bumped version" in result.output
        assert "1.0.1" in result.output

        # Verify version was updated
        content = Path(sample_report).read_text()
        assert "version: 1.0.1" in content

    def test_bump_minor_version(self, cli_runner, sample_report):
        """Test bumping minor version."""
        result = cli_runner.invoke(
            research, ["bump-version", sample_report, "--type", "minor"]
        )

        assert result.exit_code == 0
        assert "1.1.0" in result.output

    def test_bump_major_version(self, cli_runner, sample_report):
        """Test bumping major version."""
        result = cli_runner.invoke(
            research, ["bump-version", sample_report, "--type", "major"]
        )

        assert result.exit_code == 0
        assert "2.0.0" in result.output

    def test_set_explicit_version(self, cli_runner, sample_report):
        """Test setting explicit version."""
        result = cli_runner.invoke(
            research, ["bump-version", sample_report, "--version", "3.5.2"]
        )

        assert result.exit_code == 0
        assert "✅ Set version to: 3.5.2" in result.output

        # Verify version was set
        content = Path(sample_report).read_text()
        assert "version: 3.5.2" in content


class TestFormatCommand:
    """Tests for 'research format' command."""

    def test_format_report(self, cli_runner):
        """Test formatting a research report."""
        # Create report with formatting issues
        content = "# Title   \n\n\n\nContent   \n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = cli_runner.invoke(research, ["format", temp_path])

            assert result.exit_code == 0
            assert "✅ Formatted" in result.output

            # Verify formatting was applied
            formatted = Path(temp_path).read_text()
            assert not formatted.endswith("   \n")  # Trailing whitespace removed
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_format_check_mode(self, cli_runner):
        """Test format check mode."""
        # Create properly formatted report
        content = "# Title\n\nContent\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = cli_runner.invoke(research, ["format", temp_path, "--check"])

            assert result.exit_code == 0
            assert "✅ Research report is properly formatted" in result.output
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_format_check_detects_issues(self, cli_runner):
        """Test format check detects formatting issues."""
        # Create report with formatting issues
        content = "# Title   \n\n\n\n\nToo many blank lines"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = cli_runner.invoke(research, ["format", temp_path, "--check"])

            assert result.exit_code == 1
            assert "❌ Research report needs formatting" in result.output
        finally:
            Path(temp_path).unlink(missing_ok=True)

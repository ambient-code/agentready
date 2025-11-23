"""Unit tests for skill generation."""

import json
from pathlib import Path

import pytest

from agentready.learners.skill_generator import SkillGenerator
from agentready.models import Citation, DiscoveredSkill


@pytest.fixture
def sample_skill():
    """Create sample discovered skill."""
    return DiscoveredSkill(
        skill_id="test-skill",
        name="Test Skill",
        description="Test description for a skill",
        confidence=90.0,
        source_attribute_id="test_attr",
        reusability_score=85.0,
        impact_score=50.0,
        pattern_summary="This is a test pattern summary explaining the skill.",
        code_examples=["example1", "example2"],
        citations=[],
    )


@pytest.fixture
def sample_skill_with_citations():
    """Create sample skill with citations."""
    return DiscoveredSkill(
        skill_id="test-skill-citations",
        name="Test Skill with Citations",
        description="Test description",
        confidence=95.0,
        source_attribute_id="test_attr",
        reusability_score=90.0,
        impact_score=50.0,
        pattern_summary="Pattern with research backing.",
        code_examples=["example1"],
        citations=[
            Citation(
                source="Research Paper",
                title="Best Practices for Code",
                url="https://example.com/paper",
                relevance="High",
            )
        ],
    )


class TestSkillGenerator:
    """Test SkillGenerator class."""

    def test_init_default_output_dir(self):
        """Test initialization with default output directory."""
        generator = SkillGenerator()
        assert generator.output_dir == Path(".skills-proposals")

    def test_init_custom_output_dir(self, tmp_path):
        """Test initialization with custom output directory."""
        custom_dir = tmp_path / "custom-skills"
        generator = SkillGenerator(output_dir=custom_dir)
        assert generator.output_dir == custom_dir

    def test_generate_skill_file(self, sample_skill, tmp_path):
        """Test SKILL.md file generation."""
        generator = SkillGenerator(output_dir=tmp_path)
        output_file = generator.generate_skill_file(sample_skill)

        assert output_file.exists()
        assert output_file.parent.name == "test-skill"
        assert output_file.name == "SKILL.md"

        content = output_file.read_text()
        assert "Test Skill" in content
        assert "test-skill" in content
        assert "Test description" in content

    def test_generate_skill_file_creates_directory(self, sample_skill, tmp_path):
        """Test that skill file generation creates necessary directories."""
        generator = SkillGenerator(output_dir=tmp_path)
        skill_dir = tmp_path / sample_skill.skill_id

        # Directory shouldn't exist yet
        assert not skill_dir.exists()

        output_file = generator.generate_skill_file(sample_skill)

        # Directory should now exist
        assert skill_dir.exists()
        assert output_file.exists()

    def test_generate_github_issue(self, sample_skill, tmp_path):
        """Test GitHub issue template generation."""
        generator = SkillGenerator(output_dir=tmp_path)
        output_file = generator.generate_github_issue(sample_skill)

        assert output_file.exists()
        assert output_file.name == "skill-test-skill.md"

        content = output_file.read_text()
        assert "Test Skill" in content
        assert "test-skill" in content

    def test_generate_github_issue_creates_output_dir(self, sample_skill, tmp_path):
        """Test that GitHub issue generation creates output directory."""
        output_dir = tmp_path / "issues"
        generator = SkillGenerator(output_dir=output_dir)

        # Directory shouldn't exist yet
        assert not output_dir.exists()

        output_file = generator.generate_github_issue(sample_skill)

        # Directory should now exist
        assert output_dir.exists()
        assert output_file.exists()

    def test_generate_markdown_report(self, sample_skill, tmp_path):
        """Test markdown report generation."""
        generator = SkillGenerator(output_dir=tmp_path)
        output_file = generator.generate_markdown_report(sample_skill)

        assert output_file.exists()
        assert output_file.name == "test-skill-report.md"

        content = output_file.read_text()
        assert "Test Skill" in content
        assert "test-skill" in content
        assert "90%" in content  # Confidence
        assert "+50.0 pts" in content  # Impact
        assert "85.0%" in content  # Reusability

    def test_generate_markdown_report_with_code_examples(self, sample_skill, tmp_path):
        """Test markdown report includes code examples."""
        generator = SkillGenerator(output_dir=tmp_path)
        output_file = generator.generate_markdown_report(sample_skill)

        content = output_file.read_text()
        assert "example1" in content
        assert "example2" in content
        assert "Example 1" in content or "```" in content

    def test_generate_markdown_report_without_code_examples(self, tmp_path):
        """Test markdown report handles missing code examples."""
        skill_no_examples = DiscoveredSkill(
            skill_id="no-examples",
            name="No Examples Skill",
            description="Test",
            confidence=80.0,
            source_attribute_id="test",
            reusability_score=80.0,
            impact_score=30.0,
            pattern_summary="Test pattern",
            code_examples=[],
            citations=[],
        )

        generator = SkillGenerator(output_dir=tmp_path)
        output_file = generator.generate_markdown_report(skill_no_examples)

        content = output_file.read_text()
        assert "No code examples available" in content

    def test_generate_markdown_report_with_citations(
        self, sample_skill_with_citations, tmp_path
    ):
        """Test markdown report includes citations."""
        generator = SkillGenerator(output_dir=tmp_path)
        output_file = generator.generate_markdown_report(sample_skill_with_citations)

        content = output_file.read_text()
        assert "Research Paper" in content
        assert "Best Practices for Code" in content
        assert "https://example.com/paper" in content

    def test_generate_markdown_report_without_citations(self, sample_skill, tmp_path):
        """Test markdown report handles missing citations."""
        generator = SkillGenerator(output_dir=tmp_path)
        output_file = generator.generate_markdown_report(sample_skill)

        content = output_file.read_text()
        assert "No citations available" in content

    def test_generate_all_formats(self, sample_skill, tmp_path):
        """Test generating all output formats."""
        generator = SkillGenerator(output_dir=tmp_path)
        results = generator.generate_all_formats(sample_skill)

        assert "skill_md" in results
        assert "github_issue" in results
        assert "markdown_report" in results

        assert results["skill_md"].exists()
        assert results["github_issue"].exists()
        assert results["markdown_report"].exists()

    def test_generate_batch_skill_md(self, tmp_path):
        """Test batch generation of SKILL.md files."""
        skills = [
            DiscoveredSkill(
                skill_id=f"skill-{i}",
                name=f"Skill {i}",
                description=f"Description {i}",
                confidence=80.0 + i,
                source_attribute_id=f"attr_{i}",
                reusability_score=80.0,
                impact_score=30.0,
                pattern_summary=f"Pattern {i}",
                code_examples=[],
                citations=[],
            )
            for i in range(3)
        ]

        generator = SkillGenerator(output_dir=tmp_path)
        generated_files = generator.generate_batch(skills, output_format="skill_md")

        assert len(generated_files) == 3
        for file_path in generated_files:
            assert file_path.exists()
            assert file_path.name == "SKILL.md"

    def test_generate_batch_github_issues(self, tmp_path):
        """Test batch generation of GitHub issues."""
        skills = [
            DiscoveredSkill(
                skill_id=f"skill-{i}",
                name=f"Skill {i}",
                description=f"Description {i}",
                confidence=80.0,
                source_attribute_id=f"attr_{i}",
                reusability_score=80.0,
                impact_score=30.0,
                pattern_summary=f"Pattern {i}",
                code_examples=[],
                citations=[],
            )
            for i in range(3)
        ]

        generator = SkillGenerator(output_dir=tmp_path)
        generated_files = generator.generate_batch(skills, output_format="github_issue")

        assert len(generated_files) == 3
        for file_path in generated_files:
            assert file_path.exists()
            assert file_path.name.startswith("skill-")
            assert file_path.name.endswith(".md")

    def test_generate_batch_markdown_reports(self, tmp_path):
        """Test batch generation of markdown reports."""
        skills = [
            DiscoveredSkill(
                skill_id=f"skill-{i}",
                name=f"Skill {i}",
                description=f"Description {i}",
                confidence=80.0,
                source_attribute_id=f"attr_{i}",
                reusability_score=80.0,
                impact_score=30.0,
                pattern_summary=f"Pattern {i}",
                code_examples=[],
                citations=[],
            )
            for i in range(3)
        ]

        generator = SkillGenerator(output_dir=tmp_path)
        generated_files = generator.generate_batch(
            skills, output_format="markdown_report"
        )

        assert len(generated_files) == 3
        for file_path in generated_files:
            assert file_path.exists()
            assert file_path.name.endswith("-report.md")

    def test_generate_batch_all_formats(self, tmp_path):
        """Test batch generation of all formats."""
        skills = [
            DiscoveredSkill(
                skill_id=f"skill-{i}",
                name=f"Skill {i}",
                description=f"Description {i}",
                confidence=80.0,
                source_attribute_id=f"attr_{i}",
                reusability_score=80.0,
                impact_score=30.0,
                pattern_summary=f"Pattern {i}",
                code_examples=[],
                citations=[],
            )
            for i in range(2)
        ]

        generator = SkillGenerator(output_dir=tmp_path)
        generated_files = generator.generate_batch(skills, output_format="all")

        # Each skill generates 3 files (skill_md, github_issue, markdown_report)
        assert len(generated_files) == 6

    def test_generate_batch_empty_list(self, tmp_path):
        """Test batch generation with empty skill list."""
        generator = SkillGenerator(output_dir=tmp_path)
        generated_files = generator.generate_batch([], output_format="skill_md")

        assert len(generated_files) == 0

    def test_create_markdown_report_structure(self, sample_skill, tmp_path):
        """Test markdown report has expected structure."""
        generator = SkillGenerator(output_dir=tmp_path)
        report_content = generator._create_markdown_report(sample_skill)

        # Check for expected sections
        assert "# Skill Report:" in report_content
        assert "## Overview" in report_content
        assert "## Description" in report_content
        assert "## Pattern Summary" in report_content
        assert "## Implementation Guidance" in report_content
        assert "## Metrics" in report_content

    def test_create_markdown_report_includes_metrics(self, sample_skill, tmp_path):
        """Test markdown report includes all metrics."""
        generator = SkillGenerator(output_dir=tmp_path)
        report_content = generator._create_markdown_report(sample_skill)

        # Check for metric values
        assert "**Confidence**: 90.0%" in report_content
        assert "**Impact**: +50.0 pts" in report_content
        assert "**Reusability**: 85.0%" in report_content
        assert "**Confidence Score**: 90.0%" in report_content
        assert "**Impact Score**: 50.0 pts" in report_content
        assert "**Reusability Score**: 85.0%" in report_content

    def test_file_naming_conventions(self, sample_skill, tmp_path):
        """Test that generated files follow naming conventions."""
        generator = SkillGenerator(output_dir=tmp_path)

        # Generate all formats
        skill_md = generator.generate_skill_file(sample_skill)
        github_issue = generator.generate_github_issue(sample_skill)
        markdown_report = generator.generate_markdown_report(sample_skill)

        # Check naming
        assert skill_md.name == "SKILL.md"
        assert github_issue.name == f"skill-{sample_skill.skill_id}.md"
        assert markdown_report.name == f"{sample_skill.skill_id}-report.md"

    def test_output_directory_as_string(self, tmp_path):
        """Test that output directory works as string path."""
        generator = SkillGenerator(output_dir=str(tmp_path))
        assert isinstance(generator.output_dir, Path)
        assert generator.output_dir == tmp_path

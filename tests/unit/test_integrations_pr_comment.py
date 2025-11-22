"""Tests for PR comment generation functionality."""

import pytest

from agentready.integrations.pr_comment import PRCommentGenerator
from agentready.models.assessment import Assessment
from agentready.models.attribute import Attribute
from agentready.models.finding import Finding, Remediation


@pytest.fixture
def sample_attribute():
    """Create a sample attribute for testing."""
    return Attribute(
        id="test_attr",
        name="Test Attribute",
        description="A test attribute",
        tier=1,
        weight=0.05,
    )


@pytest.fixture
def sample_assessment(sample_attribute):
    """Create a sample assessment for testing."""
    findings = [
        Finding(
            attribute=sample_attribute,
            status="pass",
            score=100.0,
            explanation="Test passed",
            evidence=[],
            remediation=None,
        ),
        Finding(
            attribute=Attribute(
                id="test_attr_2",
                name="Failed Attribute",
                description="A failing test",
                tier=2,
                weight=0.03,
            ),
            status="fail",
            score=0.0,
            explanation="Test failed",
            evidence=[],
            remediation=Remediation(
                summary="Fix the failing test",
                steps=["Fix step 1", "Fix step 2"],
                tools=[],
                commands=[],
                examples=[],
                citations=[],
            ),
        ),
    ]

    return Assessment(
        repository_path="/test/repo",
        score=85.0,
        certification_level="gold",
        findings=findings,
        metadata={},
    )


class TestPRCommentGenerator:
    """Tests for PRCommentGenerator class."""

    def test_generate_summary_comment_basic(self, sample_assessment):
        """Test basic summary comment generation."""
        comment = PRCommentGenerator.generate_summary_comment(sample_assessment)

        assert "## AgentReady Assessment Results" in comment
        assert "85.0/100 (Gold)" in comment
        assert "✅ **Passed**: 1 attributes" in comment
        assert "❌ **Failed**: 1 attributes" in comment

    def test_generate_summary_comment_with_delta(self, sample_assessment):
        """Test summary comment with score delta."""
        comment = PRCommentGenerator.generate_summary_comment(
            sample_assessment, previous_score=80.0
        )

        assert "+5.0" in comment
        assert "📈" in comment  # Improvement emoji
        assert "_Previous: 80.0/100_" in comment

    def test_generate_summary_comment_with_negative_delta(self, sample_assessment):
        """Test summary comment with negative score delta."""
        comment = PRCommentGenerator.generate_summary_comment(
            sample_assessment, previous_score=90.0
        )

        assert "-5.0" in comment
        assert "📉" in comment  # Decline emoji

    def test_generate_summary_comment_with_report_url(self, sample_assessment):
        """Test summary comment with report URL."""
        comment = PRCommentGenerator.generate_summary_comment(
            sample_assessment, report_url="https://example.com/report.html"
        )

        assert "[📊 View Full Report](https://example.com/report.html)" in comment

    def test_generate_summary_comment_with_details(self, sample_assessment):
        """Test summary comment with detailed findings."""
        comment = PRCommentGenerator.generate_summary_comment(
            sample_assessment, show_details=True
        )

        assert "<details>" in comment
        assert "📋 Detailed Findings" in comment
        assert "### ❌ Failed Attributes" in comment
        assert "**Failed Attribute**" in comment
        assert "Fix step 1" in comment

    def test_generate_summary_comment_without_details(self, sample_assessment):
        """Test summary comment without detailed findings."""
        comment = PRCommentGenerator.generate_summary_comment(
            sample_assessment, show_details=False
        )

        assert "<details>" not in comment
        assert "Failed Attribute" not in comment

    def test_generate_compact_comment(self, sample_assessment):
        """Test compact comment generation."""
        comment = PRCommentGenerator.generate_compact_comment(sample_assessment)

        assert "**AgentReady**: 85.0/100 (Gold)" in comment
        assert "✅ 1 passed" in comment
        assert "❌ 1 failed" in comment

    def test_generate_compact_comment_with_url(self, sample_assessment):
        """Test compact comment with report URL."""
        comment = PRCommentGenerator.generate_compact_comment(
            sample_assessment, report_url="https://example.com/report.html"
        )

        assert "[📊 Full Report](https://example.com/report.html)" in comment

    def test_generate_status_description(self, sample_assessment):
        """Test status description generation."""
        description = PRCommentGenerator.generate_status_description(sample_assessment)

        assert "AgentReady: 85.0/100 (Gold)" in description
        assert "1/2 passed" in description

    def test_generate_check_output(self, sample_assessment):
        """Test check output generation."""
        title, summary, text = PRCommentGenerator.generate_check_output(
            sample_assessment
        )

        # Title
        assert "85.0/100 (Gold)" in title

        # Summary
        assert "Passed 1 attributes" in summary
        assert "failed 1 attributes" in summary

        # Text
        assert "## Assessment Results" in text
        assert "### Failed Attributes" in text
        assert "**Failed Attribute**" in text

    def test_generate_check_output_with_remediation(self, sample_assessment):
        """Test check output with remediation steps."""
        title, summary, text = PRCommentGenerator.generate_check_output(
            sample_assessment, include_remediation=True
        )

        assert "**Remediation:**" in text
        assert "Fix step 1" in text
        assert "Fix step 2" in text

    def test_generate_check_output_without_remediation(self, sample_assessment):
        """Test check output without remediation steps."""
        title, summary, text = PRCommentGenerator.generate_check_output(
            sample_assessment, include_remediation=False
        )

        assert "**Remediation:**" not in text

    def test_format_trend_ascii_no_data(self):
        """Test trend formatting with no data."""
        trend = PRCommentGenerator.format_trend_ascii([])

        assert "_No trend data available_" in trend

    def test_format_trend_ascii_single_score(self):
        """Test trend formatting with single score."""
        trend = PRCommentGenerator.format_trend_ascii([85.0])

        assert "_No trend data available_" in trend

    def test_format_trend_ascii_with_scores(self):
        """Test trend formatting with multiple scores."""
        scores = [70.0, 75.0, 80.0, 85.0, 90.0]
        trend = PRCommentGenerator.format_trend_ascii(scores)

        assert "Trend (last 5 assessments):" in trend
        assert "_Range:" in trend
        # Should contain chart characters
        assert any(char in trend for char in ["█", "▆", "▄", "▂", "_"])

    def test_format_trend_ascii_unchanged(self):
        """Test trend formatting with unchanged scores."""
        scores = [85.0, 85.0, 85.0]
        trend = PRCommentGenerator.format_trend_ascii(scores)

        assert "_Scores unchanged_" in trend

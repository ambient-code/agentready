"""Tests for badge generation functionality."""

import pytest

from agentready.integrations.badge import BadgeGenerator


class TestBadgeGenerator:
    """Tests for BadgeGenerator class."""

    def test_get_certification_level_platinum(self):
        """Test platinum level detection (90-100)."""
        assert BadgeGenerator.get_certification_level(100.0) == "platinum"
        assert BadgeGenerator.get_certification_level(95.0) == "platinum"
        assert BadgeGenerator.get_certification_level(90.0) == "platinum"

    def test_get_certification_level_gold(self):
        """Test gold level detection (75-89)."""
        assert BadgeGenerator.get_certification_level(89.9) == "gold"
        assert BadgeGenerator.get_certification_level(80.0) == "gold"
        assert BadgeGenerator.get_certification_level(75.0) == "gold"

    def test_get_certification_level_silver(self):
        """Test silver level detection (60-74)."""
        assert BadgeGenerator.get_certification_level(74.9) == "silver"
        assert BadgeGenerator.get_certification_level(65.0) == "silver"
        assert BadgeGenerator.get_certification_level(60.0) == "silver"

    def test_get_certification_level_bronze(self):
        """Test bronze level detection (40-59)."""
        assert BadgeGenerator.get_certification_level(59.9) == "bronze"
        assert BadgeGenerator.get_certification_level(50.0) == "bronze"
        assert BadgeGenerator.get_certification_level(40.0) == "bronze"

    def test_get_certification_level_needs_improvement(self):
        """Test needs improvement level detection (0-39)."""
        assert BadgeGenerator.get_certification_level(39.9) == "needs_improvement"
        assert BadgeGenerator.get_certification_level(20.0) == "needs_improvement"
        assert BadgeGenerator.get_certification_level(0.0) == "needs_improvement"

    def test_generate_shields_url_basic(self):
        """Test basic Shields.io URL generation."""
        url = BadgeGenerator.generate_shields_url(85.0)

        assert "img.shields.io/badge" in url
        assert "AgentReady" in url
        assert "85.0" in url
        assert "Gold" in url
        assert "eab308" in url  # Gold color without #
        assert "style=flat-square" in url

    def test_generate_shields_url_custom_style(self):
        """Test Shields.io URL with custom style."""
        url = BadgeGenerator.generate_shields_url(85.0, style="for-the-badge")

        assert "style=for-the-badge" in url

    def test_generate_shields_url_custom_label(self):
        """Test Shields.io URL with custom label."""
        url = BadgeGenerator.generate_shields_url(85.0, label="Quality")

        assert "Quality" in url

    def test_generate_shields_url_explicit_level(self):
        """Test Shields.io URL with explicit certification level."""
        url = BadgeGenerator.generate_shields_url(85.0, level="platinum")

        assert "Platinum" in url
        assert "9333ea" in url  # Platinum color

    def test_generate_svg_basic(self):
        """Test SVG generation."""
        svg = BadgeGenerator.generate_svg(85.0)

        assert '<svg xmlns="http://www.w3.org/2000/svg"' in svg
        assert "AgentReady: 85.0 (Gold)" in svg
        assert "#eab308" in svg  # Gold color

    def test_generate_svg_custom_width(self):
        """Test SVG with custom width."""
        svg = BadgeGenerator.generate_svg(85.0, width=300)

        assert 'width="300"' in svg

    def test_generate_markdown_badge_no_link(self):
        """Test Markdown badge without link."""
        markdown = BadgeGenerator.generate_markdown_badge(85.0)

        assert markdown.startswith("![AgentReady]")
        assert "img.shields.io" in markdown
        # Should not have link wrapper
        assert not markdown.startswith("[![")

    def test_generate_markdown_badge_with_link(self):
        """Test Markdown badge with link."""
        markdown = BadgeGenerator.generate_markdown_badge(
            85.0, report_url="https://example.com/report"
        )

        assert markdown.startswith("[![AgentReady]")
        assert "](https://example.com/report)" in markdown

    def test_generate_html_badge_no_link(self):
        """Test HTML badge without link."""
        html = BadgeGenerator.generate_html_badge(85.0)

        assert '<img src="https://img.shields.io' in html
        assert 'alt="AgentReady Badge"' in html
        # Should not have anchor tag
        assert "<a href=" not in html

    def test_generate_html_badge_with_link(self):
        """Test HTML badge with link."""
        html = BadgeGenerator.generate_html_badge(
            85.0, report_url="https://example.com/report"
        )

        assert '<a href="https://example.com/report">' in html
        assert '<img src="https://img.shields.io' in html

    def test_color_consistency(self):
        """Test that color values are consistent across levels."""
        for score, expected_level in [
            (95.0, "platinum"),
            (80.0, "gold"),
            (65.0, "silver"),
            (45.0, "bronze"),
            (20.0, "needs_improvement"),
        ]:
            level = BadgeGenerator.get_certification_level(score)
            assert level == expected_level

            # Check color is used correctly
            color = BadgeGenerator.COLORS[level]
            url = BadgeGenerator.generate_shields_url(score)
            assert color.lstrip("#") in url

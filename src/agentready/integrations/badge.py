"""Badge generation for repository certification levels."""

from typing import Literal

CertificationLevel = Literal["platinum", "gold", "silver", "bronze", "needs_improvement"]


class BadgeGenerator:
    """Generates SVG badges showing AgentReady certification levels."""

    # Color schemes for each certification level
    COLORS = {
        "platinum": "#9333ea",  # Purple
        "gold": "#eab308",  # Yellow
        "silver": "#94a3b8",  # Silver
        "bronze": "#92400e",  # Brown
        "needs_improvement": "#dc2626",  # Red
    }

    # Shields.io style names
    SHIELD_STYLES = ["flat", "flat-square", "plastic", "for-the-badge", "social"]

    @staticmethod
    def get_certification_level(score: float) -> CertificationLevel:
        """
        Determine certification level from score.

        Args:
            score: Assessment score (0-100)

        Returns:
            Certification level string
        """
        if score >= 90:
            return "platinum"
        elif score >= 75:
            return "gold"
        elif score >= 60:
            return "silver"
        elif score >= 40:
            return "bronze"
        else:
            return "needs_improvement"

    @classmethod
    def generate_shields_url(
        cls,
        score: float,
        level: CertificationLevel | None = None,
        style: str = "flat-square",
        label: str = "AgentReady",
    ) -> str:
        """
        Generate Shields.io badge URL.

        Args:
            score: Assessment score (0-100)
            level: Certification level (auto-detected if None)
            style: Badge style (flat, flat-square, plastic, for-the-badge, social)
            label: Badge label text

        Returns:
            Shields.io badge URL
        """
        if level is None:
            level = cls.get_certification_level(score)

        color = cls.COLORS[level]
        # Remove # from color for URL
        color = color.lstrip("#")

        # Format: {label}-{score} ({level})-{color}
        message = f"{score:.1f} ({level.replace('_', ' ').title()})"

        # Shields.io static badge format
        # https://img.shields.io/badge/{label}-{message}-{color}?style={style}
        return (
            f"https://img.shields.io/badge/{label}-{message}-{color}?style={style}"
        )

    @classmethod
    def generate_svg(
        cls, score: float, level: CertificationLevel | None = None, width: int = 200
    ) -> str:
        """
        Generate custom SVG badge (alternative to Shields.io).

        Args:
            score: Assessment score (0-100)
            level: Certification level (auto-detected if None)
            width: Badge width in pixels

        Returns:
            SVG markup as string
        """
        if level is None:
            level = cls.get_certification_level(score)

        color = cls.COLORS[level]
        level_text = level.replace("_", " ").title()

        # Simple SVG badge design
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="28">
  <defs>
    <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{color};stop-opacity:0.9" />
    </linearGradient>
  </defs>
  <rect width="{width}" height="28" rx="4" fill="url(#gradient)"/>
  <text x="{width//2}" y="18" font-family="Arial, sans-serif" font-size="12"
        font-weight="bold" fill="white" text-anchor="middle">
    AgentReady: {score:.1f} ({level_text})
  </text>
</svg>'''
        return svg

    @classmethod
    def generate_markdown_badge(
        cls,
        score: float,
        level: CertificationLevel | None = None,
        report_url: str | None = None,
        style: str = "flat-square",
    ) -> str:
        """
        Generate Markdown badge with optional link.

        Args:
            score: Assessment score (0-100)
            level: Certification level (auto-detected if None)
            report_url: URL to link badge to (optional)
            style: Badge style

        Returns:
            Markdown formatted badge
        """
        badge_url = cls.generate_shields_url(score, level, style)

        if report_url:
            return f"[![AgentReady]({badge_url})]({report_url})"
        else:
            return f"![AgentReady]({badge_url})"

    @classmethod
    def generate_html_badge(
        cls,
        score: float,
        level: CertificationLevel | None = None,
        report_url: str | None = None,
        style: str = "flat-square",
    ) -> str:
        """
        Generate HTML badge with optional link.

        Args:
            score: Assessment score (0-100)
            level: Certification level (auto-detected if None)
            report_url: URL to link badge to (optional)
            style: Badge style

        Returns:
            HTML formatted badge
        """
        badge_url = cls.generate_shields_url(score, level, style)

        img_tag = f'<img src="{badge_url}" alt="AgentReady Badge">'

        if report_url:
            return f'<a href="{report_url}">{img_tag}</a>'
        else:
            return img_tag

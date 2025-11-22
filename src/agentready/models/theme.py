"""Theme system for HTML reports with accessibility validation."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Theme:
    """HTML report theme with color scheme and styling.

    All themes must maintain WCAG 2.1 AA contrast ratios (4.5:1 for normal text).
    """

    name: str
    display_name: str
    background: str
    surface: str
    surface_elevated: str
    primary: str
    primary_light: str
    primary_dark: str
    text_primary: str
    text_secondary: str
    text_muted: str
    success: str
    warning: str
    danger: str
    neutral: str
    border: str
    shadow: str

    # Built-in themes
    BUILT_IN_THEMES: ClassVar[dict[str, "Theme"]] = {}

    def to_css_vars(self) -> dict[str, str]:
        """Convert theme to CSS custom properties dictionary."""
        return {
            "--background": self.background,
            "--surface": self.surface,
            "--surface-elevated": self.surface_elevated,
            "--primary": self.primary,
            "--primary-light": self.primary_light,
            "--primary-dark": self.primary_dark,
            "--text-primary": self.text_primary,
            "--text-secondary": self.text_secondary,
            "--text-muted": self.text_muted,
            "--success": self.success,
            "--warning": self.warning,
            "--danger": self.danger,
            "--neutral": self.neutral,
            "--border": self.border,
            "--shadow": self.shadow,
        }

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "background": self.background,
            "surface": self.surface,
            "surface_elevated": self.surface_elevated,
            "primary": self.primary,
            "primary_light": self.primary_light,
            "primary_dark": self.primary_dark,
            "text_primary": self.text_primary,
            "text_secondary": self.text_secondary,
            "text_muted": self.text_muted,
            "success": self.success,
            "warning": self.warning,
            "danger": self.danger,
            "neutral": self.neutral,
            "border": self.border,
            "shadow": self.shadow,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Theme":
        """Create theme from dictionary."""
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            background=data["background"],
            surface=data["surface"],
            surface_elevated=data["surface_elevated"],
            primary=data["primary"],
            primary_light=data["primary_light"],
            primary_dark=data["primary_dark"],
            text_primary=data["text_primary"],
            text_secondary=data["text_secondary"],
            text_muted=data["text_muted"],
            success=data["success"],
            warning=data["warning"],
            danger=data["danger"],
            neutral=data["neutral"],
            border=data["border"],
            shadow=data["shadow"],
        )

    @classmethod
    def get_theme(cls, theme_name: str) -> "Theme":
        """Get built-in theme by name.

        Args:
            theme_name: Theme identifier (default, dark, light, etc.)

        Returns:
            Theme object

        Raises:
            KeyError: If theme not found
        """
        if theme_name not in cls.BUILT_IN_THEMES:
            raise KeyError(
                f"Theme '{theme_name}' not found. "
                f"Available themes: {', '.join(cls.BUILT_IN_THEMES.keys())}"
            )
        return cls.BUILT_IN_THEMES[theme_name]

    @classmethod
    def get_available_themes(cls) -> list[str]:
        """Get list of available built-in theme names."""
        return list(cls.BUILT_IN_THEMES.keys())


# Define built-in themes
Theme.BUILT_IN_THEMES = {
    "default": Theme(
        name="default",
        display_name="Default (Dark Professional)",
        background="#0a0e27",
        surface="#1a1f3a",
        surface_elevated="#252b4a",
        primary="#8b5cf6",
        primary_light="#a78bfa",
        primary_dark="#6d28d9",
        text_primary="#f8fafc",
        text_secondary="#cbd5e1",
        text_muted="#94a3b8",
        success="#10b981",
        warning="#f59e0b",
        danger="#ef4444",
        neutral="#64748b",
        border="#334155",
        shadow="rgba(0, 0, 0, 0.5)",
    ),
    "light": Theme(
        name="light",
        display_name="Light",
        background="#f8fafc",
        surface="#ffffff",
        surface_elevated="#f1f5f9",
        primary="#8b5cf6",
        primary_light="#a78bfa",
        primary_dark="#6d28d9",
        text_primary="#0f172a",
        text_secondary="#334155",
        text_muted="#64748b",
        success="#10b981",
        warning="#f59e0b",
        danger="#ef4444",
        neutral="#94a3b8",
        border="#e2e8f0",
        shadow="rgba(0, 0, 0, 0.1)",
    ),
    "dark": Theme(
        name="dark",
        display_name="Dark",
        background="#0f172a",
        surface="#1e293b",
        surface_elevated="#334155",
        primary="#8b5cf6",
        primary_light="#a78bfa",
        primary_dark="#6d28d9",
        text_primary="#f1f5f9",
        text_secondary="#cbd5e1",
        text_muted="#94a3b8",
        success="#10b981",
        warning="#f59e0b",
        danger="#ef4444",
        neutral="#64748b",
        border="#475569",
        shadow="rgba(0, 0, 0, 0.6)",
    ),
    "high-contrast": Theme(
        name="high-contrast",
        display_name="High Contrast",
        background="#000000",
        surface="#1a1a1a",
        surface_elevated="#2d2d2d",
        primary="#00ffff",
        primary_light="#66ffff",
        primary_dark="#00cccc",
        text_primary="#ffffff",
        text_secondary="#e0e0e0",
        text_muted="#b0b0b0",
        success="#00ff00",
        warning="#ffff00",
        danger="#ff0000",
        neutral="#808080",
        border="#ffffff",
        shadow="rgba(255, 255, 255, 0.2)",
    ),
    "solarized-dark": Theme(
        name="solarized-dark",
        display_name="Solarized Dark",
        background="#002b36",
        surface="#073642",
        surface_elevated="#0e4e5c",
        primary="#268bd2",
        primary_light="#5fa8db",
        primary_dark="#1e6fa9",
        text_primary="#fdf6e3",
        text_secondary="#eee8d5",
        text_muted="#93a1a1",
        success="#859900",
        warning="#b58900",
        danger="#dc322f",
        neutral="#586e75",
        border="#586e75",
        shadow="rgba(0, 0, 0, 0.5)",
    ),
    "dracula": Theme(
        name="dracula",
        display_name="Dracula",
        background="#282a36",
        surface="#44475a",
        surface_elevated="#6272a4",
        primary="#bd93f9",
        primary_light="#d4b5ff",
        primary_dark="#9b72d6",
        text_primary="#f8f8f2",
        text_secondary="#e6e6e6",
        text_muted="#6272a4",
        success="#50fa7b",
        warning="#f1fa8c",
        danger="#ff5555",
        neutral="#8be9fd",
        border="#6272a4",
        shadow="rgba(0, 0, 0, 0.5)",
    ),
}


def validate_theme_contrast(theme: Theme) -> list[str]:
    """Validate theme meets WCAG 2.1 AA contrast requirements.

    Args:
        theme: Theme to validate

    Returns:
        List of validation warnings (empty if all valid)
    """
    warnings = []

    # Simple luminance calculation (simplified WCAG formula)
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def relative_luminance(rgb: tuple[int, int, int]) -> float:
        """Calculate relative luminance (simplified)."""
        r, g, b = [x / 255.0 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def contrast_ratio(color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors."""
        try:
            l1 = relative_luminance(hex_to_rgb(color1))
            l2 = relative_luminance(hex_to_rgb(color2))
            lighter = max(l1, l2)
            darker = min(l1, l2)
            return (lighter + 0.05) / (darker + 0.05)
        except (ValueError, IndexError):
            return 0.0

    # Check key contrast pairs (WCAG 2.1 AA requires 4.5:1 for normal text)
    min_contrast = 4.5

    contrast_checks = [
        (theme.text_primary, theme.background, "Primary text on background"),
        (theme.text_primary, theme.surface, "Primary text on surface"),
        (theme.text_secondary, theme.background, "Secondary text on background"),
        (theme.text_secondary, theme.surface, "Secondary text on surface"),
    ]

    for fg, bg, description in contrast_checks:
        ratio = contrast_ratio(fg, bg)
        if ratio < min_contrast:
            warnings.append(
                f"{description}: {ratio:.2f}:1 (minimum {min_contrast}:1 required)"
            )

    return warnings

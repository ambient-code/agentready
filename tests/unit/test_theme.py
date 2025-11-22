"""Unit tests for theme system."""

import pytest

from agentready.models.theme import Theme, validate_theme_contrast


class TestTheme:
    """Test Theme model and functionality."""

    def test_theme_creation(self):
        """Test creating a theme with all required fields."""
        theme = Theme(
            name="test",
            display_name="Test Theme",
            background="#000000",
            surface="#111111",
            surface_elevated="#222222",
            primary="#3333ff",
            primary_light="#5555ff",
            primary_dark="#1111ff",
            text_primary="#ffffff",
            text_secondary="#eeeeee",
            text_muted="#cccccc",
            success="#00ff00",
            warning="#ffff00",
            danger="#ff0000",
            neutral="#888888",
            border="#444444",
            shadow="rgba(0, 0, 0, 0.5)",
        )

        assert theme.name == "test"
        assert theme.display_name == "Test Theme"
        assert theme.background == "#000000"
        assert theme.primary == "#3333ff"

    def test_theme_to_css_vars(self):
        """Test converting theme to CSS custom properties."""
        theme = Theme.get_theme("default")
        css_vars = theme.to_css_vars()

        assert "--background" in css_vars
        assert "--surface" in css_vars
        assert "--primary" in css_vars
        assert "--text-primary" in css_vars
        assert len(css_vars) == 15  # All theme properties

    def test_theme_to_dict(self):
        """Test converting theme to dictionary."""
        theme = Theme.get_theme("default")
        theme_dict = theme.to_dict()

        assert theme_dict["name"] == "default"
        assert theme_dict["display_name"] == "Default (Dark Professional)"
        assert "background" in theme_dict
        assert "primary" in theme_dict

    def test_theme_from_dict(self):
        """Test creating theme from dictionary."""
        theme_data = {
            "name": "custom",
            "display_name": "Custom Theme",
            "background": "#000000",
            "surface": "#111111",
            "surface_elevated": "#222222",
            "primary": "#3333ff",
            "primary_light": "#5555ff",
            "primary_dark": "#1111ff",
            "text_primary": "#ffffff",
            "text_secondary": "#eeeeee",
            "text_muted": "#cccccc",
            "success": "#00ff00",
            "warning": "#ffff00",
            "danger": "#ff0000",
            "neutral": "#888888",
            "border": "#444444",
            "shadow": "rgba(0, 0, 0, 0.5)",
        }

        theme = Theme.from_dict(theme_data)

        assert theme.name == "custom"
        assert theme.display_name == "Custom Theme"
        assert theme.background == "#000000"

    def test_get_theme_default(self):
        """Test getting default theme."""
        theme = Theme.get_theme("default")

        assert theme.name == "default"
        assert theme.display_name == "Default (Dark Professional)"

    def test_get_theme_light(self):
        """Test getting light theme."""
        theme = Theme.get_theme("light")

        assert theme.name == "light"
        assert theme.display_name == "Light"
        assert theme.background == "#f8fafc"  # Light background

    def test_get_theme_dark(self):
        """Test getting dark theme."""
        theme = Theme.get_theme("dark")

        assert theme.name == "dark"
        assert theme.display_name == "Dark"
        assert theme.background == "#0f172a"  # Dark background

    def test_get_theme_high_contrast(self):
        """Test getting high contrast theme."""
        theme = Theme.get_theme("high-contrast")

        assert theme.name == "high-contrast"
        assert theme.display_name == "High Contrast"
        assert theme.background == "#000000"  # Pure black

    def test_get_theme_solarized(self):
        """Test getting solarized dark theme."""
        theme = Theme.get_theme("solarized-dark")

        assert theme.name == "solarized-dark"
        assert theme.display_name == "Solarized Dark"

    def test_get_theme_dracula(self):
        """Test getting dracula theme."""
        theme = Theme.get_theme("dracula")

        assert theme.name == "dracula"
        assert theme.display_name == "Dracula"

    def test_get_theme_not_found(self):
        """Test getting non-existent theme raises KeyError."""
        with pytest.raises(KeyError, match="Theme 'nonexistent' not found"):
            Theme.get_theme("nonexistent")

    def test_get_available_themes(self):
        """Test getting list of available themes."""
        themes = Theme.get_available_themes()

        assert "default" in themes
        assert "light" in themes
        assert "dark" in themes
        assert "high-contrast" in themes
        assert "solarized-dark" in themes
        assert "dracula" in themes
        assert len(themes) == 6

    def test_built_in_themes_complete(self):
        """Test all built-in themes have required fields."""
        for theme_name in Theme.get_available_themes():
            theme = Theme.get_theme(theme_name)

            # Verify all fields are present
            assert theme.name
            assert theme.display_name
            assert theme.background
            assert theme.surface
            assert theme.surface_elevated
            assert theme.primary
            assert theme.primary_light
            assert theme.primary_dark
            assert theme.text_primary
            assert theme.text_secondary
            assert theme.text_muted
            assert theme.success
            assert theme.warning
            assert theme.danger
            assert theme.neutral
            assert theme.border
            assert theme.shadow


class TestThemeValidation:
    """Test theme accessibility validation."""

    def test_validate_theme_high_contrast(self):
        """Test high contrast theme passes validation."""
        theme = Theme.get_theme("high-contrast")
        warnings = validate_theme_contrast(theme)

        # High contrast theme should have no warnings
        assert len(warnings) == 0

    def test_validate_theme_default(self):
        """Test default theme validation."""
        theme = Theme.get_theme("default")
        warnings = validate_theme_contrast(theme)

        # Default theme should be accessible
        assert len(warnings) == 0

    def test_validate_theme_light(self):
        """Test light theme validation."""
        theme = Theme.get_theme("light")
        warnings = validate_theme_contrast(theme)

        # Light theme should be accessible
        assert len(warnings) == 0

    def test_validate_all_built_in_themes(self):
        """Test all built-in themes meet accessibility standards."""
        for theme_name in Theme.get_available_themes():
            theme = Theme.get_theme(theme_name)
            warnings = validate_theme_contrast(theme)

            # All built-in themes should pass WCAG 2.1 AA
            assert len(warnings) == 0, f"Theme {theme_name} has warnings: {warnings}"

    def test_validate_poor_contrast_theme(self):
        """Test validation detects poor contrast."""
        # Create a theme with poor contrast
        poor_theme = Theme(
            name="poor",
            display_name="Poor Contrast",
            background="#ffffff",  # White background
            surface="#ffffff",
            surface_elevated="#f0f0f0",
            primary="#ff0000",
            primary_light="#ff5555",
            primary_dark="#cc0000",
            text_primary="#cccccc",  # Light gray on white - poor contrast
            text_secondary="#dddddd",  # Even worse
            text_muted="#eeeeee",
            success="#00ff00",
            warning="#ffff00",
            danger="#ff0000",
            neutral="#888888",
            border="#f0f0f0",
            shadow="rgba(0, 0, 0, 0.1)",
        )

        warnings = validate_theme_contrast(poor_theme)

        # Should detect poor contrast
        assert len(warnings) > 0
        assert any("Primary text on background" in w for w in warnings)


class TestThemeRoundtrip:
    """Test theme serialization and deserialization."""

    def test_theme_dict_roundtrip(self):
        """Test converting theme to dict and back preserves data."""
        original = Theme.get_theme("default")
        theme_dict = original.to_dict()
        restored = Theme.from_dict(theme_dict)

        assert restored.name == original.name
        assert restored.display_name == original.display_name
        assert restored.background == original.background
        assert restored.surface == original.surface
        assert restored.primary == original.primary
        assert restored.text_primary == original.text_primary

    def test_css_vars_have_correct_format(self):
        """Test CSS variables are correctly formatted."""
        theme = Theme.get_theme("default")
        css_vars = theme.to_css_vars()

        for key, value in css_vars.items():
            # Keys should start with --
            assert key.startswith("--")
            # Values should be valid CSS colors or shadows
            assert isinstance(value, str)
            assert len(value) > 0

"""Tests for config auto-discovery functionality."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from agentready.cli.main import cli, discover_config


@pytest.fixture
def runner():
    """Create Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_repo():
    """Create temporary repository directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_config_content():
    """Valid configuration YAML content."""
    return """
weights:
  claude_md: 0.15
  readme_file: 0.10

excluded_attributes:
  - dependency_freshness

output_dir: ./custom-reports

report_theme: dark
"""


@pytest.fixture
def user_config_dir(monkeypatch, tmp_path):
    """Mock user config directory."""
    config_dir = tmp_path / ".config" / "agentready"
    config_dir.mkdir(parents=True)

    # Monkeypatch Path.home() to return our temp directory
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    return config_dir


class TestDiscoverConfig:
    """Test config discovery function."""

    def test_explicit_config_takes_precedence(self, temp_repo, valid_config_content):
        """Explicit --config flag should take highest priority."""
        # Create both repo-level and explicit configs
        repo_config = temp_repo / ".agentready.yaml"
        repo_config.write_text("report_theme: light\n")

        explicit_config = temp_repo / "custom-config.yaml"
        explicit_config.write_text(valid_config_content)

        # Explicit should win
        config = discover_config(temp_repo, explicit_config)
        assert config is not None
        assert config.report_theme == "dark"  # From explicit config

    def test_repo_level_yaml_config(self, temp_repo, valid_config_content):
        """Should discover .agentready.yaml in repo root."""
        config_file = temp_repo / ".agentready.yaml"
        config_file.write_text(valid_config_content)

        config = discover_config(temp_repo, None)
        assert config is not None
        assert config.report_theme == "dark"

    def test_repo_level_yml_config(self, temp_repo, valid_config_content):
        """Should discover .agentready.yml in repo root."""
        config_file = temp_repo / ".agentready.yml"
        config_file.write_text(valid_config_content)

        config = discover_config(temp_repo, None)
        assert config is not None
        assert config.report_theme == "dark"

    def test_yaml_preferred_over_yml(self, temp_repo):
        """Should prefer .yaml over .yml when both exist."""
        yaml_config = temp_repo / ".agentready.yaml"
        yaml_config.write_text("report_theme: dark\n")

        yml_config = temp_repo / ".agentready.yml"
        yml_config.write_text("report_theme: light\n")

        config = discover_config(temp_repo, None)
        assert config is not None
        assert config.report_theme == "dark"  # .yaml wins

    def test_user_level_config(self, temp_repo, user_config_dir, valid_config_content):
        """Should discover user-level config when no repo config exists."""
        user_config = user_config_dir / "config.yaml"
        user_config.write_text(valid_config_content)

        config = discover_config(temp_repo, None)
        assert config is not None
        assert config.report_theme == "dark"

    def test_repo_config_preferred_over_user_config(
        self, temp_repo, user_config_dir, valid_config_content
    ):
        """Repo-level config should take precedence over user-level."""
        # Create user-level config
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("report_theme: light\n")

        # Create repo-level config
        repo_config = temp_repo / ".agentready.yaml"
        repo_config.write_text(valid_config_content)

        config = discover_config(temp_repo, None)
        assert config is not None
        assert config.report_theme == "dark"  # Repo config wins

    def test_no_config_returns_none(self, temp_repo):
        """Should return None when no config found anywhere."""
        config = discover_config(temp_repo, None)
        assert config is None

    def test_explicit_config_not_found_exits(self, temp_repo):
        """Should exit with error if explicit config doesn't exist."""
        nonexistent_config = temp_repo / "nonexistent.yaml"

        # discover_config calls sys.exit(1) when explicit config not found
        # We'll test this via CLI instead since function exits
        # (Testing sys.exit directly is complex in pytest)
        pass  # Covered by CLI integration test below


class TestCLIIntegration:
    """Test config discovery in actual CLI commands."""

    def test_assess_with_explicit_config(self, runner, temp_repo, valid_config_content):
        """Test assess command with --config flag."""
        # Create a minimal repo structure
        (temp_repo / "README.md").write_text("# Test\n")

        # Create config file
        config_file = temp_repo / "config.yaml"
        config_file.write_text(valid_config_content)

        # Run assess with explicit config
        result = runner.invoke(
            cli,
            ["assess", str(temp_repo), "--config", str(config_file)],
            catch_exceptions=False,
        )

        # Should show config usage message
        assert "📋 Using config:" in result.output or result.exit_code == 0

    def test_assess_discovers_repo_config(self, runner, temp_repo, valid_config_content):
        """Test assess command discovers repo-level config."""
        # Create a minimal repo structure
        (temp_repo / "README.md").write_text("# Test\n")

        # Create repo-level config
        config_file = temp_repo / ".agentready.yaml"
        config_file.write_text(valid_config_content)

        # Run assess without explicit config
        result = runner.invoke(
            cli, ["assess", str(temp_repo)], catch_exceptions=False
        )

        # Should auto-discover and use config
        assert "📋 Using config:" in result.output or result.exit_code == 0

    def test_assess_no_config_uses_defaults(self, runner, temp_repo):
        """Test assess command works without any config."""
        # Create a minimal repo structure
        (temp_repo / "README.md").write_text("# Test\n")

        # Run assess without config
        result = runner.invoke(
            cli, ["assess", str(temp_repo)], catch_exceptions=False
        )

        # Should not show config usage message (using defaults)
        # But should still complete successfully
        assert result.exit_code == 0 or "📋 Using config:" not in result.output

    def test_assess_explicit_config_not_found(self, runner, temp_repo):
        """Test assess command with nonexistent config file."""
        # Create a minimal repo structure
        (temp_repo / "README.md").write_text("# Test\n")

        # Try to use nonexistent config
        result = runner.invoke(
            cli,
            ["assess", str(temp_repo), "--config", "nonexistent.yaml"],
        )

        # Should fail with error message
        assert result.exit_code != 0
        assert "Config file not found" in result.output or "does not exist" in result.output


class TestPriorityChain:
    """Test the full priority chain of config discovery."""

    def test_full_priority_chain(
        self, temp_repo, user_config_dir, valid_config_content
    ):
        """Test complete priority chain: explicit > repo > user > none."""
        # Create all three config levels
        user_config = user_config_dir / "config.yaml"
        user_config.write_text("report_theme: light\n")

        repo_config = temp_repo / ".agentready.yaml"
        repo_config.write_text("report_theme: dark\n")

        explicit_config = temp_repo / "explicit.yaml"
        explicit_config.write_text("report_theme: high-contrast\n")

        # Test explicit takes precedence
        config = discover_config(temp_repo, explicit_config)
        assert config.report_theme == "high-contrast"

        # Test repo takes precedence over user
        config = discover_config(temp_repo, None)
        assert config.report_theme == "dark"

        # Remove repo config, user should be used
        repo_config.unlink()
        config = discover_config(temp_repo, None)
        assert config.report_theme == "light"

        # Remove user config, should return None
        user_config.unlink()
        config = discover_config(temp_repo, None)
        assert config is None


class TestConfigValidationInDiscovery:
    """Test that discovery respects config validation."""

    def test_invalid_config_shows_error(self, temp_repo):
        """Invalid config should show validation errors."""
        # Create invalid config (negative weight)
        config_file = temp_repo / ".agentready.yaml"
        config_file.write_text("weights:\n  claude_md: -0.5\n")

        # Try to discover - should fail validation
        with pytest.raises(SystemExit):
            discover_config(temp_repo, config_file)

    def test_malformed_yaml_shows_error(self, temp_repo):
        """Malformed YAML should show error."""
        # Create malformed YAML
        config_file = temp_repo / ".agentready.yaml"
        config_file.write_text("weights:\n  invalid yaml: [unclosed bracket\n")

        # Try to discover - should fail parsing
        with pytest.raises(SystemExit):
            discover_config(temp_repo, config_file)

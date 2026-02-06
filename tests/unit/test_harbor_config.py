"""
Tests for Harbor framework configuration validation.

Following TDD red-green-refactor workflow:
- Phase 1 (RED): Write tests, verify they FAIL
- Phase 2 (GREEN): Implement HarborConfig to make tests PASS
- Phase 3 (REFACTOR): Add docstrings and improve code quality
"""

from pathlib import Path

import pytest

from agentready.services.eval_harness.harbor_config import (
    ALLOWED_AGENTS,
    ALLOWED_MODELS,
    HarborConfig,
)


class TestHarborConfigValidModels:
    """Test valid model acceptance"""

    def test_harbor_config_valid_model_haiku(self):
        """Test that haiku-4-5 model is accepted"""
        config = HarborConfig(
            model="anthropic/claude-haiku-4-5",
            agent="claude-code",
            jobs_dir=Path("/tmp/test"),
            api_key="test-key",
        )
        assert config.model == "anthropic/claude-haiku-4-5"

    def test_harbor_config_valid_model_sonnet(self):
        """Test that sonnet-4-5 model is accepted"""
        config = HarborConfig(
            model="anthropic/claude-sonnet-4-5",
            agent="claude-code",
            jobs_dir=Path("/tmp/test"),
            api_key="test-key",
        )
        assert config.model == "anthropic/claude-sonnet-4-5"


class TestHarborConfigInvalidModels:
    """Test invalid model rejection"""

    def test_harbor_config_invalid_model_rejected(self):
        """Test that invalid model raises ValueError"""
        with pytest.raises(ValueError, match="Invalid model"):
            HarborConfig(
                model="invalid/model",
                agent="claude-code",
                jobs_dir=Path("/tmp/test"),
                api_key="test-key",
            )

    def test_harbor_config_invalid_model_opus_rejected(self):
        """Test that opus (expensive, not in allowlist) is rejected"""
        with pytest.raises(ValueError, match="Invalid model"):
            HarborConfig(
                model="anthropic/claude-opus-4-1",
                agent="claude-code",
                jobs_dir=Path("/tmp/test"),
                api_key="test-key",
            )


class TestHarborConfigInvalidAgents:
    """Test invalid agent rejection"""

    def test_harbor_config_invalid_agent_rejected(self):
        """Test that invalid agent raises ValueError"""
        with pytest.raises(ValueError, match="Invalid agent"):
            HarborConfig(
                model="anthropic/claude-haiku-4-5",
                agent="invalid-agent",
                jobs_dir=Path("/tmp/test"),
                api_key="test-key",
            )

    def test_harbor_config_oracle_agent_rejected(self):
        """Test that oracle agent (reference baseline, not relevant) is rejected"""
        with pytest.raises(ValueError, match="Invalid agent"):
            HarborConfig(
                model="anthropic/claude-haiku-4-5",
                agent="oracle",
                jobs_dir=Path("/tmp/test"),
                api_key="test-key",
            )


class TestHarborConfigAPIKey:
    """Test API key validation"""

    def test_harbor_config_empty_api_key_rejected(self):
        """Test that empty API key raises ValueError"""
        with pytest.raises(ValueError, match="API key"):
            HarborConfig(
                model="anthropic/claude-haiku-4-5",
                agent="claude-code",
                jobs_dir=Path("/tmp/test"),
                api_key="",
            )

    def test_harbor_config_none_api_key_rejected(self):
        """Test that None API key raises ValueError"""
        with pytest.raises(ValueError, match="API key"):
            HarborConfig(
                model="anthropic/claude-haiku-4-5",
                agent="claude-code",
                jobs_dir=Path("/tmp/test"),
                api_key=None,
            )


class TestHarborConfigTimeout:
    """Test timeout validation"""

    def test_harbor_config_negative_timeout_rejected(self):
        """Test that negative timeout raises ValueError"""
        with pytest.raises(ValueError, match="Timeout"):
            HarborConfig(
                model="anthropic/claude-haiku-4-5",
                agent="claude-code",
                jobs_dir=Path("/tmp/test"),
                api_key="test-key",
                timeout=-1,
            )

    def test_harbor_config_zero_timeout_rejected(self):
        """Test that zero timeout raises ValueError"""
        with pytest.raises(ValueError, match="Timeout"):
            HarborConfig(
                model="anthropic/claude-haiku-4-5",
                agent="claude-code",
                jobs_dir=Path("/tmp/test"),
                api_key="test-key",
                timeout=0,
            )

    def test_harbor_config_positive_timeout_accepted(self):
        """Test that positive timeout is accepted"""
        config = HarborConfig(
            model="anthropic/claude-haiku-4-5",
            agent="claude-code",
            jobs_dir=Path("/tmp/test"),
            api_key="test-key",
            timeout=3600,
        )
        assert config.timeout == 3600


class TestHarborConfigPathResolution:
    """Test jobs_dir path resolution"""

    def test_harbor_config_path_resolution(self):
        """Test that jobs_dir is resolved to absolute path"""
        config = HarborConfig(
            model="anthropic/claude-haiku-4-5",
            agent="claude-code",
            jobs_dir=Path("relative/path"),
            api_key="test-key",
        )
        assert config.jobs_dir.is_absolute()

    def test_harbor_config_absolute_path_unchanged(self):
        """Test that absolute path remains unchanged"""
        abs_path = Path("/tmp/test").resolve()
        config = HarborConfig(
            model="anthropic/claude-haiku-4-5",
            agent="claude-code",
            jobs_dir=abs_path,
            api_key="test-key",
        )
        assert config.jobs_dir == abs_path


class TestHarborConfigDefaults:
    """Test default values"""

    def test_harbor_config_default_timeout(self):
        """Test that default timeout is 3600 seconds"""
        config = HarborConfig(
            model="anthropic/claude-haiku-4-5",
            agent="claude-code",
            jobs_dir=Path("/tmp/test"),
            api_key="test-key",
        )
        assert config.timeout == 3600

    def test_harbor_config_default_n_concurrent(self):
        """Test that default n_concurrent is 1"""
        config = HarborConfig(
            model="anthropic/claude-haiku-4-5",
            agent="claude-code",
            jobs_dir=Path("/tmp/test"),
            api_key="test-key",
        )
        assert config.n_concurrent == 1


class TestAllowlists:
    """Test allowlist constants"""

    def test_allowed_models_contains_haiku(self):
        """Test that ALLOWED_MODELS contains haiku-4-5"""
        assert "anthropic/claude-haiku-4-5" in ALLOWED_MODELS

    def test_allowed_models_contains_sonnet(self):
        """Test that ALLOWED_MODELS contains sonnet-4-5"""
        assert "anthropic/claude-sonnet-4-5" in ALLOWED_MODELS

    def test_allowed_agents_contains_claude_code(self):
        """Test that ALLOWED_AGENTS contains claude-code"""
        assert "claude-code" in ALLOWED_AGENTS

    def test_allowed_models_is_set(self):
        """Test that ALLOWED_MODELS is a set (not list)"""
        assert isinstance(ALLOWED_MODELS, set)

    def test_allowed_agents_is_set(self):
        """Test that ALLOWED_AGENTS is a set (not list)"""
        assert isinstance(ALLOWED_AGENTS, set)


class TestHarborConfigCursorModels:
    """Test cursor/* model acceptance"""

    def test_harbor_config_cursor_models_accepted(self):
        """Test that cursor/* models are accepted"""
        config = HarborConfig(
            model="cursor/sonnet-4.5",
            agent="cursor-cli",
            jobs_dir=Path("/tmp/test"),
            api_key="test-key",
        )
        assert config.model == "cursor/sonnet-4.5"

        config_gemini = HarborConfig(
            model="cursor/gemini-3-pro",
            agent="cursor-cli",
            jobs_dir=Path("/tmp/test"),
            api_key="test-key",
        )
        assert config_gemini.model == "cursor/gemini-3-pro"


class TestHarborConfigCursorAgent:
    """Test cursor-cli agent acceptance"""

    def test_harbor_config_cursor_agent_accepted(self):
        """Test that cursor-cli agent is accepted"""
        config = HarborConfig(
            model="anthropic/claude-haiku-4-5",
            agent="cursor-cli",
            jobs_dir=Path("/tmp/test"),
            api_key="test-key",
        )
        assert config.agent == "cursor-cli"

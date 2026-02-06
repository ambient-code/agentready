"""
Harbor framework configuration for Terminal-Bench integration.

This module provides configuration and validation for Harbor framework subprocess execution.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Allowed models (excludes opus due to cost)
# Anthropic models: https://platform.claude.com/docs/en/about-claude/models/overview
# Cursor models: https://cursor.com/docs/models
ALLOWED_MODELS = {
    "anthropic/claude-haiku-4-5",
    "anthropic/claude-sonnet-4-5",
    "cursor/composer-1",
    "cursor/gpt-5.2-codex",
    "cursor/gpt-5.2-codex-fast",
    "cursor/gemini-3-pro",
    "cursor/opus-4.5",
    "cursor/sonnet-4.5",
    "cursor/sonnet-4.5-thinking",
    "cursor/gpt-5.1-high",
    "cursor/gemini-3-flash",
}

# Allowed agents (excludes oracle as it's not relevant for real-world assessment)
# Harbor supported agents: https://github.com/laude-institute/harbor/blob/main/src/harbor/agents/factory.py
ALLOWED_AGENTS = {
    "claude-code",
    "cursor-cli",
}


@dataclass
class HarborConfig:
    """
    Configuration for Harbor framework subprocess execution.

    Attributes:
        model: LLM model identifier (must be in ALLOWED_MODELS)
        agent: Agent identifier (must be in ALLOWED_AGENTS)
        jobs_dir: Output directory for results (resolved to absolute path)
        api_key: Anthropic API key (must not be empty)
        timeout: Subprocess timeout in seconds (default: 3600, must be positive)
        n_concurrent: Harbor's internal concurrency (default: 1, must be >= 1)
        smoketest: Run fast validation with 1-2 tasks (default: False)
        task_path: Optional path to specific task (for smoketest mode)
    """

    model: str
    agent: str
    jobs_dir: Path
    api_key: str
    timeout: int = 3600
    n_concurrent: int = 1
    smoketest: bool = False
    task_path: Optional[Path] = None

    def __post_init__(self):
        """Validate configuration parameters"""
        # Validate model allowlist
        if self.model not in ALLOWED_MODELS:
            raise ValueError(
                f"Invalid model: {self.model}. "
                f"Allowed models: {sorted(ALLOWED_MODELS)}"
            )

        # Validate agent allowlist
        if self.agent not in ALLOWED_AGENTS:
            raise ValueError(
                f"Invalid agent: {self.agent}. "
                f"Allowed agents: {sorted(ALLOWED_AGENTS)}"
            )

        # Validate API key is not empty
        if not self.api_key:
            raise ValueError("API key cannot be empty")

        # Validate timeout is positive
        if self.timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {self.timeout}")

        # Resolve jobs_dir to absolute path
        self.jobs_dir = Path(self.jobs_dir).resolve()

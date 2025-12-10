"""Service for safely enabling/disabling the doubleagent.md file."""

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


class AgentFileToggler:
    """Safely enable/disable agent files via atomic rename operations."""

    def __init__(self, agent_file: Path):
        """Initialize toggler with agent file path.

        Args:
            agent_file: Path to the agent file (e.g., .claude/agents/doubleagent.md)
        """
        self.agent_file = agent_file
        self.disabled_file = agent_file.with_suffix(agent_file.suffix + ".disabled")

    def disable(self) -> None:
        """Rename agent file to .disabled extension."""
        if self.agent_file.exists():
            if self.disabled_file.exists():
                # Already disabled, nothing to do
                return
            shutil.move(str(self.agent_file), str(self.disabled_file))

    def enable(self) -> None:
        """Restore agent file from .disabled extension."""
        if self.disabled_file.exists():
            if self.agent_file.exists():
                # Already enabled, nothing to do
                return
            shutil.move(str(self.disabled_file), str(self.agent_file))

    def is_enabled(self) -> bool:
        """Check if agent file is currently enabled.

        Returns:
            True if agent file exists and is not disabled
        """
        return self.agent_file.exists() and not self.disabled_file.exists()

    def is_disabled(self) -> bool:
        """Check if agent file is currently disabled.

        Returns:
            True if disabled file exists
        """
        return self.disabled_file.exists()

    @contextmanager
    def temporarily_disabled(self) -> Generator[None, None, None]:
        """Context manager for safe disable/enable.

        Ensures agent file is restored even if exception occurs.

        Example:
            with toggler.temporarily_disabled():
                # Agent file is disabled here
                run_benchmark()
            # Agent file is automatically restored here
        """
        was_enabled = self.is_enabled()
        try:
            self.disable()
            yield
        finally:
            if was_enabled:
                self.enable()

    @contextmanager
    def temporarily_enabled(self) -> Generator[None, None, None]:
        """Context manager for safe enable/disable.

        Ensures agent file state is restored even if exception occurs.

        Example:
            with toggler.temporarily_enabled():
                # Agent file is enabled here
                run_benchmark()
            # Agent file state is automatically restored here
        """
        was_disabled = self.is_disabled()
        try:
            self.enable()
            yield
        finally:
            if was_disabled:
                self.disable()

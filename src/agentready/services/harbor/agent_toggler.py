"""Service for safely enabling/disabling agent files and manipulating repository state."""

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Dict, Generator, Tuple


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


class AssessorStateToggler:
    """Manipulate repository state to force assessor pass/fail for A/B testing.

    This class safely modifies repository files to simulate scenarios where
    specific assessors would pass or fail, enabling empirical validation of
    assessor impacts on agent performance.

    Example:
        toggler = AssessorStateToggler()

        # Force CLAUDE.md assessor to fail
        toggler.force_fail("claude_md_file")
        # Run benchmark
        toggler.restore("claude_md_file")
    """

    # Mapping of assessor IDs to (fail_action, restore_action) tuples
    # Each action is a callable that takes the repository root Path
    MANIPULATIONS: Dict[str, Tuple[Callable[[Path], None], Callable[[Path], None]]] = {}

    @classmethod
    def register_manipulation(
        cls,
        assessor_id: str,
        fail_action: Callable[[Path], None],
        restore_action: Callable[[Path], None],
    ) -> None:
        """Register a manipulation strategy for an assessor.

        Args:
            assessor_id: Unique assessor identifier (e.g., "claude_md_file")
            fail_action: Function to force assessor to fail state
            restore_action: Function to restore assessor to pass state
        """
        cls.MANIPULATIONS[assessor_id] = (fail_action, restore_action)

    def __init__(self, repo_root: Path = None):
        """Initialize toggler with repository root.

        Args:
            repo_root: Root of the repository (default: current directory)
        """
        self.repo_root = repo_root or Path.cwd()
        self._backup_suffix = ".assessor_backup"
        self._initialize_default_manipulations()

    def _initialize_default_manipulations(self) -> None:
        """Register default manipulation strategies for Phase 1 assessors."""

        # CLAUDE.md Assessor - Tier 1, 10% weight
        def fail_claude_md(repo_root: Path) -> None:
            claude_md = repo_root / ".claude" / "CLAUDE.md"
            backup = repo_root / ".claude" / f"CLAUDE.md{self._backup_suffix}"
            if claude_md.exists() and not backup.exists():
                shutil.move(str(claude_md), str(backup))

        def restore_claude_md(repo_root: Path) -> None:
            claude_md = repo_root / ".claude" / "CLAUDE.md"
            backup = repo_root / ".claude" / f"CLAUDE.md{self._backup_suffix}"
            if backup.exists() and not claude_md.exists():
                shutil.move(str(backup), str(claude_md))

        self.register_manipulation("claude_md_file", fail_claude_md, restore_claude_md)

        # README Assessor - Tier 1, 10% weight
        def fail_readme(repo_root: Path) -> None:
            readme = repo_root / "README.md"
            backup = repo_root / f"README.md{self._backup_suffix}"
            if readme.exists() and not backup.exists():
                shutil.move(str(readme), str(backup))

        def restore_readme(repo_root: Path) -> None:
            readme = repo_root / "README.md"
            backup = repo_root / f"README.md{self._backup_suffix}"
            if backup.exists() and not readme.exists():
                shutil.move(str(backup), str(readme))

        self.register_manipulation("readme_structure", fail_readme, restore_readme)

        # Test Coverage Assessor - Tier 2, 3% weight
        def fail_tests(repo_root: Path) -> None:
            tests_dir = repo_root / "tests"
            backup_dir = repo_root / f"tests{self._backup_suffix}"
            if tests_dir.exists() and not backup_dir.exists():
                shutil.move(str(tests_dir), str(backup_dir))

        def restore_tests(repo_root: Path) -> None:
            tests_dir = repo_root / "tests"
            backup_dir = repo_root / f"tests{self._backup_suffix}"
            if backup_dir.exists() and not tests_dir.exists():
                shutil.move(str(backup_dir), str(tests_dir))

        self.register_manipulation("test_coverage", fail_tests, restore_tests)

    def force_fail(self, assessor_id: str) -> None:
        """Force assessor to fail by manipulating repository state.

        Args:
            assessor_id: Assessor identifier (e.g., "claude_md_file")

        Raises:
            ValueError: If assessor_id is not recognized
        """
        if assessor_id not in self.MANIPULATIONS:
            raise ValueError(
                f"Unknown assessor: {assessor_id}. "
                f"Available: {', '.join(self.MANIPULATIONS.keys())}"
            )

        fail_action, _ = self.MANIPULATIONS[assessor_id]
        fail_action(self.repo_root)

    def restore(self, assessor_id: str) -> None:
        """Restore repository to state where assessor passes.

        Args:
            assessor_id: Assessor identifier (e.g., "claude_md_file")

        Raises:
            ValueError: If assessor_id is not recognized
        """
        if assessor_id not in self.MANIPULATIONS:
            raise ValueError(
                f"Unknown assessor: {assessor_id}. "
                f"Available: {', '.join(self.MANIPULATIONS.keys())}"
            )

        _, restore_action = self.MANIPULATIONS[assessor_id]
        restore_action(self.repo_root)

    def list_supported_assessors(self) -> list[str]:
        """Get list of assessor IDs with registered manipulations.

        Returns:
            List of assessor IDs that can be toggled
        """
        return list(self.MANIPULATIONS.keys())

    @contextmanager
    def temporarily_failed(self, assessor_id: str) -> Generator[None, None, None]:
        """Context manager for safe fail/restore of assessor state.

        Ensures repository is restored even if exception occurs during testing.

        Args:
            assessor_id: Assessor identifier

        Example:
            toggler = AssessorStateToggler()
            with toggler.temporarily_failed("claude_md_file"):
                # CLAUDE.md is now missing (assessor fails)
                run_benchmark()
            # CLAUDE.md is automatically restored here

        Yields:
            None
        """
        try:
            self.force_fail(assessor_id)
            yield
        finally:
            self.restore(assessor_id)

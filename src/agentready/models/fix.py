"""Fix models for automated remediation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Fix(ABC):
    """Base class for automated fixes.

    Attributes:
        attribute_id: ID of the attribute being fixed
        description: Human-readable description of the fix
        points_gained: Estimated points this fix will add to score
    """

    attribute_id: str
    description: str
    points_gained: float

    @abstractmethod
    def apply(self, dry_run: bool = False) -> bool:
        """Apply the fix to the repository.

        Args:
            dry_run: If True, don't make changes, just validate

        Returns:
            True if fix was applied successfully, False otherwise
        """
        pass

    @abstractmethod
    def preview(self) -> str:
        """Generate a preview of what this fix will do.

        Returns:
            Human-readable description of changes
        """
        pass


@dataclass
class FileCreationFix(Fix):
    """Fix that creates a new file.

    Attributes:
        file_path: Path to create (relative to repository root)
        content: File content to write
        repository_path: Repository root path
    """

    file_path: Path
    content: str
    repository_path: Path

    def apply(self, dry_run: bool = False) -> bool:
        """Create the file."""
        target_path = self.repository_path / self.file_path

        # Check if file already exists
        if target_path.exists():
            return False

        if not dry_run:
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            # Write content
            target_path.write_text(self.content, encoding="utf-8")

        return True

    def preview(self) -> str:
        """Preview file creation."""
        size_kb = len(self.content) / 1024
        return f"CREATE {self.file_path} ({size_kb:.1f} KB)"


@dataclass
class FileModificationFix(Fix):
    """Fix that modifies an existing file.

    Attributes:
        file_path: Path to modify (relative to repository root)
        additions: Lines to add to the file
        repository_path: Repository root path
        append: If True, append additions; if False, use smart merge
    """

    file_path: Path
    additions: List[str]
    repository_path: Path
    append: bool = True

    def apply(self, dry_run: bool = False) -> bool:
        """Modify the file."""
        target_path = self.repository_path / self.file_path

        # Check if file exists
        if not target_path.exists():
            return False

        if not dry_run:
            if self.append:
                # Append additions to end of file
                with target_path.open("a", encoding="utf-8") as f:
                    for line in self.additions:
                        f.write(line + "\n")
            else:
                # Smart merge: avoid duplicates
                existing = target_path.read_text(encoding="utf-8").splitlines()
                existing_set = set(existing)

                with target_path.open("a", encoding="utf-8") as f:
                    for line in self.additions:
                        if line not in existing_set:
                            f.write(line + "\n")

        return True

    def preview(self) -> str:
        """Preview file modification."""
        return f"MODIFY {self.file_path} (+{len(self.additions)} lines)"


@dataclass
class CommandFix(Fix):
    """Fix that executes a command.

    Attributes:
        command: Command to execute
        working_dir: Directory to run command in
        repository_path: Repository root path
        capture_output: If True, suppress stdout/stderr; if False, stream to terminal
    """

    command: str
    working_dir: Optional[Path]
    repository_path: Path
    capture_output: bool = True

    def apply(self, dry_run: bool = False) -> bool:
        """Execute the command.

        Security: Uses shlex.split() to safely parse commands without shell=True,
        preventing command injection attacks.
        """
        if dry_run:
            return True

        import shlex
        import subprocess

        cwd = self.working_dir or self.repository_path

        try:
            # Security: Parse command safely without shell interpretation
            # This prevents injection via shell metacharacters (;, |, &&, etc.)
            cmd_list = shlex.split(self.command)

            # Validate that we have a command to run
            if not cmd_list:
                return False

            subprocess.run(
                cmd_list,
                cwd=cwd,
                check=True,
                capture_output=self.capture_output,
                text=True,
                # Security: Never use shell=True - explicitly removed
            )
            return True
        except (subprocess.CalledProcessError, ValueError):
            # ValueError can be raised by shlex.split() on malformed input
            return False

    def preview(self) -> str:
        """Preview command execution."""
        return f"RUN {self.command}"


@dataclass
class MultiStepFix(Fix):
    """Fix composed of multiple steps.

    Attributes:
        steps: Ordered list of fixes to apply
    """

    steps: List[Fix]

    def apply(self, dry_run: bool = False) -> bool:
        """Apply all steps in order."""
        for step in self.steps:
            if not step.apply(dry_run):
                return False
        return True

    def preview(self) -> str:
        """Preview all steps."""
        lines = [f"MULTI-STEP FIX ({len(self.steps)} steps):"]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  {i}. {step.preview()}")
        return "\n".join(lines)

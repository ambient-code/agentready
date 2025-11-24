"""Base reporter interface for generating assessment reports."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models.assessment import Assessment


class BaseReporter(ABC):
    """Abstract base class for all report generators.

    Reporters transform Assessment data into different output formats
    (HTML, Markdown, PDF, etc.) for human consumption.

    Provides common file handling methods to eliminate duplication across reporters.
    """

    @abstractmethod
    def generate(self, assessment: Assessment, output_path: Path) -> Path:
        """Generate report from assessment data.

        Args:
            assessment: Complete assessment with findings
            output_path: Path where report should be saved

        Returns:
            Path to generated report file

        Raises:
            IOError: If report cannot be written
        """
        pass

    def _ensure_output_dir(self, output_path: Path) -> None:
        """Ensure output directory exists.

        Creates parent directories if they don't exist.

        Args:
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_file(
        self, content: str | bytes, output_path: Path, encoding: str = "utf-8"
    ) -> Path:
        """Write content to file and return path.

        Automatically creates parent directories if needed.

        Args:
            content: Content to write (string or bytes)
            output_path: Path to write to
            encoding: Text encoding (default: utf-8, ignored for bytes)

        Returns:
            Path to written file

        Raises:
            IOError: If file cannot be written
        """
        self._ensure_output_dir(output_path)

        if isinstance(content, bytes):
            with open(output_path, "wb") as f:
                f.write(content)
        else:
            with open(output_path, "w", encoding=encoding) as f:
                f.write(content)

        return output_path
